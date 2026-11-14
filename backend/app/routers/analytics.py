"""
Analytics router.

Provides aggregated JSON data formatted specifically for Chart.js and dashboard
metric cards (grade distribution, pass/fail per level, probation cases per level,
top failed courses, probation trends, and GPA distribution).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.probation import ProbationCase, ProbationStatus
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User
from app.services.gpa import compute_gpa

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _get_target_semester_id(db: Session, semester_id: int | None) -> int:
    """Helper to default to the current semester if none is supplied."""
    if semester_id is not None:
        return semester_id
    current_sem = db.query(Semester).filter(Semester.is_current == True).first()  # noqa: E712
    if current_sem:
        return current_sem.id
    latest_sem = db.query(Semester).order_by(Semester.id.desc()).first()
    return latest_sem.id if latest_sem else 1


@router.get("/summary")
def get_dashboard_summary(
    semester_id: int | None = Query(None, description="Semester ID (defaults to current)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    High-level metrics for dashboard stat cards:
    Total students, courses, active probation cases, average GPA, and pass rate.
    """
    target_sem_id = _get_target_semester_id(db, semester_id)

    total_students = db.query(Student).count()
    total_courses = db.query(Course).count()

    # Probation counts
    active_probations = (
        db.query(ProbationCase)
        .filter(
            ProbationCase.semester_id == target_sem_id,
            ProbationCase.status == ProbationStatus.active,
        )
        .count()
    )
    reviewing_probations = (
        db.query(ProbationCase)
        .filter(
            ProbationCase.semester_id == target_sem_id,
            ProbationCase.status == ProbationStatus.reviewing,
        )
        .count()
    )
    cleared_probations = (
        db.query(ProbationCase)
        .filter(
            ProbationCase.semester_id == target_sem_id,
            ProbationCase.status == ProbationStatus.cleared,
        )
        .count()
    )

    # Graded enrollments for pass rate and average score
    graded_enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.semester_id == target_sem_id,
            Enrollment.score.isnot(None),
        )
        .all()
    )

    total_graded = len(graded_enrollments)
    passed_count = sum(1 for e in graded_enrollments if e.grade != "F")
    pass_rate = round((passed_count / total_graded * 100), 1) if total_graded > 0 else 0.0

    # Calculate semester average GPA
    # Group enrollments by student
    student_enrollments: dict[int, list[Enrollment]] = {}
    for e in graded_enrollments:
        student_enrollments.setdefault(e.student_id, []).append(e)

    gpas = [
        compute_gpa(enrs)
        for enrs in student_enrollments.values()
    ]
    valid_gpas = [g for g in gpas if g is not None]
    avg_gpa = round(sum(valid_gpas) / len(valid_gpas), 2) if valid_gpas else 0.0

    return {
        "semester_id": target_sem_id,
        "total_students": total_students,
        "total_courses": total_courses,
        "active_probations": active_probations,
        "reviewing_probations": reviewing_probations,
        "cleared_probations": cleared_probations,
        "total_graded_enrollments": total_graded,
        "pass_rate_percentage": pass_rate,
        "average_gpa": avg_gpa,
    }


@router.get("/course-distribution/{course_id}")
def get_course_grade_distribution(
    course_id: int,
    semester_id: int | None = Query(None, description="Semester ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grade distribution (A, B, C, D, E, F) and average metrics for a single course.
    Used for Chart.js bar charts on the Lecturer and Course Detail views.
    """
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role == "lecturer" and course.lecturer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this course's analytics")

    target_sem_id = _get_target_semester_id(db, semester_id)

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.semester_id == target_sem_id,
            Enrollment.score.isnot(None),
        )
        .all()
    )

    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    scores: list[float] = []

    for e in enrollments:
        if e.grade in distribution:
            distribution[e.grade] += 1
        if e.score is not None:
            scores.append(e.score)

    total_graded = len(scores)
    avg_score = round(sum(scores) / total_graded, 1) if total_graded > 0 else 0.0
    passed = sum(distribution[g] for g in ["A", "B", "C", "D", "E"])
    pass_rate = round((passed / total_graded * 100), 1) if total_graded > 0 else 0.0

    return {
        "course_id": course.id,
        "course_code": course.code,
        "course_title": course.title,
        "semester_id": target_sem_id,
        "total_enrolled": len(enrollments),
        "total_graded": total_graded,
        "average_score": avg_score,
        "pass_rate_percentage": pass_rate,
        "distribution": distribution,
    }


@router.get("/pass-fail-by-level")
def get_pass_fail_by_level(
    semester_id: int | None = Query(None, description="Semester ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pass and fail rates grouped by student academic level (100L, 200L, 300L, 400L).
    """
    target_sem_id = _get_target_semester_id(db, semester_id)

    results = (
        db.query(Student.level, Enrollment.grade, func.count(Enrollment.id))
        .join(Enrollment, Student.id == Enrollment.student_id)
        .filter(
            Enrollment.semester_id == target_sem_id,
            Enrollment.score.isnot(None),
        )
        .group_by(Student.level, Enrollment.grade)
        .all()
    )

    level_data: dict[int, dict] = {}
    for lvl in [100, 200, 300, 400]:
        level_data[lvl] = {"level": lvl, "passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0}

    for lvl, grade, count in results:
        if lvl not in level_data:
            level_data[lvl] = {"level": lvl, "passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0}
        level_data[lvl]["total"] += count
        if grade == "F":
            level_data[lvl]["failed"] += count
        else:
            level_data[lvl]["passed"] += count

    output = []
    for lvl in sorted(level_data.keys()):
        d = level_data[lvl]
        if d["total"] > 0:
            d["pass_rate"] = round((d["passed"] / d["total"]) * 100, 1)
        output.append(d)

    return output


@router.get("/probation-by-level")
def get_probation_by_level(
    semester_id: int | None = Query(None, description="Semester ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Active probation case count grouped by student level.
    """
    target_sem_id = _get_target_semester_id(db, semester_id)

    results = (
        db.query(Student.level, func.count(ProbationCase.id))
        .join(ProbationCase, Student.id == ProbationCase.student_id)
        .filter(
            ProbationCase.semester_id == target_sem_id,
            ProbationCase.status == ProbationStatus.active,
        )
        .group_by(Student.level)
        .all()
    )

    counts = {lvl: 0 for lvl in [100, 200, 300, 400]}
    for lvl, count in results:
        counts[lvl] = count

    return [{"level": lvl, "count": counts[lvl]} for lvl in sorted(counts.keys())]


@router.get("/top-failed-courses")
def get_top_failed_courses(
    semester_id: int | None = Query(None, description="Semester ID"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns courses with the highest number of F grades in the given semester.
    """
    target_sem_id = _get_target_semester_id(db, semester_id)

    # Subquery: fails per course
    fails_subq = (
        db.query(
            Enrollment.course_id,
            func.count(Enrollment.id).label("fail_count"),
        )
        .filter(
            Enrollment.semester_id == target_sem_id,
            Enrollment.grade == "F",
        )
        .group_by(Enrollment.course_id)
        .subquery()
    )

    # Total enrollments per course
    totals_subq = (
        db.query(
            Enrollment.course_id,
            func.count(Enrollment.id).label("total_count"),
        )
        .filter(
            Enrollment.semester_id == target_sem_id,
            Enrollment.score.isnot(None),
        )
        .group_by(Enrollment.course_id)
        .subquery()
    )

    rows = (
        db.query(
            Course.id,
            Course.code,
            Course.title,
            Course.level,
            func.coalesce(fails_subq.c.fail_count, 0).label("fails"),
            func.coalesce(totals_subq.c.total_count, 0).label("totals"),
        )
        .join(fails_subq, Course.id == fails_subq.c.course_id)
        .outerjoin(totals_subq, Course.id == totals_subq.c.course_id)
        .order_by(fails_subq.c.fail_count.desc())
        .limit(limit)
        .all()
    )

    output = []
    for cid, code, title, level, fails, totals in rows:
        fail_rate = round((fails / totals * 100), 1) if totals > 0 else 0.0
        output.append({
            "course_id": cid,
            "code": code,
            "title": title,
            "level": level,
            "fail_count": fails,
            "total_enrollments": totals,
            "fail_rate": fail_rate,
        })

    return output


@router.get("/probation-trends")
def get_probation_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trend of probation cases (active, reviewing, cleared) across all semesters.
    """
    semesters = db.query(Semester).order_by(Semester.id).all()
    trends = []

    for sem in semesters:
        active = (
            db.query(ProbationCase)
            .filter(ProbationCase.semester_id == sem.id, ProbationCase.status == ProbationStatus.active)
            .count()
        )
        reviewing = (
            db.query(ProbationCase)
            .filter(ProbationCase.semester_id == sem.id, ProbationCase.status == ProbationStatus.reviewing)
            .count()
        )
        cleared = (
            db.query(ProbationCase)
            .filter(ProbationCase.semester_id == sem.id, ProbationCase.status == ProbationStatus.cleared)
            .count()
        )

        trends.append({
            "semester_id": sem.id,
            "session": sem.session,
            "name": sem.name,
            "display_name": f"{sem.session} {sem.name}",
            "active_count": active,
            "reviewing_count": reviewing,
            "cleared_count": cleared,
            "total_flagged": active + reviewing + cleared,
        })

    return trends


@router.get("/gpa-distribution")
def get_gpa_distribution(
    semester_id: int | None = Query(None, description="Semester ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Distribution of student GPAs bucketed by degree classification:
    - Probation (< 1.50)
    - Pass / Third Class (1.50 - 2.39)
    - Second Class Lower (2.40 - 3.49)
    - Second Class Upper (3.50 - 4.49)
    - First Class (4.50 - 5.00)
    """
    target_sem_id = _get_target_semester_id(db, semester_id)

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.semester_id == target_sem_id,
            Enrollment.score.isnot(None),
        )
        .all()
    )

    by_student: dict[int, list[Enrollment]] = {}
    for e in enrollments:
        by_student.setdefault(e.student_id, []).append(e)

    buckets = {
        "probation": 0,    # < 1.50
        "pass": 0,         # 1.50 - 2.39
        "second_lower": 0, # 2.40 - 3.49
        "second_upper": 0, # 3.50 - 4.49
        "first_class": 0,  # 4.50 - 5.00
    }

    for enrs in by_student.values():
        gpa = compute_gpa(enrs)
        if gpa is None:
            continue
        if gpa < 1.50:
            buckets["probation"] += 1
        elif gpa < 2.40:
            buckets["pass"] += 1
        elif gpa < 3.50:
            buckets["second_lower"] += 1
        elif gpa < 4.50:
            buckets["second_upper"] += 1
        else:
            buckets["first_class"] += 1

    return {
        "semester_id": target_sem_id,
        "total_students_evaluated": len(by_student),
        "buckets": buckets,
    }


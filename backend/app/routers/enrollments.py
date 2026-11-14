"""
Enrollments router — enrol students in courses and submit grades.

Access rules:
- Admin: full CRUD, can submit grades for any course.
- Lecturer: read-only except for grade submission, which is restricted to
  courses assigned to them.

Grade submission automatically computes grade and grade_point from the score
using the GPA service.  In Phase 5 the probation engine will also be triggered
here after every submission.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut, GradeEntry
from app.services.gpa import score_to_grade
from app.services.probation import sync_student_probation_case

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_enrollment_or_404(db: Session, enrollment_id: int) -> Enrollment:
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(404, detail="Enrollment not found")
    return e


def _assert_lecturer_owns_course(course: Course, current_user: User) -> None:
    """Raise 403 if a lecturer tries to touch a course that isn't theirs."""
    if current_user.role == "lecturer" and course.lecturer_id != current_user.id:
        raise HTTPException(403, detail="You are not assigned to this course")


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[EnrollmentOut])
def list_enrollments(
    student_id: int | None = None,
    course_id: int | None = None,
    semester_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Flexible query with optional filters.
    Lecturers are limited to enrollments in their own courses.
    """
    query = db.query(Enrollment)

    if student_id:
        query = query.filter(Enrollment.student_id == student_id)
    if course_id:
        query = query.filter(Enrollment.course_id == course_id)
    if semester_id:
        query = query.filter(Enrollment.semester_id == semester_id)

    if current_user.role == "lecturer":
        # Only return rows for courses this lecturer teaches
        lecturer_course_ids = (
            db.query(Course.id)
            .filter(Course.lecturer_id == current_user.id)
            .scalar_subquery()
        )
        query = query.filter(Enrollment.course_id.in_(lecturer_course_ids))

    return query.all()


@router.post(
    "/",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_enrollment(body: EnrollmentCreate, db: Session = Depends(get_db)):
    """
    Enrol a student in a course for a semester. Admin only.
    Duplicate enrollments (same student + course + semester) are rejected.
    """
    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == body.student_id,
            Enrollment.course_id == body.course_id,
            Enrollment.semester_id == body.semester_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, detail="Student already enrolled in this course for that semester")

    e = Enrollment(**body.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@router.get("/{enrollment_id}", response_model=EnrollmentOut)
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    e = _get_enrollment_or_404(db, enrollment_id)
    if current_user.role == "lecturer":
        course = db.get(Course, e.course_id)
        _assert_lecturer_owns_course(course, current_user)
    return e


@router.patch("/{enrollment_id}/grade", response_model=EnrollmentOut)
def submit_grade(
    enrollment_id: int,
    body: GradeEntry,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit or update a student's score for an enrollment.
    Grade letter and grade_point are computed automatically.
    Lecturers can only grade their own courses; admins can grade any.

    Automatically runs the probation engine after grade submission.
    """
    e = _get_enrollment_or_404(db, enrollment_id)
    course = db.get(Course, e.course_id)

    if current_user.role == "lecturer":
        _assert_lecturer_owns_course(course, current_user)

    grade_letter, grade_point = score_to_grade(body.score)
    e.score = body.score
    e.grade = grade_letter
    e.grade_point = grade_point

    db.commit()
    db.refresh(e)

    # ── Automated Probation Engine Trigger ──────────────────────────────
    sync_student_probation_case(
        student_id=e.student_id,
        semester_id=e.semester_id,
        db=db,
        background_tasks=background_tasks,
    )

    return e


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_enrollment(enrollment_id: int, db: Session = Depends(get_db)):
    e = _get_enrollment_or_404(db, enrollment_id)
    db.delete(e)
    db.commit()


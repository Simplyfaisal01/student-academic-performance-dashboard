"""
Probation Cases router.

Provides endpoints to list, inspect, and update probation cases, as well as
triggering batch evaluation across a semester.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.database import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.probation import ProbationCase, ProbationStatus
from app.models.student import Student
from app.models.user import User
from app.schemas.probation import ProbationCaseOut, ProbationCaseUpdate
from app.services.probation import evaluate_semester_probations

router = APIRouter(prefix="/probation", tags=["Probation"])


@router.get("/", response_model=list[ProbationCaseOut])
def list_probation_cases(
    semester_id: int | None = Query(None, description="Filter by semester ID"),
    status: ProbationStatus | None = Query(None, description="Filter by case status"),
    level: int | None = Query(None, description="Filter by student academic level"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List probation cases with optional filtering.
    Admins see all records. Lecturers see advisees and students in their courses.
    """
    query = db.query(ProbationCase).join(Student, ProbationCase.student_id == Student.id)

    if semester_id:
        query = query.filter(ProbationCase.semester_id == semester_id)
    if status:
        query = query.filter(ProbationCase.status == status)
    if level:
        query = query.filter(Student.level == level)

    if current_user.role == "lecturer":
        # Students either advised by this lecturer OR taking their courses
        advisee_ids = db.query(Student.id).filter(Student.advisor_id == current_user.id).all()
        advisee_set = {r[0] for r in advisee_ids}

        course_student_ids = (
            db.query(Enrollment.student_id)
            .join(Course, Course.id == Enrollment.course_id)
            .filter(Course.lecturer_id == current_user.id)
            .all()
        )
        course_set = {r[0] for r in course_student_ids}

        allowed_student_ids = advisee_set | course_set
        query = query.filter(ProbationCase.student_id.in_(allowed_student_ids))

    return query.order_by(ProbationCase.flagged_on.desc()).all()


@router.get("/{case_id}", response_model=ProbationCaseOut)
def get_probation_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch details of a single probation case."""
    case = db.get(ProbationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Probation case not found")
    return case


@router.patch("/{case_id}", response_model=ProbationCaseOut)
def update_probation_case(
    case_id: int,
    body: ProbationCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update notes or status on a probation case (e.g. from active to reviewing or cleared).
    Admins can update any case; advisors can update cases for their advisees.
    """
    case = db.get(ProbationCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Probation case not found")

    student = db.get(Student, case.student_id)
    if current_user.role != "admin" and (not student or student.advisor_id != current_user.id):
        raise HTTPException(status_code=403, detail="Only admins or the assigned advisor may update this case")

    if body.status is not None:
        case.status = body.status
    if body.notes is not None:
        case.notes = body.notes

    db.commit()
    db.refresh(case)
    return case


@router.post(
    "/evaluate-semester/{semester_id}",
    dependencies=[Depends(require_admin)],
)
def evaluate_semester(
    semester_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Batch evaluation endpoint: re-runs probation engine for all students in a semester.
    Admin only.
    """
    result = evaluate_semester_probations(
        semester_id=semester_id,
        db=db,
        background_tasks=background_tasks,
    )
    return result


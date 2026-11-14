"""
Students router.
- Admin: full CRUD on all students.
- Lecturer: read-only; only students enrolled in one of their courses.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.database import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


def _lecturer_student_ids(db: Session, lecturer_id: int) -> set[int]:
    """
    Return the set of student IDs enrolled in any course taught by this lecturer.
    Used to restrict what a lecturer can see.
    """
    from app.models.enrollment import Enrollment
    from app.models.course import Course

    rows = (
        db.query(Enrollment.student_id)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Course.lecturer_id == lecturer_id)
        .all()
    )
    return {r.student_id for r in rows}


@router.get("/", response_model=list[StudentOut])
def list_students(
    level: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin → all students (optional ?level= filter).
    Lecturer → only their students (same level filter applies).
    """
    query = db.query(Student)
    if level:
        query = query.filter(Student.level == level)

    if current_user.role == "lecturer":
        allowed = _lecturer_student_ids(db, current_user.id)
        query = query.filter(Student.id.in_(allowed))

    return query.all()


@router.post(
    "/",
    response_model=StudentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_student(body: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student record. Admin only."""
    if db.query(Student).filter(Student.matric_no == body.matric_no).first():
        raise HTTPException(400, detail="Matric number already exists")
    student = Student(**body.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, detail="Student not found")

    if current_user.role == "lecturer":
        if student_id not in _lecturer_student_ids(db, current_user.id):
            raise HTTPException(403, detail="Access denied")

    return student


@router.patch(
    "/{student_id}",
    response_model=StudentOut,
    dependencies=[Depends(require_admin)],
)
def update_student(student_id: int, body: StudentUpdate, db: Session = Depends(get_db)):
    """Partially update a student. Admin only."""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, detail="Student not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student. Admin only."""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, detail="Student not found")
    db.delete(student)
    db.commit()


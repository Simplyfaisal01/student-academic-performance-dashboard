"""
Courses router.
- Admin: full CRUD on all courses.
- Lecturer: read-only; only their own courses.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.database import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=list[CourseOut])
def list_courses(
    level: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin → all courses (optional ?level= filter).
    Lecturer → only courses assigned to them.
    """
    query = db.query(Course)
    if level:
        query = query.filter(Course.level == level)
    if current_user.role == "lecturer":
        query = query.filter(Course.lecturer_id == current_user.id)
    return query.all()


@router.post(
    "/",
    response_model=CourseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_course(body: CourseCreate, db: Session = Depends(get_db)):
    """Create a course. Admin only."""
    if db.query(Course).filter(Course.code == body.code).first():
        raise HTTPException(400, detail="Course code already exists")
    course = Course(**body.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, detail="Course not found")
    if current_user.role == "lecturer" and course.lecturer_id != current_user.id:
        raise HTTPException(403, detail="Access denied")
    return course


@router.patch(
    "/{course_id}",
    response_model=CourseOut,
    dependencies=[Depends(require_admin)],
)
def update_course(course_id: int, body: CourseUpdate, db: Session = Depends(get_db)):
    """Partially update a course. Admin only."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, detail="Course not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course. Admin only."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, detail="Course not found")
    db.delete(course)
    db.commit()


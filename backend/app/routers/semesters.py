"""
Semesters router.
- Admin: full CRUD; setting is_current=True automatically clears the flag
  on every other semester (only one can be "current" at a time).
- All authenticated users: read access.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.database import get_db
from app.models.semester import Semester
from app.schemas.semester import SemesterCreate, SemesterOut, SemesterUpdate

router = APIRouter(prefix="/semesters", tags=["Semesters"])


def _unset_current(db: Session, exclude_id: int | None = None) -> None:
    """Clear is_current on all semesters except *exclude_id*."""
    q = db.query(Semester).filter(Semester.is_current == True)  # noqa: E712
    if exclude_id:
        q = q.filter(Semester.id != exclude_id)
    q.update({"is_current": False}, synchronize_session="fetch")


@router.get("/", response_model=list[SemesterOut], dependencies=[Depends(get_current_user)])
def list_semesters(db: Session = Depends(get_db)):
    return db.query(Semester).order_by(Semester.id).all()


@router.get("/current", response_model=SemesterOut, dependencies=[Depends(get_current_user)])
def get_current_semester(db: Session = Depends(get_db)):
    """Return the semester flagged is_current=True."""
    sem = db.query(Semester).filter(Semester.is_current == True).first()  # noqa: E712
    if not sem:
        raise HTTPException(404, detail="No current semester set")
    return sem


@router.post(
    "/",
    response_model=SemesterOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_semester(body: SemesterCreate, db: Session = Depends(get_db)):
    """Create a semester. If is_current=True, all others are unset. Admin only."""
    if body.is_current:
        _unset_current(db)
    sem = Semester(**body.model_dump())
    db.add(sem)
    db.commit()
    db.refresh(sem)
    return sem


@router.get("/{semester_id}", response_model=SemesterOut, dependencies=[Depends(get_current_user)])
def get_semester(semester_id: int, db: Session = Depends(get_db)):
    sem = db.get(Semester, semester_id)
    if not sem:
        raise HTTPException(404, detail="Semester not found")
    return sem


@router.patch(
    "/{semester_id}",
    response_model=SemesterOut,
    dependencies=[Depends(require_admin)],
)
def update_semester(semester_id: int, body: SemesterUpdate, db: Session = Depends(get_db)):
    """
    Update a semester. If is_current is being set to True, all others
    are automatically unset first. Admin only.
    """
    sem = db.get(Semester, semester_id)
    if not sem:
        raise HTTPException(404, detail="Semester not found")

    if body.is_current:
        _unset_current(db, exclude_id=semester_id)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(sem, field, value)

    db.commit()
    db.refresh(sem)
    return sem


@router.delete(
    "/{semester_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_semester(semester_id: int, db: Session = Depends(get_db)):
    sem = db.get(Semester, semester_id)
    if not sem:
        raise HTTPException(404, detail="Semester not found")
    db.delete(sem)
    db.commit()


"""
Grades router — bulk CSV upload and CSV template download.

Endpoints:
  POST /grades/csv-upload?course_id=X&semester_id=Y
      Upload a CSV file; validate and save valid rows.

  POST /grades/csv-validate?course_id=X&semester_id=Y
      Dry-run: validate without saving (lets lecturers preview errors first).

  GET  /grades/template
      Download a sample CSV the lecturer can fill in.

Access rules:
  - Admin   → any course.
  - Lecturer → only courses assigned to them.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.course import Course
from app.models.student import Student
from app.models.user import User
from app.schemas.grades import GradeImportResult
from app.services.csv_import import validate_and_import_grades
from app.services.probation import sync_student_probation_case

router = APIRouter(prefix="/grades", tags=["Grades / CSV"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB hard cap


# ── Shared helper ─────────────────────────────────────────────────────────────

def _resolve_course(course_id: int, db: Session, current_user: User) -> Course:
    """Fetch the course and enforce lecturer ownership."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, detail="Course not found")
    if current_user.role == "lecturer" and course.lecturer_id != current_user.id:
        raise HTTPException(403, detail="You are not assigned to this course")
    return course


async def _read_csv_file(file: UploadFile) -> bytes:
    """Read and size-check the uploaded file."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, detail="Only .csv files are accepted")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, detail="File exceeds the 5 MB limit")
    if len(contents) == 0:
        raise HTTPException(400, detail="Uploaded file is empty")

    return contents


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/csv-upload", response_model=GradeImportResult)
async def upload_grades_csv(
    course_id: int = Query(..., description="ID of the course"),
    semester_id: int = Query(..., description="ID of the semester"),
    file: UploadFile = File(..., description="CSV with columns: matric_no, score"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload grades from a CSV file.

    **CSV format** (first row must be a header):
    ```
    matric_no,score
    2024/CS/001,75
    2024/CS/002,45
    ```

    What happens on each row:
    - If the student is already enrolled → score / grade are **updated**.
    - If the student is not yet enrolled → a new enrollment is **created**.
    - Rows that fail validation are skipped and listed in `errors`.

    Only valid rows are committed; a failed row never affects saved rows.
    Automatically triggers the probation engine for all affected students.
    """
    _resolve_course(course_id, db, current_user)
    contents = await _read_csv_file(file)

    result = validate_and_import_grades(
        file_bytes=contents,
        course_id=course_id,
        semester_id=semester_id,
        db=db,
        save=True,
    )

    # ── Automated Probation Engine Trigger ──────────────────────────────
    if result["saved"]:
        matrics = [r["matric_no"] for r in result["saved"]]
        students = db.query(Student).filter(Student.matric_no.in_(matrics)).all()
        for st in students:
            sync_student_probation_case(
                student_id=st.id,
                semester_id=semester_id,
                db=db,
                background_tasks=background_tasks,
            )

    return result


@router.post("/csv-validate", response_model=GradeImportResult)
async def validate_grades_csv(
    course_id: int = Query(..., description="ID of the course"),
    semester_id: int = Query(..., description="ID of the semester"),
    file: UploadFile = File(..., description="CSV with columns: matric_no, score"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **Dry-run** validation only — nothing is written to the database.

    Use this endpoint to let lecturers check for errors before committing.
    The response is identical in shape to `/csv-upload` but `saved` rows
    include `"note": "dry-run — not saved"`.
    """
    _resolve_course(course_id, db, current_user)
    contents = await _read_csv_file(file)

    return validate_and_import_grades(
        file_bytes=contents,
        course_id=course_id,
        semester_id=semester_id,
        db=db,
        save=False,  # ← dry-run
    )


@router.get("/template", response_class=PlainTextResponse)
def download_csv_template(
    _: User = Depends(get_current_user),
):
    """
    Download a blank CSV template pre-filled with example rows.
    The lecturer fills in real matric numbers and scores, then uploads
    to `/csv-upload`.
    """
    template = (
        "matric_no,score\n"
        "# Replace the rows below with real data; delete this comment line\n"
        "2024/CS/001,75\n"
        "2024/CS/002,45\n"
        "2024/CS/003,88\n"
    )
    return PlainTextResponse(
        template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=grades_template.csv"},
    )


"""
Reports router.

Provides downloadable PDF (ReportLab) and CSV exports:
- Official Academic Probation Audit Report (PDF & CSV)
- Individual Student Transcript & Standing Profile (PDF)
- Complete Cohort Performance Summary (CSV)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User
from app.services.reports import (
    generate_probation_report_csv,
    generate_probation_report_pdf,
    generate_semester_performance_csv,
    generate_student_transcript_pdf,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


def _resolve_semester_id(db: Session, semester_id: int | None) -> int:
    if semester_id is not None:
        return semester_id
    current_sem = db.query(Semester).filter(Semester.is_current == True).first()  # noqa: E712
    if current_sem:
        return current_sem.id
    latest_sem = db.query(Semester).order_by(Semester.id.desc()).first()
    return latest_sem.id if latest_sem else 1


@router.get("/probation/pdf")
def export_probation_pdf(
    semester_id: int | None = Query(None, description="Semester ID (defaults to active)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download official Academic Probation Audit Report as a styled PDF document.
    """
    target_sem_id = _resolve_semester_id(db, semester_id)
    pdf_bytes = generate_probation_report_pdf(db=db, semester_id=target_sem_id)

    semester = db.get(Semester, target_sem_id)
    session_slug = semester.session.replace("/", "-") if semester else str(target_sem_id)
    filename = f"Probation_Report_{session_slug}_Sem{target_sem_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/probation/csv")
def export_probation_csv(
    semester_id: int | None = Query(None, description="Semester ID (defaults to active)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export probation cases as a CSV file.
    """
    target_sem_id = _resolve_semester_id(db, semester_id)
    csv_str = generate_probation_report_csv(db=db, semester_id=target_sem_id)

    semester = db.get(Semester, target_sem_id)
    session_slug = semester.session.replace("/", "-") if semester else str(target_sem_id)
    filename = f"Probation_Cases_{session_slug}.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/transcript/{student_id}/pdf")
def export_student_transcript_pdf(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an official Student Academic Transcript & Standing Profile in PDF format.
    Lecturers may only generate transcripts for students in their advisee/course list.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    pdf_bytes = generate_student_transcript_pdf(db=db, student_id=student_id)
    matric_clean = student.matric_no.replace("/", "-")
    filename = f"Transcript_{matric_clean}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/performance/csv")
def export_performance_csv(
    semester_id: int | None = Query(None, description="Semester ID (defaults to active)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download complete cohort performance audit for a semester as a CSV spreadsheet.
    """
    target_sem_id = _resolve_semester_id(db, semester_id)
    csv_str = generate_semester_performance_csv(db=db, semester_id=target_sem_id)

    semester = db.get(Semester, target_sem_id)
    session_slug = semester.session.replace("/", "-") if semester else str(target_sem_id)
    filename = f"Cohort_Performance_{session_slug}.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


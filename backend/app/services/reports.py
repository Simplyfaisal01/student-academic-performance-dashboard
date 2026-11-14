"""
Reports generation service: PDF (using ReportLab) and CSV export.

Produces official university-style academic reports:
1. Academic Probation Report (PDF & CSV)
2. At-Risk Student Diagnostic Report (PDF & CSV)
3. Overall Semester Performance Summary (PDF & CSV)
4. Individual Student Transcript & Academic History (PDF)
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.probation import ProbationCase, ProbationStatus
from app.models.semester import Semester
from app.models.student import Student
from app.services.gpa import compute_gpa, count_failed_courses
from app.services.probation import evaluate_probation


# ── Styles Helper ─────────────────────────────────────────────────────────────

def _get_pdf_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#142B4A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#087B5B"),
        spaceAfter=2,
    )

    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748B"),
    )

    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    td_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#263445"),
    )

    td_bold = ParagraphStyle(
        "TableCellBold",
        parent=td_style,
        fontName="Helvetica-Bold",
    )

    td_danger = ParagraphStyle(
        "TableCellDanger",
        parent=td_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#DC2626"),
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "meta": meta_style,
        "th": th_style,
        "td": td_style,
        "td_bold": td_bold,
        "td_danger": td_danger,
    }


def _draw_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#94A3B8"))
    canvas.drawString(
        54, 30,
        f"AcadTrack Academic Monitoring System • Confidential University Report • Page {doc.page}"
    )
    canvas.drawRightString(
        letter[0] - 54, 30,
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    canvas.restoreState()


# ── Data Assembly Helpers ─────────────────────────────────────────────────────

def _get_evaluated_students_for_semester(db: Session, semester_id: int):
    """Fetch students and compute GPA, failed courses, and standing for a semester."""
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.semester_id == semester_id, Enrollment.score.isnot(None))
        .all()
    )

    by_student: dict[int, list[Enrollment]] = {}
    for e in enrollments:
        by_student.setdefault(e.student_id, []).append(e)

    students = db.query(Student).filter(Student.id.in_(list(by_student.keys()))).all()
    student_map = {s.id: s for s in students}

    records = []
    for s_id, enrs in by_student.items():
        st = student_map.get(s_id)
        if not st:
            continue
        gpa = compute_gpa(enrs)
        fails = count_failed_courses(enrs)
        is_flagged, reasons = evaluate_probation(gpa, fails)

        standing = "Good Standing"
        if gpa is not None and gpa < 1.0 or fails >= 4:
            standing = "Critical Risk"
        elif is_flagged:
            standing = "Probation"
        elif (gpa is not None and gpa < 2.0) or fails > 0:
            standing = "At Risk"

        records.append({
            "student_id": st.id,
            "matric_no": st.matric_no,
            "name": st.name,
            "level": st.level,
            "advisor": st.advisor.name if st.advisor else "Departmental Advisor",
            "gpa": gpa,
            "fails": fails,
            "standing": standing,
            "reasons": reasons if reasons else "Satisfactory progress",
            "enrollments": enrs,
        })

    # Sort by level ascending, then by name
    records.sort(key=lambda r: (r["level"], r["name"]))
    return records


# ── PDF Generators ────────────────────────────────────────────────────────────

def generate_probation_report_pdf(db: Session, semester_id: int) -> bytes:
    """Generate a PDF listing all probation and critical risk students for a semester."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45,
    )

    styles = _get_pdf_styles()
    semester = db.get(Semester, semester_id)
    sem_title = f"{semester.session} — {semester.name}" if semester else f"Semester #{semester_id}"

    records = _get_evaluated_students_for_semester(db, semester_id)
    probation_records = [
        r for r in records if r["standing"] in ("Probation", "Critical Risk")
    ]

    elements = [
        Paragraph("STUDENT ACADEMIC PERFORMANCE & PROBATION MONITORING", styles["title"]),
        Paragraph(f"OFFICIAL ACADEMIC PROBATION AUDIT REPORT — {sem_title}", styles["subtitle"]),
        Paragraph(
            f"Institutional Regulations: Flagged if Semester GPA < {settings.PROBATION_MIN_GPA:.2f} "
            f"OR Failed Courses > {settings.PROBATION_MAX_FAILED_COURSES}",
            styles["meta"],
        ),
        Spacer(1, 14),
    ]

    # Summary metric block
    summary_data = [
        [
            Paragraph("Total Students Evaluated", styles["meta"]),
            Paragraph("Probation Cases Flagged", styles["meta"]),
            Paragraph("Critical Risk Cases", styles["meta"]),
            Paragraph("Pass Rate for Cohort", styles["meta"]),
        ],
        [
            Paragraph(str(len(records)), styles["td_bold"]),
            Paragraph(str(len(probation_records)), styles["td_danger"]),
            Paragraph(
                str(sum(1 for r in probation_records if r["standing"] == "Critical Risk")),
                styles["td_danger"],
            ),
            Paragraph(
                f"{(len(records) - len(probation_records)) / (len(records) or 1) * 100:.1f}%",
                styles["td_bold"],
            ),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[135, 135, 135, 135])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # Main data table
    table_headers = [
        Paragraph("Matric No", styles["th"]),
        Paragraph("Student Name", styles["th"]),
        Paragraph("Level", styles["th"]),
        Paragraph("GPA", styles["th"]),
        Paragraph("Fails", styles["th"]),
        Paragraph("Standing", styles["th"]),
        Paragraph("Diagnostic Reasons", styles["th"]),
    ]
    table_rows = [table_headers]

    for r in probation_records:
        gpa_str = f"{r['gpa']:.2f}" if r["gpa"] is not None else "N/A"
        table_rows.append([
            Paragraph(r["matric_no"], styles["td_bold"]),
            Paragraph(r["name"], styles["td"]),
            Paragraph(f"{r['level']}L", styles["td"]),
            Paragraph(gpa_str, styles["td_danger"]),
            Paragraph(str(r["fails"]), styles["td_danger"]),
            Paragraph(r["standing"], styles["td_danger"]),
            Paragraph(r["reasons"], styles["td"]),
        ])

    if len(table_rows) == 1:
        table_rows.append([
            Paragraph("No probation cases recorded for this semester.", styles["td"]),
            Paragraph("", styles["td"]),
            Paragraph("", styles["td"]),
            Paragraph("", styles["td"]),
            Paragraph("", styles["td"]),
            Paragraph("", styles["td"]),
            Paragraph("", styles["td"]),
        ])

    data_table = Table(
        table_rows,
        colWidths=[80, 110, 35, 38, 32, 75, 170],
        repeatRows=1,
    )
    data_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#142B4A")),
            ("ALIGN", (2, 0), (4, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(data_table)

    # Signatures
    elements.append(Spacer(1, 28))
    sig_data = [
        [
            Paragraph("____________________________<br/>Head of Department / Exam Officer", styles["meta"]),
            Paragraph("____________________________<br/>Chairman, Academic Review Panel", styles["meta"]),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    elements.append(sig_table)

    doc.build(elements, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_student_transcript_pdf(db: Session, student_id: int) -> bytes:
    """Generate a student academic transcript PDF showing all semesters and CGPA."""
    student = db.get(Student, student_id)
    if not student:
        raise ValueError(f"Student #{student_id} not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45,
    )

    styles = _get_pdf_styles()

    # Get student's enrollments ordered by semester
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id)
        .join(Semester, Enrollment.semester_id == Semester.id)
        .order_by(Semester.id.asc(), Enrollment.course_id.asc())
        .all()
    )

    by_sem: dict[int, list[Enrollment]] = {}
    for e in enrollments:
        by_sem.setdefault(e.semester_id, []).append(e)

    # Compute overall CGPA
    graded = [e for e in enrollments if e.score is not None]
    cgpa = compute_gpa(graded)

    elements = [
        Paragraph("STUDENT ACADEMIC PERFORMANCE & PROBATION MONITORING", styles["title"]),
        Paragraph("OFFICIAL STUDENT ACADEMIC TRANSCRIPT & STANDING PROFILE", styles["subtitle"]),
        Spacer(1, 10),
    ]

    # Student metadata header block
    info_data = [
        [
            Paragraph(f"<b>Student Name:</b> {student.name}", styles["td"]),
            Paragraph(f"<b>Matric Number:</b> {student.matric_no}", styles["td"]),
        ],
        [
            Paragraph(f"<b>Current Level:</b> {student.level} Level", styles["td"]),
            Paragraph(
                f"<b>Assigned Advisor:</b> {student.advisor.name if student.advisor else 'Departmental Advisor'}",
                styles["td"],
            ),
        ],
        [
            Paragraph(f"<b>Cumulative GPA (CGPA):</b> <b>{cgpa:.2f}</b>" if cgpa else "<b>CGPA:</b> N/A", styles["td_bold"]),
            Paragraph(f"<b>Official Email:</b> {student.email or 'N/A'}", styles["td"]),
        ],
    ]
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(info_table)
    elements.append(Spacer(1, 14))

    # Semester tables
    semesters = db.query(Semester).order_by(Semester.id.asc()).all()
    sem_map = {s.id: s for s in semesters}

    for sem_id, sem_enrollments in by_sem.items():
        sem = sem_map.get(sem_id)
        sem_name = f"{sem.session} — {sem.name}" if sem else f"Semester {sem_id}"
        sem_gpa = compute_gpa([e for e in sem_enrollments if e.score is not None])
        sem_fails = count_failed_courses(sem_enrollments)
        _, reasons = evaluate_probation(sem_gpa, sem_fails)

        elements.append(
            Paragraph(
                f"<b>{sem_name}</b> (Semester GPA: <b>{sem_gpa:.2f}</b> • Failed Courses: <b>{sem_fails}</b>)",
                styles["subtitle"],
            )
        )
        if reasons:
            elements.append(Paragraph(f"<b>Audit Flag:</b> {reasons}", styles["td_danger"]))
        elements.append(Spacer(1, 4))

        sem_table_rows = [
            [
                Paragraph("Code", styles["th"]),
                Paragraph("Course Title", styles["th"]),
                Paragraph("Units", styles["th"]),
                Paragraph("Score", styles["th"]),
                Paragraph("Grade", styles["th"]),
                Paragraph("Points", styles["th"]),
            ]
        ]

        for e in sem_enrollments:
            course = e.course
            score_str = f"{e.score:.0f}" if e.score is not None else "—"
            grade_str = e.grade or "—"
            pts_str = f"{e.grade_point:.1f}" if e.grade_point is not None else "—"
            is_f = e.grade == "F"

            sem_table_rows.append([
                Paragraph(course.code if course else "", styles["td_bold"]),
                Paragraph(course.title if course else "", styles["td"]),
                Paragraph(str(course.credit_units if course else 3), styles["td"]),
                Paragraph(score_str, styles["td_danger"] if is_f else styles["td"]),
                Paragraph(grade_str, styles["td_danger"] if is_f else styles["td_bold"]),
                Paragraph(pts_str, styles["td"]),
            ])

        st_table = Table(
            sem_table_rows,
            colWidths=[65, 275, 45, 50, 50, 55],
        )
        st_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087B5B")),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(st_table)
        elements.append(Spacer(1, 12))

    # Verification Sign-off
    elements.append(Spacer(1, 16))
    sig_data = [
        [
            Paragraph("____________________________<br/>Registrar / Dean of Academic Affairs", styles["meta"]),
            Paragraph("____________________________<br/>Official University Seal & Date", styles["meta"]),
        ]
    ]
    elements.append(Table(sig_data, colWidths=[270, 270]))

    doc.build(elements, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ── CSV Generators ────────────────────────────────────────────────────────────

def generate_probation_report_csv(db: Session, semester_id: int) -> str:
    """Generate CSV string of probation cases."""
    records = _get_evaluated_students_for_semester(db, semester_id)
    probation_records = [
        r for r in records if r["standing"] in ("Probation", "Critical Risk")
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Matric No", "Student Name", "Level", "Semester GPA",
        "Failed Courses", "Academic Standing", "Diagnostic Reasons", "Advisor"
    ])

    for r in probation_records:
        writer.writerow([
            r["matric_no"],
            r["name"],
            r["level"],
            f"{r['gpa']:.2f}" if r["gpa"] is not None else "N/A",
            r["fails"],
            r["standing"],
            r["reasons"],
            r["advisor"],
        ])

    return output.getvalue()


def generate_semester_performance_csv(db: Session, semester_id: int) -> str:
    """Generate complete cohort CSV summary for a semester."""
    records = _get_evaluated_students_for_semester(db, semester_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Matric No", "Student Name", "Level", "Semester GPA",
        "Failed Courses", "Academic Standing", "Diagnostic Reasons", "Advisor"
    ])

    for r in records:
        writer.writerow([
            r["matric_no"],
            r["name"],
            r["level"],
            f"{r['gpa']:.2f}" if r["gpa"] is not None else "N/A",
            r["fails"],
            r["standing"],
            r["reasons"],
            r["advisor"],
        ])

    return output.getvalue()


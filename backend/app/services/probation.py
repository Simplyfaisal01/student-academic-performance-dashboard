"""
Probation Engine Service.

Contains pure business logic functions (easily unit-tested) and ORM synchronization
helpers that monitor student academic standing and trigger probation cases.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enrollment import Enrollment
from app.models.probation import ProbationCase, ProbationStatus
from app.models.student import Student
from app.services.gpa import compute_gpa, count_failed_courses
from app.services.notifications import notify_advisor_of_probation


# ── Pure Evaluation Function ─────────────────────────────────────────────────

def evaluate_probation(
    gpa: float | None,
    failed_courses_count: int,
) -> tuple[bool, str]:
    """
    Pure function to evaluate if performance criteria trigger academic probation.

    Triggers (configurable in settings):
      1. GPA < settings.PROBATION_MIN_GPA (default: 1.5)
      2. failed_courses_count > settings.PROBATION_MAX_FAILED_COURSES (default: 2)

    Returns:
      (is_flagged: bool, reasons: str)
    """
    reasons: list[str] = []

    if gpa is not None and gpa < settings.PROBATION_MIN_GPA:
        reasons.append(f"GPA {gpa:.2f} below {settings.PROBATION_MIN_GPA}")

    if failed_courses_count > settings.PROBATION_MAX_FAILED_COURSES:
        reasons.append(f"{failed_courses_count} failed courses")

    is_flagged = len(reasons) > 0
    return is_flagged, "; ".join(reasons)


# ── Database Sync Logic ───────────────────────────────────────────────────────

def sync_student_probation_case(
    student_id: int,
    semester_id: int,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> ProbationCase | None:
    """
    Evaluate student's standing for a specific semester and create/update/clear
    their ProbationCase accordingly.

    Triggers advisor notifications and emails on status transitions.
    """
    student = db.get(Student, student_id)
    if not student:
        return None

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student_id,
            Enrollment.semester_id == semester_id,
        )
        .all()
    )

    if not enrollments:
        return None

    # Compute standing
    gpa = compute_gpa(enrollments)
    failed_count = count_failed_courses(enrollments)
    is_flagged, reasons = evaluate_probation(gpa, failed_count)

    # Check for existing probation case
    case = (
        db.query(ProbationCase)
        .filter(
            ProbationCase.student_id == student_id,
            ProbationCase.semester_id == semester_id,
        )
        .first()
    )

    if is_flagged:
        if not case:
            # Create new active probation case
            case = ProbationCase(
                student_id=student_id,
                semester_id=semester_id,
                reasons=reasons,
                status=ProbationStatus.active,
                notes=f"Flagged automatically: GPA={gpa if gpa is not None else 'N/A'}, Fails={failed_count}",
            )
            db.add(case)
            db.commit()
            db.refresh(case)

            # Notify advisor
            notify_advisor_of_probation(db, case, student.advisor, action="flagged")

        elif case.status != ProbationStatus.active:
            # Re-activate probation if previously cleared
            case.status = ProbationStatus.active
            case.reasons = reasons
            case.resolved_on = None
            case.notes = (case.notes or "") + f"\nRe-flagged: {reasons}"
            db.commit()
            db.refresh(case)

            notify_advisor_of_probation(db, case, student.advisor, action="flagged")

        else:
            # Update reasons if they changed
            if case.reasons != reasons:
                case.reasons = reasons
                db.commit()
                db.refresh(case)

        return case

    else:
        # Not flagged — if an active or reviewing case exists, resolve it to "cleared"
        if case and case.status in (ProbationStatus.active, ProbationStatus.reviewing):
            case.status = ProbationStatus.cleared
            case.resolved_on = datetime.now(timezone.utc)
            cleared_note = f"Cleared: GPA={gpa if gpa is not None else 'N/A'}, Fails={failed_count}"
            case.notes = (case.notes + "\n" + cleared_note) if case.notes else cleared_note
            db.commit()
            db.refresh(case)

            notify_advisor_of_probation(db, case, student.advisor, action="cleared")

        return case


def evaluate_semester_probations(
    semester_id: int,
    db: Session,
    background_tasks: BackgroundTasks | None = None,
) -> dict:
    """
    Run the probation engine across all students enrolled in a semester.
    Useful for batch evaluation after bulk imports or initial seeding.
    """
    student_ids = (
        db.query(Enrollment.student_id)
        .filter(Enrollment.semester_id == semester_id)
        .distinct()
        .all()
    )

    evaluated_count = len(student_ids)
    active_count = 0
    cleared_count = 0

    for (s_id,) in student_ids:
        case = sync_student_probation_case(
            student_id=s_id,
            semester_id=semester_id,
            db=db,
            background_tasks=background_tasks,
        )
        if case:
            if case.status == ProbationStatus.active:
                active_count += 1
            elif case.status == ProbationStatus.cleared:
                cleared_count += 1

    return {
        "semester_id": semester_id,
        "students_evaluated": evaluated_count,
        "active_probations": active_count,
        "cleared_probations": cleared_count,
    }


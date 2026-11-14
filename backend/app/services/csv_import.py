"""
CSV import service for bulk grade uploads.

Deliberately a pure function (no FastAPI coupling) so it is easy to unit-test.
The route just reads the file bytes and calls validate_and_import_grades().

Validation rules (all configurable here):
  1. File must be parseable as CSV.
  2. Required columns: matric_no, score.
  3. No duplicate matric_no within the same upload.
  4. score must be numeric and in [0, 100].
  5. matric_no must match a Student row in the database.
  6. Valid rows upsert the Enrollment (create if missing, update if present).
"""
from __future__ import annotations

import io
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.models.student import Student
from app.services.gpa import score_to_grade

REQUIRED_COLUMNS = {"matric_no", "score"}
MAX_ROWS = 500  # guard against huge files; raise in config if needed


# ── Helpers ───────────────────────────────────────────────────────────────────

def _error(row_num: int, matric_no: Any, message: str) -> dict:
    return {"row": row_num, "matric_no": str(matric_no), "error": message}


def _build_result(total: int, saved: list, errors: list) -> dict:
    return {
        "total_rows": total,
        "saved_count": len(saved),
        "error_count": len(errors),
        "saved": saved,
        "errors": errors,
    }


# ── Main function ─────────────────────────────────────────────────────────────

def validate_and_import_grades(
    file_bytes: bytes,
    course_id: int,
    semester_id: int,
    db: Session,
    save: bool = True,
) -> dict:
    """
    Validate a CSV grade file and (if save=True) persist valid rows.

    Parameters
    ----------
    file_bytes : raw bytes of the uploaded CSV file
    course_id  : the course these grades belong to
    semester_id: the semester these grades belong to
    db         : SQLAlchemy session
    save       : False → dry-run (validate only, do not write to DB)

    Returns
    -------
    dict with keys: total_rows, saved_count, error_count, saved[], errors[]
    """
    errors: list[dict] = []
    saved: list[dict] = []

    # ── 1. Parse CSV ──────────────────────────────────────────────────────
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)  # read all as str first
    except Exception as exc:
        return _build_result(0, [], [_error(0, "", f"Cannot parse CSV: {exc}")])

    if df.empty:
        return _build_result(0, [], [_error(0, "", "The file has no data rows")])

    if len(df) > MAX_ROWS:
        return _build_result(
            len(df), [], [_error(0, "", f"File has {len(df)} rows; maximum allowed is {MAX_ROWS}")]
        )

    # ── 2. Normalise column names (strip whitespace, lowercase) ───────────
    df.columns = df.columns.str.strip().str.lower()

    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        return _build_result(
            0, [], [_error(0, "", f"Missing required columns: {sorted(missing_cols)}")]
        )

    df["matric_no"] = df["matric_no"].str.strip()

    # ── 3. Detect duplicate matric_no within the file ─────────────────────
    dup_mask = df["matric_no"].duplicated(keep=False)
    duplicate_matrics: set[str] = set(df.loc[dup_mask, "matric_no"].tolist())

    # ── 4. Pre-fetch all relevant students in one query ───────────────────
    all_matrics = df["matric_no"].dropna().unique().tolist()
    students_by_matric: dict[str, Student] = {
        s.matric_no: s
        for s in db.query(Student).filter(Student.matric_no.in_(all_matrics)).all()
    }

    # ── 5. Per-row validation ─────────────────────────────────────────────
    valid_rows: list[tuple[int, Student, float]] = []

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 1-based numbering; +1 accounts for header

        matric_no: str = row.get("matric_no", "")
        raw_score: str = row.get("score", "")

        # 5a. Duplicate check
        if matric_no in duplicate_matrics:
            errors.append(_error(row_num, matric_no, "Duplicate matric number in this file"))
            continue

        # 5b. Score must be a number
        try:
            score = float(raw_score)
        except (ValueError, TypeError):
            errors.append(_error(row_num, matric_no, f"Score '{raw_score}' is not a valid number"))
            continue

        # 5c. Score must be in range
        if not (0.0 <= score <= 100.0):
            errors.append(_error(row_num, matric_no, f"Score {score} is outside the valid range 0–100"))
            continue

        # 5d. Student must exist
        student = students_by_matric.get(matric_no)
        if not student:
            errors.append(_error(row_num, matric_no, "No student with this matric number found"))
            continue

        valid_rows.append((row_num, student, score))

    # ── 6. Save valid rows (upsert enrollments) ───────────────────────────
    if save and valid_rows:
        # Pre-fetch existing enrollments for this course + semester
        student_ids = [st.id for _, st, _ in valid_rows]
        existing: dict[int, Enrollment] = {
            e.student_id: e
            for e in db.query(Enrollment).filter(
                Enrollment.course_id == course_id,
                Enrollment.semester_id == semester_id,
                Enrollment.student_id.in_(student_ids),
            ).all()
        }

        for row_num, student, score in valid_rows:
            grade_letter, grade_point = score_to_grade(score)
            enrollment = existing.get(student.id)

            if enrollment:
                enrollment.score = score
                enrollment.grade = grade_letter
                enrollment.grade_point = grade_point
            else:
                enrollment = Enrollment(
                    student_id=student.id,
                    course_id=course_id,
                    semester_id=semester_id,
                    score=score,
                    grade=grade_letter,
                    grade_point=grade_point,
                )
                db.add(enrollment)

            saved.append({
                "row": row_num,
                "matric_no": student.matric_no,
                "name": student.name,
                "score": score,
                "grade": grade_letter,
                "grade_point": grade_point,
            })

        db.commit()

    elif not save:
        # Dry-run: report what would be saved without touching DB
        for row_num, student, score in valid_rows:
            grade_letter, grade_point = score_to_grade(score)
            saved.append({
                "row": row_num,
                "matric_no": student.matric_no,
                "name": student.name,
                "score": score,
                "grade": grade_letter,
                "grade_point": grade_point,
                "note": "dry-run — not saved",
            })

    return _build_result(len(df), saved, errors)


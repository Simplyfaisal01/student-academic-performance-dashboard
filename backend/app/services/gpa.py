"""
GPA service — pure functions only, no database access.
This makes them trivial to unit-test in Phase 9.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment


def score_to_grade(score: float) -> tuple[str, float]:
    """
    Convert a numeric score (0-100) to a (grade_letter, grade_point) pair
    using the scale defined in settings.GRADE_SCALE.

    The scale is checked highest-first, so the first matching entry wins.

    >>> score_to_grade(72)
    ('A', 5.0)
    >>> score_to_grade(39)
    ('F', 0.0)
    >>> score_to_grade(40)
    ('E', 1.0)
    """
    for min_score, letter, point in settings.GRADE_SCALE:
        if score >= min_score:
            return letter, point
    return "F", 0.0  # safety fallback (score < 0 edge-case)


def compute_gpa(enrollments: list[Enrollment]) -> float | None:
    """
    Weighted GPA = Σ(grade_point × credit_units) / Σ(credit_units)
    for every enrollment that has a recorded score.

    Returns None when no enrollment has been graded yet (avoids 0 vs None confusion).
    Returns 0.0 when all graded enrollments earned grade_point = 0.

    This formula covers both Semester GPA and CGPA — the caller decides
    which enrollments to pass in.
    """
    weighted_sum = 0.0
    total_units = 0

    for e in enrollments:
        if getattr(e, "grade_point", None) is not None and getattr(e, "score", None) is not None:
            course = getattr(e, "course", None)
            units = getattr(course, "credit_units", 0) if course else getattr(e, "credit_units", 0)
            weighted_sum += e.grade_point * units
            total_units += units

    if total_units == 0:
        return None

    return round(weighted_sum / total_units, 2)


def count_failed_courses(enrollments: list[Enrollment]) -> int:
    """Return the number of graded enrollments with an F grade."""
    return sum(
        1 for e in enrollments
        if e.score is not None and e.grade == "F"
    )


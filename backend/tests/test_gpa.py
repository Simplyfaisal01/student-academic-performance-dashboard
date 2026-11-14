"""
Unit tests for GPA computation and score-to-grade mapping.
Covers standard scenarios and edge cases:
- Exact grade boundary thresholds
- Zero credit units
- Empty and ungraded enrollments
- All failing courses
- Rounding behavior
"""
from types import SimpleNamespace
import unittest

from app.services.gpa import compute_gpa, count_failed_courses, score_to_grade


class TestScoreToGrade(unittest.TestCase):
    def test_standard_grades(self):
        self.assertEqual(score_to_grade(85), ("A", 5.0))
        self.assertEqual(score_to_grade(64), ("B", 4.0))
        self.assertEqual(score_to_grade(55), ("C", 3.0))
        self.assertEqual(score_to_grade(47), ("D", 2.0))
        self.assertEqual(score_to_grade(42), ("E", 1.0))
        self.assertEqual(score_to_grade(32), ("F", 0.0))

    def test_exact_grade_boundaries(self):
        """Boundary values right on the threshold and just below it."""
        # 70 -> A, 69.9 -> B
        self.assertEqual(score_to_grade(70.0), ("A", 5.0))
        self.assertEqual(score_to_grade(69.9), ("B", 4.0))

        # 60 -> B, 59.9 -> C
        self.assertEqual(score_to_grade(60.0), ("B", 4.0))
        self.assertEqual(score_to_grade(59.9), ("C", 3.0))

        # 50 -> C, 49.9 -> D
        self.assertEqual(score_to_grade(50.0), ("C", 3.0))
        self.assertEqual(score_to_grade(49.9), ("D", 2.0))

        # 45 -> D, 44.9 -> E
        self.assertEqual(score_to_grade(45.0), ("D", 2.0))
        self.assertEqual(score_to_grade(44.9), ("E", 1.0))

        # 40 -> E (Pass), 39.9 -> F (Fail)
        self.assertEqual(score_to_grade(40.0), ("E", 1.0))
        self.assertEqual(score_to_grade(39.9), ("F", 0.0))

        # 0 -> F
        self.assertEqual(score_to_grade(0.0), ("F", 0.0))

    def test_extreme_and_negative_scores(self):
        """Scores out of normal range should safely return F."""
        self.assertEqual(score_to_grade(-5), ("F", 0.0))
        self.assertEqual(score_to_grade(100), ("A", 5.0))


class TestComputeGPA(unittest.TestCase):
    def test_standard_gpa_calculation(self):
        """CSC101 (3u, A=5.0), MTH101 (3u, B=4.0), PHY101 (2u, C=3.0) -> (15+12+6)/8 = 33/8 = 4.125 -> 4.12"""
        enrollments = [
            SimpleNamespace(score=75, grade="A", grade_point=5.0, credit_units=3),
            SimpleNamespace(score=65, grade="B", grade_point=4.0, credit_units=3),
            SimpleNamespace(score=55, grade="C", grade_point=3.0, credit_units=2),
        ]
        gpa = compute_gpa(enrollments)
        self.assertEqual(gpa, 4.12)

    def test_with_nested_course_object(self):
        """Supports ORM enrollment with e.course.credit_units."""
        enrollments = [
            SimpleNamespace(score=70, grade="A", grade_point=5.0, course=SimpleNamespace(credit_units=3)),
            SimpleNamespace(score=45, grade="D", grade_point=2.0, course=SimpleNamespace(credit_units=3)),
        ]
        # (15 + 6) / 6 = 3.50
        self.assertEqual(compute_gpa(enrollments), 3.50)

    def test_zero_credit_units_edge_case(self):
        """Zero credit units should not divide by zero; must return None."""
        enrollments = [
            SimpleNamespace(score=75, grade="A", grade_point=5.0, credit_units=0),
            SimpleNamespace(score=80, grade="A", grade_point=5.0, credit_units=0),
        ]
        self.assertIsNone(compute_gpa(enrollments))

    def test_empty_enrollments(self):
        """Empty enrollment list returns None."""
        self.assertIsNone(compute_gpa([]))

    def test_all_ungraded_enrollments(self):
        """Enrollments with score=None return None."""
        enrollments = [
            SimpleNamespace(score=None, grade=None, grade_point=None, credit_units=3),
            SimpleNamespace(score=None, grade=None, grade_point=None, credit_units=2),
        ]
        self.assertIsNone(compute_gpa(enrollments))

    def test_all_failing_grades(self):
        """All F's should return 0.0, NOT None."""
        enrollments = [
            SimpleNamespace(score=30, grade="F", grade_point=0.0, credit_units=3),
            SimpleNamespace(score=25, grade="F", grade_point=0.0, credit_units=3),
        ]
        self.assertEqual(compute_gpa(enrollments), 0.0)

    def test_gpa_rounding(self):
        """Verify strict round to 2 decimal places."""
        # 1 unit of A(5.0), 2 units of B(4.0) -> (5 + 8)/3 = 13/3 = 4.33333... -> 4.33
        enrollments = [
            SimpleNamespace(score=72, grade="A", grade_point=5.0, credit_units=1),
            SimpleNamespace(score=65, grade="B", grade_point=4.0, credit_units=2),
        ]
        self.assertEqual(compute_gpa(enrollments), 4.33)


class TestCountFailedCourses(unittest.TestCase):
    def test_counting_fails(self):
        enrollments = [
            SimpleNamespace(score=75, grade="A"),
            SimpleNamespace(score=35, grade="F"),
            SimpleNamespace(score=55, grade="C"),
            SimpleNamespace(score=28, grade="F"),
            SimpleNamespace(score=None, grade=None),  # Ungraded should not count as fail
        ]
        self.assertEqual(count_failed_courses(enrollments), 2)

    def test_no_fails(self):
        enrollments = [
            SimpleNamespace(score=40, grade="E"),
            SimpleNamespace(score=50, grade="C"),
        ]
        self.assertEqual(count_failed_courses(enrollments), 0)


if __name__ == "__main__":
    unittest.main()


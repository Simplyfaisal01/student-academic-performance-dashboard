"""
Supplementary pytest tests (Phase 9) covering the specific cases required
for the final-year project report (Table 4.5):

  Test 1  – GPA of A(3cr) + C(3cr) + F(2cr) = 3.00
  Test 2  – All integer grade boundaries: 100, 70, 69, 60, 59, 50, 49, 45, 44, 40, 39, 0
  Test 3  – GPA exactly 1.50 → NOT flagged
  Test 4  – GPA exactly 1.49 → flagged (GPA reason in output)
  Test 5  – Exactly 2 failed courses → NOT flagged
  Test 6  – Exactly 3 failed courses → flagged (failed-courses reason)
  Test 7  – Both criteria simultaneously → one case with both reasons
  Test 8  – Active case exists and criteria still met → NO duplicate case
  Test 9  – Active case exists and criteria no longer met → case becomes "cleared"
  Test 10 – Student with no graded courses → no error, not flagged
  Test 11 – upload_sample_with_errors.csv (fixture) → 30 valid, 6 errors
  Test 12 – upload_sample_errors_2.csv (fixture)   → 29 valid, 7 errors;
             boundary scores 0, 39, 40, 100 all accepted
  Test 13 – File with wrong column names → rejected wholesale (saved_count == 0)

Database tests (Tests 7-10, 11-12) use an in-memory SQLite database via setUp.
They never touch the real MySQL database.
"""
import os
import unittest
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.course import Course
from app.models.semester import Semester
from app.models.enrollment import Enrollment
from app.models.probation import ProbationCase, ProbationStatus

from app.services.gpa import compute_gpa, score_to_grade
from app.services.probation import evaluate_probation, should_flag, sync_student_probation_case
from app.services.csv_import import validate_and_import_grades


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(name: str) -> bytes:
    """Return the raw bytes of a CSV fixture file."""
    path = os.path.join(FIXTURE_DIR, name)
    with open(path, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Test 1 – GPA of A(3cr) + C(3cr) + F(2cr) = 3.00
# ---------------------------------------------------------------------------

class TestGPAWeightedMixed(unittest.TestCase):
    """Test the specific GPA calculation asked for in the brief."""

    def test_gpa_a_c_f_weighted(self):
        """
        A(5.0 pts, 3 cr) + C(3.0 pts, 3 cr) + F(0.0 pts, 2 cr)
        = (15.0 + 9.0 + 0.0) / (3 + 3 + 2)
        = 24.0 / 8
        = 3.00
        """
        enrollments = [
            SimpleNamespace(score=75, grade="A", grade_point=5.0, credit_units=3),
            SimpleNamespace(score=55, grade="C", grade_point=3.0, credit_units=3),
            SimpleNamespace(score=30, grade="F", grade_point=0.0, credit_units=2),
        ]
        gpa = compute_gpa(enrollments)
        self.assertEqual(gpa, 3.00)


# ---------------------------------------------------------------------------
# Test 2 – All integer grade boundaries
# ---------------------------------------------------------------------------

class TestAllGradeBoundaries(unittest.TestCase):
    """
    Verify every integer boundary value on the 5-point scale.
    Scale: 70-100=A(5), 60-69=B(4), 50-59=C(3), 45-49=D(2), 40-44=E(1), 0-39=F(0)
    """

    def _assert_grade(self, score, expected_letter, expected_point):
        letter, point = score_to_grade(score)
        self.assertEqual(
            letter, expected_letter,
            f"score {score}: expected grade '{expected_letter}', got '{letter}'"
        )
        self.assertEqual(
            point, expected_point,
            f"score {score}: expected grade_point {expected_point}, got {point}"
        )

    def test_score_100(self):
        self._assert_grade(100, "A", 5.0)

    def test_score_70(self):
        self._assert_grade(70, "A", 5.0)

    def test_score_69(self):
        # 69 is below the 70 threshold → B
        self._assert_grade(69, "B", 4.0)

    def test_score_60(self):
        self._assert_grade(60, "B", 4.0)

    def test_score_59(self):
        # 59 is below the 60 threshold → C
        self._assert_grade(59, "C", 3.0)

    def test_score_50(self):
        self._assert_grade(50, "C", 3.0)

    def test_score_49(self):
        # 49 is below the 50 threshold → D
        self._assert_grade(49, "D", 2.0)

    def test_score_45(self):
        self._assert_grade(45, "D", 2.0)

    def test_score_44(self):
        # 44 is below the 45 threshold → E
        self._assert_grade(44, "E", 1.0)

    def test_score_40(self):
        self._assert_grade(40, "E", 1.0)

    def test_score_39(self):
        # 39 is below the 40 threshold → F (fail)
        self._assert_grade(39, "F", 0.0)

    def test_score_0(self):
        self._assert_grade(0, "F", 0.0)


# ---------------------------------------------------------------------------
# Tests 3-6 – Probation threshold rules (pure function, no DB)
# ---------------------------------------------------------------------------

class TestProbationThresholds(unittest.TestCase):
    """
    Pure-function tests for evaluate_probation / should_flag.
    Both names are importable from app.services.probation.
    """

    def test_gpa_exactly_1_50_not_flagged(self):
        """GPA = 1.50 is NOT strictly below 1.50, so no probation."""
        flagged, reasons = should_flag(gpa=1.50, failed_courses_count=0)
        self.assertFalse(flagged)
        self.assertEqual(reasons, "")

    def test_gpa_1_49_flagged(self):
        """GPA = 1.49 is strictly below 1.50 → flagged with GPA reason."""
        flagged, reasons = should_flag(gpa=1.49, failed_courses_count=0)
        self.assertTrue(flagged)
        self.assertIn("GPA 1.49 below 1.5", reasons)

    def test_exactly_2_failed_not_flagged(self):
        """Exactly 2 failed courses is NOT strictly greater than 2 → no probation."""
        flagged, reasons = should_flag(gpa=2.50, failed_courses_count=2)
        self.assertFalse(flagged)
        self.assertEqual(reasons, "")

    def test_3_failed_flagged(self):
        """3 failed courses exceeds the threshold of 2 → flagged."""
        flagged, reasons = should_flag(gpa=2.50, failed_courses_count=3)
        self.assertTrue(flagged)
        self.assertIn("3 failed courses", reasons)


# ---------------------------------------------------------------------------
# Tests 7-10 – Lifecycle tests (in-memory SQLite, never touches MySQL)
# ---------------------------------------------------------------------------

class TestProbationLifecycleExtended(unittest.TestCase):
    """
    Integration tests that exercise sync_student_probation_case end-to-end.
    All data lives in a fresh in-memory SQLite database (setUp / tearDown).
    """

    def setUp(self):
        # In-memory SQLite — no MySQL involved
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Minimal seed data: one advisor, one student, one semester, two courses
        advisor = User(
            id=1, name="Advisor", email="a@test.com",
            password_hash="x", role=UserRole.admin,
        )
        self.student = Student(
            id=1, matric_no="FT24TEST0001", name="Test Student",
            level=100, advisor_id=1,
        )
        self.semester = Semester(
            id=1, session="2024/2025", name="First", is_current=True,
        )
        self.c1 = Course(id=1, code="CSC101", title="CompSci", credit_units=3, level=100)
        self.c2 = Course(id=2, code="MTH101", title="Maths",   credit_units=3, level=100)
        self.c3 = Course(id=3, code="PHY101", title="Physics",  credit_units=3, level=100)

        self.db.add_all([advisor, self.student, self.semester, self.c1, self.c2, self.c3])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    # --- helpers -----------------------------------------------------------

    def _enroll(self, course_id, score, grade, grade_point):
        """Add a single enrollment for student 1 / semester 1."""
        e = Enrollment(
            student_id=1, course_id=course_id, semester_id=1,
            score=score, grade=grade, grade_point=grade_point,
        )
        self.db.add(e)
        self.db.commit()
        return e

    def _sync(self):
        return sync_student_probation_case(student_id=1, semester_id=1, db=self.db)

    # --- Test 7 – both criteria at once ------------------------------------

    def test_both_criteria_one_case_two_reasons(self):
        """
        GPA < 1.50 AND more than 2 fails simultaneously.
        Only one ProbationCase row must be created, containing both reasons.
        """
        # 3 × F (0 pts, 3 cr each) → GPA 0.00, 3 fails
        self._enroll(1, 30, "F", 0.0)
        self._enroll(2, 25, "F", 0.0)
        self._enroll(3, 35, "F", 0.0)

        case = self._sync()

        # Exactly one case
        count = self.db.query(ProbationCase).filter(
            ProbationCase.student_id == 1,
            ProbationCase.semester_id == 1,
        ).count()
        self.assertEqual(count, 1)

        # Both reason strings present
        self.assertIn("GPA 0.00 below 1.5", case.reasons)
        self.assertIn("3 failed courses", case.reasons)
        self.assertEqual(case.status, ProbationStatus.active)

    # --- Test 8 – active case + criteria still met → no duplicate ----------

    def test_active_case_no_duplicate_on_re_sync(self):
        """
        Running sync twice while the student is still on probation must not
        create a second ProbationCase row.
        """
        self._enroll(1, 30, "F", 0.0)   # GPA 0.00, 1 fail
        case1 = self._sync()
        case_id = case1.id

        # Run again without changing any grades
        case2 = self._sync()

        self.assertEqual(case2.id, case_id, "sync must reuse the existing case, not create a new one")
        total = self.db.query(ProbationCase).filter(
            ProbationCase.student_id == 1,
            ProbationCase.semester_id == 1,
        ).count()
        self.assertEqual(total, 1)

    # --- Test 9 – active case + grades improve → case becomes "cleared" ---

    def test_case_cleared_when_grades_improve(self):
        """
        After flagging a student, if their grade is revised up to a passing
        mark the existing active case must transition to 'cleared'.
        """
        e = self._enroll(1, 30, "F", 0.0)
        self._sync()   # creates active case

        # Grade revised to A
        e.score = 80
        e.grade = "A"
        e.grade_point = 5.0
        self.db.commit()

        cleared = self._sync()

        self.assertEqual(cleared.status, ProbationStatus.cleared)
        self.assertIsNotNone(cleared.resolved_on)

    # --- Test 10 – no graded courses → no error, not flagged ---------------

    def test_no_graded_courses_not_flagged(self):
        """
        A student with no enrollments at all (or only None-score rows) must
        not cause an exception and must not receive a probation case.
        """
        # No enrollments added at all
        case = self._sync()

        self.assertIsNone(case, "no case should be created when there are no graded enrollments")
        count = self.db.query(ProbationCase).filter(
            ProbationCase.student_id == 1,
            ProbationCase.semester_id == 1,
        ).count()
        self.assertEqual(count, 0)


# ---------------------------------------------------------------------------
# Tests 11-13 – CSV validation (in-memory SQLite, never touches MySQL)
# ---------------------------------------------------------------------------

class TestCSVValidationFixtures(unittest.TestCase):
    """
    Tests for the bulk CSV grade upload and validation logic.

    Students FT24BCMP0001 … FT24BCMP0036 are seeded in the test database.
    FT99UNKNOWN1 and FT99UNKNOWN2 are intentionally NOT seeded (unknown matrics).

    Fixture files live in backend/tests/fixtures/:
      upload_sample_with_errors.csv  – designed to yield 30 valid, 6 errors
      upload_sample_errors_2.csv     – designed to yield 29 valid, 7 errors
      upload_sample_wrong_columns.csv – wrong headers → rejected wholesale
    """

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed students FT24BCMP0001 … FT24BCMP0036
        for i in range(1, 37):
            matric = f"FT24BCMP{i:04d}"
            self.db.add(Student(id=i, matric_no=matric, name=f"Student {i}", level=100))

        # One course and semester to pass to validate_and_import_grades
        self.db.add(Course(id=10, code="CSC306", title="Comp Sci", credit_units=3, level=300))
        self.db.add(Semester(id=1, session="2024/2025", name="First", is_current=True))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def _import(self, filename: str, save: bool = True) -> dict:
        return validate_and_import_grades(
            file_bytes=_read_fixture(filename),
            course_id=10,
            semester_id=1,
            db=self.db,
            save=save,
        )

    # --- Test 11 – upload_sample_with_errors.csv → 30 valid, 6 errors -----

    def test_upload_sample_with_errors_counts(self):
        """
        The fixture contains 36 rows.
        6 deliberate errors:  1 unknown matric, 1 non-numeric score,
                              1 score > 100, 1 score < 0.
        Wait — let's be explicit: see fixture design comments.
        Expected: saved_count=30, error_count=6.
        """
        res = self._import("upload_sample_with_errors.csv")
        self.assertEqual(
            res["saved_count"], 30,
            f"Expected 30 valid rows, got {res['saved_count']}.\nErrors: {res['errors']}"
        )
        self.assertEqual(
            res["error_count"], 6,
            f"Expected 6 error rows, got {res['error_count']}.\nErrors: {res['errors']}"
        )

    # --- Test 12 – upload_sample_errors_2.csv → 29 valid, 7 errors --------

    def test_upload_sample_errors_2_counts(self):
        """
        The fixture contains 36 rows.
        7 deliberate errors: 2 unknown matrics, 1 non-numeric, 1 > 100, 1 < 0,
                              and two more of the same kinds.
        Boundary scores 0, 39, 40, 100 must NOT be in the error list.
        Expected: saved_count=29, error_count=7.
        """
        res = self._import("upload_sample_errors_2.csv")
        self.assertEqual(
            res["saved_count"], 29,
            f"Expected 29 valid rows, got {res['saved_count']}.\nErrors: {res['errors']}"
        )
        self.assertEqual(
            res["error_count"], 7,
            f"Expected 7 error rows, got {res['error_count']}.\nErrors: {res['errors']}"
        )

    def test_boundary_scores_accepted_in_errors_2(self):
        """
        Scores 0, 39, 40 and 100 are all in [0, 100] and must be accepted
        (i.e. must not appear in the error list).
        """
        res = self._import("upload_sample_errors_2.csv")
        error_matrics = {e["matric_no"] for e in res["errors"]}

        # These students carry boundary scores in the fixture file
        for matric, score in [
            ("FT24BCMP0001", 0),   # score = 0
            ("FT24BCMP0002", 39),  # score = 39
            ("FT24BCMP0003", 40),  # score = 40
            ("FT24BCMP0004", 100), # score = 100
        ]:
            self.assertNotIn(
                matric, error_matrics,
                f"{matric} with score {score} should be valid but appears in errors"
            )

    # --- Test 13 – wrong column names → rejected wholesale -----------------

    def test_wrong_column_names_rejected(self):
        """
        A CSV with headers 'student_id' and 'mark' (instead of matric_no / score)
        must be rejected immediately: saved_count=0 and an error mentioning
        'Missing required columns'.
        """
        res = self._import("upload_sample_wrong_columns.csv")
        self.assertEqual(res["saved_count"], 0)
        self.assertTrue(
            any("Missing required columns" in e["error"] for e in res["errors"]),
            f"Expected 'Missing required columns' error, got: {res['errors']}"
        )


if __name__ == "__main__":
    unittest.main()

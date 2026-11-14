"""
Unit tests for CSV bulk grade ingestion and validation logic:
- Missing required columns
- Duplicate matric numbers
- Non-numeric scores
- Out of range scores (<0 or >100)
- Unknown matric number
- Dry-run vs actual commit
"""
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.student import Student
from app.models.course import Course
from app.models.semester import Semester
from app.models.enrollment import Enrollment
from app.services.csv_import import validate_and_import_grades


class TestCSVGradeImport(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed test student
        self.st1 = Student(id=1, matric_no="FT24BCMP0001", name="Student One", level=100)
        self.st2 = Student(id=2, matric_no="FT24BCMP0002", name="Student Two", level=100)
        self.course = Course(id=10, code="CSC101", title="Comp Sci", credit_units=3, level=100)
        self.semester = Semester(id=1, session="2024/2025", name="First", is_current=True)

        self.db.add_all([self.st1, self.st2, self.course, self.semester])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_valid_csv_import(self):
        csv_bytes = b"matric_no,score\nFT24BCMP0001,75\nFT24BCMP0002,48\n"
        res = validate_and_import_grades(
            file_bytes=csv_bytes,
            course_id=10,
            semester_id=1,
            db=self.db,
            save=True,
        )
        self.assertEqual(res["total_rows"], 2)
        self.assertEqual(res["saved_count"], 2)
        self.assertEqual(res["error_count"], 0)

        # Check DB was written
        e1 = self.db.query(Enrollment).filter(Enrollment.student_id == 1).first()
        self.assertIsNotNone(e1)
        self.assertEqual(e1.score, 75.0)
        self.assertEqual(e1.grade, "A")
        self.assertEqual(e1.grade_point, 5.0)

    def test_missing_column(self):
        csv_bytes = b"matric_number,total_mark\nFT24BCMP0001,75\n"
        res = validate_and_import_grades(
            file_bytes=csv_bytes, course_id=10, semester_id=1, db=self.db, save=True
        )
        self.assertEqual(res["saved_count"], 0)
        self.assertTrue(any("Missing required columns" in e["error"] for e in res["errors"]))

    def test_duplicate_matric_in_file(self):
        csv_bytes = b"matric_no,score\nFT24BCMP0001,75\nFT24BCMP0001,80\n"
        res = validate_and_import_grades(
            file_bytes=csv_bytes, course_id=10, semester_id=1, db=self.db, save=True
        )
        self.assertEqual(res["saved_count"], 0)
        self.assertEqual(res["error_count"], 2)
        self.assertIn("Duplicate", res["errors"][0]["error"])

    def test_score_out_of_range(self):
        csv_bytes = b"matric_no,score\nFT24BCMP0001,150\nFT24BCMP0002,-10\n"
        res = validate_and_import_grades(
            file_bytes=csv_bytes, course_id=10, semester_id=1, db=self.db, save=True
        )
        self.assertEqual(res["saved_count"], 0)
        self.assertEqual(res["error_count"], 2)
        self.assertIn("outside the valid range", res["errors"][0]["error"])

    def test_non_numeric_score(self):
        csv_bytes = b"matric_no,score\nFT24BCMP0001,SEVENTY\n"
        res = validate_and_import_grades(
            file_bytes=csv_bytes, course_id=10, semester_id=1, db=self.db, save=True
        )
        self.assertEqual(res["saved_count"], 0)
        self.assertIn("not a valid number", res["errors"][0]["error"])

    def test_unknown_matric_number(self):
        csv_bytes = b"matric_no,score\nFT99UNKNOWN,65\n"
        res = validate_and_import_grades(
            file_bytes=csv_bytes, course_id=10, semester_id=1, db=self.db, save=True
        )
        self.assertEqual(res["saved_count"], 0)
        self.assertIn("No student with this matric number found", res["errors"][0]["error"])

    def test_dry_run_mode(self):
        """When save=False, reports valid rows without committing to database."""
        csv_bytes = b"matric_no,score\nFT24BCMP0001,75\n"
        res = validate_and_import_grades(
            file_bytes=csv_bytes, course_id=10, semester_id=1, db=self.db, save=False
        )
        self.assertEqual(res["saved_count"], 1)
        self.assertIn("dry-run", res["saved"][0]["note"])

        # DB remains empty
        e = self.db.query(Enrollment).filter(Enrollment.student_id == 1).first()
        self.assertIsNone(e)


if __name__ == "__main__":
    unittest.main()


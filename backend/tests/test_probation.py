"""
Unit tests for the probation engine pure evaluation functions and edge cases:
- Exactly on GPA threshold (1.50)
- Just below GPA threshold (1.49)
- Exactly 2 failed courses (threshold is > 2)
- 3 failed courses
- Multiple triggers simultaneously
- Neither trigger met
- Full dataset verification against expected_probation_results.csv (349 oracle cases)
"""
import os
import unittest
import pandas as pd

from app.services.probation import evaluate_probation
from app.core.config import settings


class TestProbationEnginePure(unittest.TestCase):
    def test_exactly_on_gpa_threshold(self):
        """GPA = 1.50 exactly is NOT on probation (threshold is strictly < 1.50)."""
        is_flagged, reasons = evaluate_probation(gpa=1.50, failed_courses_count=0)
        self.assertFalse(is_flagged)
        self.assertEqual(reasons, "")

    def test_just_below_gpa_threshold(self):
        """GPA = 1.49 is strictly below 1.50 and MUST trigger probation."""
        is_flagged, reasons = evaluate_probation(gpa=1.49, failed_courses_count=0)
        self.assertTrue(is_flagged)
        self.assertIn("GPA 1.49 below 1.5", reasons)

    def test_exactly_max_failed_courses(self):
        """2 failed courses is NOT on probation (threshold is strictly > 2)."""
        is_flagged, reasons = evaluate_probation(gpa=2.50, failed_courses_count=2)
        self.assertFalse(is_flagged)
        self.assertEqual(reasons, "")

    def test_exceeding_failed_courses_threshold(self):
        """3 failed courses exceeds threshold of 2 and MUST trigger probation."""
        is_flagged, reasons = evaluate_probation(gpa=2.20, failed_courses_count=3)
        self.assertTrue(is_flagged)
        self.assertEqual(reasons, "3 failed courses")

    def test_multiple_triggers_simultaneously(self):
        """Both GPA < 1.50 AND > 2 failed courses triggered at once."""
        is_flagged, reasons = evaluate_probation(gpa=1.14, failed_courses_count=3)
        self.assertTrue(is_flagged)
        # Verify both diagnostic strings are formatted and semicolon-separated
        self.assertEqual(reasons, "GPA 1.14 below 1.5; 3 failed courses")

    def test_severe_failure_triggers(self):
        """GPA = 0.00 with 5 fails."""
        is_flagged, reasons = evaluate_probation(gpa=0.00, failed_courses_count=5)
        self.assertTrue(is_flagged)
        self.assertEqual(reasons, "GPA 0.00 below 1.5; 5 failed courses")

    def test_satisfactory_performance(self):
        """High GPA and 0 fails should produce no flags."""
        is_flagged, reasons = evaluate_probation(gpa=4.25, failed_courses_count=0)
        self.assertFalse(is_flagged)
        self.assertEqual(reasons, "")

    def test_ungraded_semester_none_gpa(self):
        """If GPA is None (no graded courses yet), should not flag."""
        is_flagged, reasons = evaluate_probation(gpa=None, failed_courses_count=0)
        self.assertFalse(is_flagged)
        self.assertEqual(reasons, "")


class TestDatasetOracleVerification(unittest.TestCase):
    """
    Verifies evaluate_probation against the 349-case oracle in
    backend/dataset/csv/expected_probation_results.csv.
    """
    def test_dataset_oracle_matches_100_percent(self):
        oracle_path = os.path.join(
            os.path.dirname(__file__), "..", "dataset", "csv", "expected_probation_results.csv"
        )
        if not os.path.exists(oracle_path):
            self.skipTest(f"Oracle file not found at {oracle_path}")

        df = pd.read_csv(oracle_path)
        mismatches = []

        for idx, row in df.iterrows():
            gpa = float(row["gpa"])
            fails = int(row["failed_courses"])
            expected_flagged = bool(int(row["should_be_flagged"]))
            expected_reasons = str(row["expected_reasons"]) if pd.notna(row["expected_reasons"]) else ""

            actual_flagged, actual_reasons = evaluate_probation(gpa, fails)

            if actual_flagged != expected_flagged:
                mismatches.append(
                    f"Row {idx} (Student {row['student_id']}, Sem {row['semester_id']}): "
                    f"Flag expected={expected_flagged}, got={actual_flagged}"
                )
            elif expected_flagged and actual_reasons != expected_reasons:
                mismatches.append(
                    f"Row {idx} (Student {row['student_id']}): "
                    f"Reason expected='{expected_reasons}', got='{actual_reasons}'"
                )

        self.assertEqual(
            len(mismatches),
            0,
            f"Found {len(mismatches)} mismatches with dataset oracle:\n" + "\n".join(mismatches[:5]),
        )


if __name__ == "__main__":
    unittest.main()


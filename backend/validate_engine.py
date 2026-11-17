"""
validate_engine.py — Academic Probation Engine Validation Script
---------------------------------------------------------------
Validates the automated probation monitoring engine against the pre-computed
ground truth answer key (expected_probation_results.csv).

Validation Rules Under Test:
  1. Semester GPA < 1.50, OR
  2. More than 2 failed courses (score < 40) in the semester.

Usage:
    python validate_engine.py --clear
"""
import argparse
import io
import os
import sys
from datetime import datetime

import pandas as pd

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.notification import Notification
from app.models.probation import ProbationCase, ProbationStatus
from app.services.probation import sync_student_probation_case
import app.services.notifications as notifications_module


class OutputTee:
    """Helper class to simultaneously write output to console and a text file."""
    def __init__(self, filepath: str):
        self.terminal = sys.stdout
        self.logfile = open(filepath, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.logfile.write(message)

    def flush(self):
        self.terminal.flush()
        self.logfile.flush()

    def close(self):
        self.logfile.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate academic probation engine against expected ground-truth dataset."
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Wipe notifications and probation_cases tables before running validation.",
    )
    parser.add_argument(
        "--data",
        default=os.path.join(os.path.dirname(__file__), "data", "expected_probation_results.csv"),
        help="Path to expected_probation_results.csv answer key.",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "validation_output.txt"),
        help="Path to save validation console output.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    tee = OutputTee(args.output)
    sys.stdout = tee

    # Silence real email dispatch to console fallback during batch evaluation
    # This keeps the validation output clean while honoring console fallback logic.
    notifications_module.send_email_alert = lambda *a, **kw: True

    print("=" * 80)
    print("🎓 ACADEMIC PROBATION MONITORING ENGINE VALIDATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Answer Key: {os.path.abspath(args.data)}")
    print("=" * 80)

    # 1. Verify existence of answer key
    if not os.path.exists(args.data):
        print(f"\n❌ Error: Answer key CSV not found at '{args.data}'.")
        print("Please ensure expected_probation_results.csv is in backend/data/.")
        sys.exit(1)

    df_expected = pd.read_csv(args.data)
    total_key_records = len(df_expected)
    print(f"\n[+] Loaded ground-truth answer key: {total_key_records} records across semesters.")

    db = SessionLocal()

    # 2. Database cleanliness guard
    existing_cases_count = db.query(ProbationCase).count()
    existing_notifs_count = db.query(Notification).count()

    if existing_cases_count > 0:
        if not args.clear:
            print("\n❌ REFUSAL: The 'probation_cases' table is NOT empty!")
            print(f"    Current records in probation_cases: {existing_cases_count}")
            print(f"    Current records in notifications:    {existing_notifs_count}")
            print("\nTo prevent contaminated evaluation, the engine refuses to run.")
            print("Run with the '--clear' flag to wipe existing records and proceed cleanly:")
            print("    python validate_engine.py --clear\n")
            sys.exit(1)
        else:
            print(f"\n[+] Flag --clear supplied. Purging existing records...")
            # Delete notifications first (foreign key constraint)
            deleted_notifs = db.query(Notification).delete()
            deleted_cases = db.query(ProbationCase).delete()
            db.commit()
            print(f"    ✓ Removed {deleted_notifs} notifications and {deleted_cases} probation cases.")
    else:
        print("\n[+] Database is clean. Ready to execute validation.")

    # 3. Execute Engine for every (student_id, semester_id) in the answer key
    print("\n[+] Executing probation engine on all ground-truth records...")
    processed_count = 0
    for _, row in df_expected.iterrows():
        s_id = int(row["student_id"])
        sem_id = int(row["semester_id"])
        sync_student_probation_case(student_id=s_id, semester_id=sem_id, db=db)
        processed_count += 1

    print(f"    ✓ Evaluated {processed_count} student-semester instances through engine.")

    # 4. Read back all created probation cases
    created_cases = db.query(ProbationCase).all()
    print(f"    ✓ Total probation cases created in database: {len(created_cases)}")

    # Map created cases by (student_id, semester_id)
    case_map = {
        (c.student_id, c.semester_id): c
        for c in created_cases
    }

    # 5. Row-by-row comparison
    results = []
    mismatches = []
    reason_checks = []

    for _, row in df_expected.iterrows():
        s_id = int(row["student_id"])
        sem_id = int(row["semester_id"])
        gpa = float(row["gpa"]) if pd.notna(row["gpa"]) else None
        fails = int(row["failed_courses"]) if pd.notna(row["failed_courses"]) else 0
        exp_flag = int(row["should_be_flagged"]) == 1
        exp_reasons = str(row["expected_reasons"]) if pd.notna(row["expected_reasons"]) else ""

        case = case_map.get((s_id, sem_id))
        eng_flag = bool(case and case.status == ProbationStatus.active)
        eng_reasons = case.reasons if (case and case.status == ProbationStatus.active) else ""

        is_match = (exp_flag == eng_flag)

        record_res = {
            "student_id": s_id,
            "semester_id": sem_id,
            "gpa": gpa,
            "failed_courses": fails,
            "expected_flagged": exp_flag,
            "engine_flagged": eng_flag,
            "match": is_match,
            "expected_reasons": exp_reasons,
            "engine_reasons": eng_reasons,
        }
        results.append(record_res)

        if not is_match:
            mismatches.append(record_res)

        # 6. Reason agreement check (for cases where both agree the student is flagged)
        if exp_flag and eng_flag:
            exp_has_gpa = "GPA" in exp_reasons and "below 1.5" in exp_reasons
            eng_has_gpa = "GPA" in eng_reasons and "below 1.5" in eng_reasons
            gpa_reason_match = (exp_has_gpa == eng_has_gpa)

            exp_has_fails = "failed courses" in exp_reasons
            eng_has_fails = "failed courses" in eng_reasons
            fails_reason_match = (exp_has_fails == eng_has_fails)

            both_reasons_match = gpa_reason_match and fails_reason_match
            reason_checks.append({
                "student_id": s_id,
                "semester_id": sem_id,
                "gpa_reason_match": gpa_reason_match,
                "fails_reason_match": fails_reason_match,
                "full_match": both_reasons_match,
                "expected": exp_reasons,
                "engine": eng_reasons,
            })

    # 7. Per-semester summary tabulation
    df_res = pd.DataFrame(results)
    summary_rows = []

    for sem_id in sorted(df_res["semester_id"].unique()):
        sem_df = df_res[df_res["semester_id"] == sem_id]
        total_sem_records = len(sem_df)
        sem_exp_flagged = int(sem_df["expected_flagged"].sum())
        sem_eng_flagged = int(sem_df["engine_flagged"].sum())
        sem_mismatches = int((~sem_df["match"]).sum())

        summary_rows.append({
            "Semester": f"Semester {sem_id}",
            "Records": total_sem_records,
            "Expected Flagged": sem_exp_flagged,
            "Engine Flagged": sem_eng_flagged,
            "Mismatches": sem_mismatches,
            "Accuracy": f"{((total_sem_records - sem_mismatches) / total_sem_records) * 100:.2f}%",
        })

    # Total row
    tot_rec = len(df_res)
    tot_exp = int(df_res["expected_flagged"].sum())
    tot_eng = int(df_res["engine_flagged"].sum())
    tot_mis = len(mismatches)
    tot_acc = f"{((tot_rec - tot_mis) / tot_rec) * 100:.2f}%"

    summary_rows.append({
        "Semester": "TOTAL",
        "Records": tot_rec,
        "Expected Flagged": tot_exp,
        "Engine Flagged": tot_eng,
        "Mismatches": tot_mis,
        "Accuracy": tot_acc,
    })

    df_summary = pd.DataFrame(summary_rows)

    print("\n" + "=" * 80)
    print("📊 PER-SEMESTER VALIDATION SUMMARY (Table 4.5)")
    print("=" * 80)
    print(df_summary.to_string(index=False))

    # 8. Report mismatches (if any)
    print("\n" + "=" * 80)
    print("🔍 CLASSIFICATION MISMATCH DETAILS")
    print("=" * 80)
    if mismatches:
        print(f"⚠️ Found {len(mismatches)} mismatch(es):")
        df_mis = pd.DataFrame(mismatches)
        cols_to_show = [
            "student_id",
            "semester_id",
            "gpa",
            "failed_courses",
            "expected_flagged",
            "engine_flagged",
            "expected_reasons",
        ]
        print(df_mis[cols_to_show].to_string(index=False))
    else:
        print("✅ PERFECT MATCH: 0 classification mismatches across all 349 records!")

    # 9. Reasons agreement report
    print("\n" + "=" * 80)
    print("📝 REASONS AGREEMENT ANALYSIS (For Flagged Students)")
    print("=" * 80)
    if reason_checks:
        total_flagged_cases = len(reason_checks)
        gpa_matches = sum(1 for r in reason_checks if r["gpa_reason_match"])
        fails_matches = sum(1 for r in reason_checks if r["fails_reason_match"])
        full_matches = sum(1 for r in reason_checks if r["full_match"])

        print(f"Total agreed flagged cases analyzed: {total_flagged_cases}")
        print(f"  • GPA Reason Agreement:           {gpa_matches}/{total_flagged_cases} ({gpa_matches / total_flagged_cases * 100:.1f}%)")
        print(f"  • Failed Courses Reason Agreement:{fails_matches}/{total_flagged_cases} ({fails_matches / total_flagged_cases * 100:.1f}%)")
        print(f"  • Full Syntactic Reason Match:    {full_matches}/{total_flagged_cases} ({full_matches / total_flagged_cases * 100:.1f}%)")

        if full_matches < total_flagged_cases:
            print("\nReason discrepancies:")
            for r in reason_checks:
                if not r["full_match"]:
                    print(f"  Student {r['student_id']} (Sem {r['semester_id']}):")
                    print(f"     Expected: '{r['expected']}'")
                    print(f"     Engine:   '{r['engine']}'")
    else:
        print("No flagged cases found.")

    print("\n" + "=" * 80)
    print(f"Validation finished. Console output saved to: {os.path.abspath(args.output)}")
    print("=" * 80)

    db.close()
    tee.close()
    sys.stdout = tee.terminal


if __name__ == "__main__":
    main()

"""
Seed script — populate the database with realistic demo data.

If backend/dataset/csv/ is present, loads the full 143-student, 40-course,
2,460-enrollment dataset. Otherwise, falls back to the compact mock dataset.

Run from backend/:
    python scripts/seed.py
"""
import csv
import os
import sys
from datetime import date, datetime

# Allow importing the app from scripts/ folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.security import hash_password
from app.database import SessionLocal, engine, Base
import app.models  # Ensure all models are registered
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User, UserRole
from app.services.gpa import score_to_grade

DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "csv")


def _uid_to_int(uid: str | None) -> int | None:
    if not uid or not str(uid).strip():
        return None
    cleaned = str(uid).strip()
    if cleaned.startswith("U"):
        return int(cleaned[1:])
    return int(cleaned)


def _seed_from_csv(db):
    print(f"📂 Loading dataset from {os.path.abspath(DATASET_DIR)} ...")

    # 1. Users
    users_csv = os.path.join(DATASET_DIR, "users.csv")
    with open(users_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            uid = _uid_to_int(r["user_id"])
            pwd = r.get("dev_password", "Password@123")
            u = User(
                id=uid,
                name=r["name"].strip(),
                email=r["email"].strip().lower(),
                password_hash=hash_password(pwd),
                role=UserRole(r["role"].strip().lower()),
            )
            db.merge(u)
    db.commit()
    print("  ✓ Users loaded (14)")

    # 2. Semesters
    sem_csv = os.path.join(DATASET_DIR, "semesters.csv")
    with open(sem_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            s_date = datetime.strptime(r["start_date"].strip(), "%Y-%m-%d").date() if r.get("start_date") else None
            e_date = datetime.strptime(r["end_date"].strip(), "%Y-%m-%d").date() if r.get("end_date") else None
            is_curr = bool(int(r.get("is_current", 0)))
            s = Semester(
                id=int(r["semester_id"]),
                session=r["session"].strip(),
                name=r["name"].strip(),
                start_date=s_date,
                end_date=e_date,
                is_current=is_curr,
            )
            db.merge(s)
    db.commit()
    print("  ✓ Semesters loaded (4)")

    # 3. Courses
    courses_csv = os.path.join(DATASET_DIR, "courses.csv")
    with open(courses_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            c = Course(
                id=int(r["course_id"]),
                code=r["code"].strip(),
                title=r["title"].strip(),
                credit_units=int(r["credit_units"]),
                level=int(r["level"]),
                lecturer_id=_uid_to_int(r.get("lecturer_id")),
            )
            db.merge(c)
    db.commit()
    print("  ✓ Courses loaded (40)")

    # 4. Students
    students_csv = os.path.join(DATASET_DIR, "students.csv")
    with open(students_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            st = Student(
                id=int(r["student_id"]),
                matric_no=r["matric_no"].strip(),
                name=r["name"].strip(),
                level=int(r["level"]),
                email=r.get("email", "").strip().lower(),
                advisor_id=_uid_to_int(r.get("advisor_id")),
            )
            db.merge(st)
    db.commit()
    print("  ✓ Students loaded (143)")

    # 5. Enrollments
    enroll_csv = os.path.join(DATASET_DIR, "enrollments.csv")
    with open(enroll_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        enrollments = []
        for r in reader:
            score_val = r.get("score")
            score = float(score_val) if score_val and str(score_val).strip() else None
            grade = r.get("grade") if r.get("grade") and str(r.get("grade")).strip() else None
            gp_val = r.get("grade_point")
            gp = float(gp_val) if gp_val and str(gp_val).strip() else None

            if score is not None and (grade is None or gp is None):
                grade, gp = score_to_grade(score)

            enrollments.append(
                Enrollment(
                    id=int(r["enrollment_id"]),
                    student_id=int(r["student_id"]),
                    course_id=int(r["course_id"]),
                    semester_id=int(r["semester_id"]),
                    score=score,
                    grade=grade,
                    grade_point=gp,
                )
            )

        db.bulk_save_objects(enrollments)
    db.commit()
    print(f"  ✓ Enrollments loaded ({len(enrollments):,})")

    print("\n✅ Dataset seed completed successfully!")
    print("\nAdmin Logins (password: Admin@123):")
    print("  - Dr. A. Dike (HOD): adike@example.com")
    print("  - Prof. M. Abdullahi: mabdullahi@example.com")
    print("Lecturer Logins (password: Lecturer@123):")
    print("  - Dr. B. Yakubu: yakubu5@example.com")
    print("  - Mr. T. Ogunleye: ogunleye6@example.com")


def seed():
    # Ensure all tables exist in the database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("⚠ Database already contains data — skipping seed.")
            print("  To re-seed fresh, truncate or drop the tables first.")
            return

        if os.path.exists(DATASET_DIR):
            _seed_from_csv(db)
        else:
            print(f"Dataset directory not found at {DATASET_DIR}. Please ensure dataset/csv/ exists.")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

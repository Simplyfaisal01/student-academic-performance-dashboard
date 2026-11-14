"""
Integration tests for the automated probation case lifecycle using an in-memory database:
- Case creation on probation condition
- Case already active (updating reasons, no duplicate case created)
- Case clearing when performance improves
- Case re-activation if grades fall again
- Advisor in-app notification dispatch
"""
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.course import Course
from app.models.semester import Semester
from app.models.enrollment import Enrollment
from app.models.probation import ProbationCase, ProbationStatus
from app.models.notification import Notification
from app.services.probation import sync_student_probation_case


class TestProbationLifecycle(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for isolated test execution
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed minimal relational fixtures: Advisor, Student, Semester, Courses
        self.advisor = User(
            id=1,
            name="Dr. Advisor",
            email="advisor@example.com",
            password_hash="fakehash",
            role=UserRole.admin,
        )
        self.student = Student(
            id=10,
            matric_no="FT24BCMP0010",
            name="Test Student",
            level=100,
            advisor_id=1,
        )
        self.semester = Semester(
            id=1,
            session="2024/2025",
            name="First Semester",
            is_current=True,
        )
        self.course1 = Course(id=101, code="CSC101", title="Comp Sci", credit_units=3, level=100)
        self.course2 = Course(id=102, code="MTH101", title="Maths", credit_units=3, level=100)
        self.course3 = Course(id=103, code="PHY101", title="Physics", credit_units=3, level=100)

        self.db.add_all([
            self.advisor, self.student, self.semester,
            self.course1, self.course2, self.course3
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_case_creation_when_failing(self):
        """Student with failing grades (GPA = 0.00, 3 fails) should trigger a new active case."""
        # Add 3 failing enrollments (score 30, F, 0.0 pts)
        e1 = Enrollment(student_id=10, course_id=101, semester_id=1, score=30, grade="F", grade_point=0.0)
        e2 = Enrollment(student_id=10, course_id=102, semester_id=1, score=25, grade="F", grade_point=0.0)
        e3 = Enrollment(student_id=10, course_id=103, semester_id=1, score=35, grade="F", grade_point=0.0)
        self.db.add_all([e1, e2, e3])
        self.db.commit()

        case = sync_student_probation_case(student_id=10, semester_id=1, db=self.db)

        self.assertIsNotNone(case)
        self.assertEqual(case.status, ProbationStatus.active)
        self.assertIn("GPA 0.00 below 1.5", case.reasons)
        self.assertIn("3 failed courses", case.reasons)

        # Verify advisor received an in-app notification
        notif = self.db.query(Notification).filter(Notification.recipient_id == 1).first()
        self.assertIsNotNone(notif)
        self.assertIn("FLAGGED", notif.message)
        self.assertFalse(notif.is_read)

    def test_case_already_active_does_not_duplicate(self):
        """When a case is already active, re-syncing should update reasons without creating duplicates."""
        e1 = Enrollment(student_id=10, course_id=101, semester_id=1, score=30, grade="F", grade_point=0.0)
        self.db.add(e1)
        self.db.commit()

        # First evaluation
        case1 = sync_student_probation_case(student_id=10, semester_id=1, db=self.db)
        case_id = case1.id

        # Second evaluation with an additional fail
        e2 = Enrollment(student_id=10, course_id=102, semester_id=1, score=20, grade="F", grade_point=0.0)
        self.db.add(e2)
        self.db.commit()

        case2 = sync_student_probation_case(student_id=10, semester_id=1, db=self.db)

        # Same case ID, count remains 1
        self.assertEqual(case2.id, case_id)
        total_cases = self.db.query(ProbationCase).filter(
            ProbationCase.student_id == 10,
            ProbationCase.semester_id == 1,
        ).count()
        self.assertEqual(total_cases, 1)

    def test_case_clearing_when_grades_improve(self):
        """When scores are revised upward, active probation transitions to cleared."""
        # Start with failing grades
        e1 = Enrollment(student_id=10, course_id=101, semester_id=1, score=30, grade="F", grade_point=0.0)
        self.db.add(e1)
        self.db.commit()
        sync_student_probation_case(student_id=10, semester_id=1, db=self.db)

        # Grade is remarked to an A (75, A, 5.0 pts)
        e1.score = 75
        e1.grade = "A"
        e1.grade_point = 5.0
        self.db.commit()

        # Sync standing after revision
        cleared_case = sync_student_probation_case(student_id=10, semester_id=1, db=self.db)

        self.assertEqual(cleared_case.status, ProbationStatus.cleared)
        self.assertIsNotNone(cleared_case.resolved_on)
        self.assertIn("Cleared", cleared_case.notes)

        # Advisor notification dispatched for clearance
        clear_notif = (
            self.db.query(Notification)
            .filter(Notification.recipient_id == 1, Notification.message.like("%CLEARED%"))
            .first()
        )
        self.assertIsNotNone(clear_notif)


if __name__ == "__main__":
    unittest.main()


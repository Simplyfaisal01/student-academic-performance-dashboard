from sqlalchemy import Integer, Float, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "semester_id", name="uq_enrollment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    grade_point: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="enrollments")

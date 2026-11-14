import enum
from datetime import datetime
from sqlalchemy import String, Enum, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProbationStatus(str, enum.Enum):
    active = "active"
    reviewing = "reviewing"
    cleared = "cleared"


class ProbationCase(Base):
    __tablename__ = "probation_cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    reasons: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProbationStatus] = mapped_column(
        Enum(ProbationStatus), nullable=False, default=ProbationStatus.active
    )
    flagged_on: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    resolved_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="probation_cases")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="probation_cases")
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="probation_case"
    )

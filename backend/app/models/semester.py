from datetime import date
from sqlalchemy import String, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session: Mapped[str] = mapped_column(String(20), nullable=False)   # e.g. "2024/2025"
    name: Mapped[str] = mapped_column(String(30), nullable=False)      # "First" / "Second"
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="semester")
    probation_cases: Mapped[list["ProbationCase"]] = relationship(
        "ProbationCase", back_populates="semester"
    )

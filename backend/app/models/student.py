from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    matric_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)   # e.g. 100, 200 …
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    advisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    advisor: Mapped["User"] = relationship("User", back_populates="advisees")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="student")
    probation_cases: Mapped[list["ProbationCase"]] = relationship(
        "ProbationCase", back_populates="student"
    )

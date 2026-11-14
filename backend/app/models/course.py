from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_units: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    level: Mapped[int] = mapped_column(Integer, nullable=False)   # 100 / 200 / …
    lecturer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    lecturer: Mapped["User"] = relationship("User", back_populates="courses")
    enrollments: Mapped[list["Enrollment"]] = relationship("Enrollment", back_populates="course")

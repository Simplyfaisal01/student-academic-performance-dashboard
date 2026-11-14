from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    probation_case_id: Mapped[int] = mapped_column(
        ForeignKey("probation_cases.id"), nullable=False
    )
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    probation_case: Mapped["ProbationCase"] = relationship(
        "ProbationCase", back_populates="notifications"
    )
    recipient: Mapped["User"] = relationship("User", back_populates="notifications")

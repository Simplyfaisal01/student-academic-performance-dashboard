from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    probation_case_id: int
    recipient_id: int
    message: str
    is_read: bool
    sent_at: datetime

    model_config = {"from_attributes": True}


class NotificationStatusUpdate(BaseModel):
    is_read: bool = True


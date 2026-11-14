from datetime import datetime
from pydantic import BaseModel
from app.models.probation import ProbationStatus


class StudentBrief(BaseModel):
    id: int
    matric_no: str
    name: str
    level: int
    email: str | None = None
    advisor_id: int | None = None

    model_config = {"from_attributes": True}


class SemesterBrief(BaseModel):
    id: int
    session: str
    name: str

    model_config = {"from_attributes": True}


class ProbationCaseBase(BaseModel):
    student_id: int
    semester_id: int
    reasons: str
    status: ProbationStatus = ProbationStatus.active
    notes: str | None = None


class ProbationCaseUpdate(BaseModel):
    status: ProbationStatus | None = None
    notes: str | None = None


class ProbationCaseOut(ProbationCaseBase):
    id: int
    flagged_on: datetime
    resolved_on: datetime | None = None
    student: StudentBrief | None = None
    semester: SemesterBrief | None = None

    model_config = {"from_attributes": True}


from datetime import date
from pydantic import BaseModel


class SemesterBase(BaseModel):
    session: str          # e.g. "2024/2025"
    name: str             # "First" | "Second"
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(BaseModel):
    session: str | None = None
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class SemesterOut(SemesterBase):
    id: int

    model_config = {"from_attributes": True}


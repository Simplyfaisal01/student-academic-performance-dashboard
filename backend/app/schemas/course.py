from pydantic import BaseModel
from app.schemas.user import UserOut


class CourseBase(BaseModel):
    code: str
    title: str
    credit_units: int = 3
    level: int
    lecturer_id: int | None = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    code: str | None = None
    title: str | None = None
    credit_units: int | None = None
    level: int | None = None
    lecturer_id: int | None = None


class CourseOut(CourseBase):
    id: int
    lecturer: UserOut | None = None

    model_config = {"from_attributes": True}


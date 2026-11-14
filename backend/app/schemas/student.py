from pydantic import BaseModel, EmailStr
from app.schemas.user import UserOut


class StudentBase(BaseModel):
    matric_no: str
    name: str
    level: int
    email: EmailStr | None = None
    advisor_id: int | None = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: str | None = None
    level: int | None = None
    email: EmailStr | None = None
    advisor_id: int | None = None


class StudentOut(StudentBase):
    id: int
    advisor: UserOut | None = None

    model_config = {"from_attributes": True}


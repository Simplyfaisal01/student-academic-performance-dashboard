"""
Pydantic schemas for User.

Schemas are the shapes of data entering and leaving the API.
They are separate from ORM models on purpose: the ORM talks to the DB,
the schema talks to the client.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    """Used when an admin creates a new user — includes plain-text password."""
    password: str


class UserUpdate(BaseModel):
    """All fields optional so the caller can patch just what changed."""
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: UserRole | None = None


class UserOut(UserBase):
    """Shape returned to the client — never includes the password hash."""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}  # allow ORM → schema conversion


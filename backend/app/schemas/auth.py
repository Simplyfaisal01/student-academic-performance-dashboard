"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel
from app.schemas.user import UserOut


class Token(BaseModel):
    """Returned on successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    """
    We accept JSON body login (not OAuth2 form) so the React frontend
    can POST application/json.  The /docs 'Authorize' button still works
    via the separate OAuth2PasswordBearer scheme pointing at /auth/login.
    """
    email: str
    password: str


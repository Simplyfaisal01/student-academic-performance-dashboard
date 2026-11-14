"""
Auth router — login only.
Kept intentionally thin: all logic lives in security.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


def _authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, else None."""
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Exchange email + password for a JWT access token.
    The token must be sent as 'Authorization: Bearer <token>' on every
    subsequent request.
    """
    user = _authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(access_token=token, user=UserOut.model_validate(user))


# Swagger 'Authorize' button sends an OAuth2 form; we handle that too.
@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Hidden endpoint used only by Swagger UI's Authorize button."""
    user = _authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently logged-in user."""
    return current_user


"""
Central settings — every threshold and configurable value lives here.
Change these without touching business logic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Tuple


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    PROJECT_NAME: str = "Student Performance Dashboard"
    API_V1_STR: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/student_dashboard"

    # ── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_ENABLED: bool = False

    # ── Grading scale  ───────────────────────────────────────────────────────
    # Each entry: (min_score_inclusive, grade_letter, grade_point)
    GRADE_SCALE: list[tuple[int, str, float]] = [
        (70, "A", 5.0),
        (60, "B", 4.0),
        (50, "C", 3.0),
        (45, "D", 2.0),
        (40, "E", 1.0),
        (0,  "F", 0.0),
    ]
    PASS_MARK: int = 40  # scores below this are F

    # ── Probation thresholds ─────────────────────────────────────────────────
    PROBATION_MIN_GPA: float = 1.5          # GPA strictly below this triggers
    PROBATION_MAX_FAILED_COURSES: int = 2   # more than N failed courses triggers

    # ── Report dir ───────────────────────────────────────────────────────────
    REPORTS_DIR: str = "reports"


settings = Settings()

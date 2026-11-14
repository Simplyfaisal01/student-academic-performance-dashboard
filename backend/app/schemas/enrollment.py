from pydantic import BaseModel, Field


# ── Minimal nested views (avoid circular imports) ───────────────────────────

class _StudentBrief(BaseModel):
    id: int
    matric_no: str
    name: str
    level: int
    model_config = {"from_attributes": True}


class _CourseBrief(BaseModel):
    id: int
    code: str
    title: str
    credit_units: int
    model_config = {"from_attributes": True}


class _SemesterBrief(BaseModel):
    id: int
    session: str
    name: str
    model_config = {"from_attributes": True}


# ── Main schemas ─────────────────────────────────────────────────────────────

class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    semester_id: int


class GradeEntry(BaseModel):
    """Body for submitting / updating a single grade."""
    score: float = Field(ge=0, le=100)


class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    semester_id: int
    score: float | None = None
    grade: str | None = None
    grade_point: float | None = None
    student: _StudentBrief | None = None
    course: _CourseBrief | None = None
    semester: _SemesterBrief | None = None

    model_config = {"from_attributes": True}


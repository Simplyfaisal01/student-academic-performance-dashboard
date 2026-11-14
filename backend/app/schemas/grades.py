from pydantic import BaseModel


class GradeImportRow(BaseModel):
    """A single successfully-imported grade row."""
    row: int
    matric_no: str
    name: str | None = None
    score: float
    grade: str
    grade_point: float
    note: str | None = None   # populated in dry-run mode


class GradeImportError(BaseModel):
    """A row that failed validation."""
    row: int
    matric_no: str
    error: str


class GradeImportResult(BaseModel):
    """Full response returned by the CSV upload endpoint."""
    total_rows: int
    saved_count: int
    error_count: int
    saved: list[GradeImportRow]
    errors: list[GradeImportError]


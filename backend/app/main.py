"""
Application entry point. Register all routers here.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    analytics,
    auth,
    courses,
    enrollments,
    grades,
    notifications,
    probation,
    reports,
    semesters,
    students,
    users,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

# Allow the Vite dev server and deployed frontend domains to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_STR
app.include_router(auth.router,          prefix=PREFIX)
app.include_router(users.router,         prefix=PREFIX)
app.include_router(students.router,      prefix=PREFIX)
app.include_router(courses.router,       prefix=PREFIX)
app.include_router(semesters.router,     prefix=PREFIX)
app.include_router(enrollments.router,   prefix=PREFIX)
app.include_router(grades.router,        prefix=PREFIX)
app.include_router(probation.router,     prefix=PREFIX)
app.include_router(notifications.router, prefix=PREFIX)
app.include_router(analytics.router,     prefix=PREFIX)
app.include_router(reports.router,       prefix=PREFIX)


@app.get("/health")
def health_check():
    """Quick liveness probe — useful for testing the server is up."""
    return {"status": "ok", "project": settings.PROJECT_NAME}

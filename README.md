# Student Academic Performance Dashboard & Automated Probation Monitoring System

A centralized academic monitoring portal designed for universities. The system aggregates grades, automatically computes semester and cumulative GPA on a 5-point scale, proactively detects academic probation and at-risk standing, alerts academic advisors, and visualizes institutional trends through interactive dashboards and reports.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | ≥ 3.11 (tested on 3.12) | Backend API, GPA engine, ReportLab PDF generation |
| **MySQL** | ≥ 8.0 | Primary relational database |
| **Node.js** | ≥ 18 | Vite React frontend environment |
| **npm** | latest | Package manager |

---

## Quick Start Guide

### 1. Backend Setup & Database Migration

```powershell
cd backend

# Create virtual environment (Python 3.12 recommended)
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env     # Windows
# cp .env.example .env     # macOS/Linux
# Edit .env with your MySQL credentials
```

Create the MySQL database:
```sql
CREATE DATABASE student_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run schema migrations:
```powershell
alembic upgrade head
```

Seed the official dataset (143 students, 40 courses, 4 semesters, 2,460 enrollments):
```powershell
python scripts/seed.py
```

Start the FastAPI backend server:
```powershell
uvicorn app.main:app --reload
# Interactive API documentation: http://localhost:8000/api/v1/docs
```

---

### 2. Frontend Setup (React + Vite)

In a separate terminal:
```powershell
cd frontend
npm install
npm run dev
# Dashboard Portal: http://localhost:5173
```

---

## Demo Credentials (from Dataset)

| Role | Name | Email | Password |
|------|------|-------|----------|
| **Admin (HOD)** | Dr. A. Dike | `adike@example.com` | `Admin@123` |
| **Admin (Exam Officer)** | Prof. M. Abdullahi | `mabdullahi@example.com` | `Admin@123` |
| **Lecturer** | Dr. B. Yakubu | `yakubu5@example.com` | `Lecturer@123` |
| **Lecturer** | Mr. T. Ogunleye | `ogunleye6@example.com` | `Lecturer@123` |

---

## Running the Automated Test Suite (Phase 9)

Run the comprehensive pytest suite covering GPA calculations, edge cases, lifecycle state transitions, and dataset oracle validation:

```powershell
cd backend
.\.venv\Scripts\pytest tests/ -v
```

All 31 test cases verify:
* Exact grade boundary thresholds (70, 69.9, 60, 59.9, 50, 49.9, 45, 44.9, 40, 39.9, 0).
* Zero credit units (division-by-zero prevention).
* All failing scores ($0.00$ GPA).
* Probation triggers ($GPA < 1.50$ and $> 2$ failed courses).
* 100% agreement with the 349-case dataset oracle (`expected_probation_results.csv`).
* Automated case lifecycle transitions (`active` $\rightarrow$ `cleared` $\rightarrow$ re-flagged).
* CSV bulk grade upload validation (duplicate detection, range checking, unknown students).

---

## Configurable Grading Scale (`app/core/config.py`)

| Score Range | Letter Grade | Grade Points | Standing |
|---|---|---|---|
| **70 – 100** | A | 5.0 | Excellent |
| **60 – 69** | B | 4.0 | Very Good |
| **50 – 59** | C | 3.0 | Good |
| **45 – 49** | D | 2.0 | Fair |
| **40 – 44** | E | 1.0 | Pass |
| **0 – 39** | F | 0.0 | Fail |

* **Pass Mark:** 40
* **Probation Triggers:** Semester GPA $< 1.50$ **OR** more than $2$ failed courses in a semester.
* All thresholds are configurable in `backend/app/core/config.py` and via the frontend **Settings** interface.

---

## Project Structure

```
student_performance_dashboard/
├── backend/
│   ├── alembic/                # Alembic migration scripts
│   ├── app/
│   │   ├── core/               # Central settings & security (JWT, bcrypt)
│   │   ├── models/             # SQLAlchemy ORM declarative models
│   │   ├── routers/            # FastAPI route handlers (thin)
│   │   ├── schemas/            # Pydantic request and response models
│   │   └── services/           # Pure business logic (GPA, probation, reports, CSV)
│   ├── dataset/                # Official dataset CSV files & test oracle
│   ├── scripts/                # Database seeding script & sample upload files
│   ├── tests/                  # Pytest automated test suite (31 tests)
│   ├── .env.example            # Environment variables template
│   └── requirements.txt        # Python backend dependencies
└── frontend/                   # React 18 + Vite frontend
    ├── public/data/            # CSV dataset mirror for browser ingestion
    └── src/
        ├── components/         # Reusable UI cards, tables, modals, badges, layout
        ├── context/            # Authentication & Reactive Dataset Providers
        ├── pages/              # Overview, Students, Records, Probation, Analytics, Reports, Users, Settings
        └── services/           # Axios HTTP client, PapaParse loader, Probation Engine
```

"""
Synthetic dataset generator (NO-ATTENDANCE VARIANT) for the Student Academic
Performance Dashboard with Automated Probation Monitoring System.

Same students, courses and grades as the full dataset, but no attendance file and
probation rules use GPA and failed courses only.

Everything here is FICTIONAL. Names, matric numbers and emails are generated.
Run:  python generate_dataset.py
Change SEED to get a different but reproducible dataset.
Change SESSION_* constants if your report uses different academic sessions.
"""
import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

SEED = 2025
random.seed(SEED)
np.random.seed(SEED)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- settings --
# 5-point scale (adjust to match your school's regulation)
GRADE_SCALE = [(70, "A", 5), (60, "B", 4), (50, "C", 3), (45, "D", 2), (40, "E", 1), (0, "F", 0)]
PASS_MARK = 40
PROB_GPA = 1.5          # GPA below this -> probation
PROB_FAILS = 2          # MORE than this many failed courses -> probation
LECTURES_PER_COURSE = 10

# (session, name, start, end, is_current)
SEMESTERS = [
    ("2023/2024", "First Semester", date(2023, 10, 2), date(2024, 2, 9), 0),
    ("2023/2024", "Second Semester", date(2024, 3, 4), date(2024, 7, 12), 0),
    ("2024/2025", "First Semester", date(2024, 10, 7), date(2025, 2, 14), 0),
    ("2024/2025", "Second Semester", date(2025, 3, 10), date(2025, 7, 18), 1),
]
# students per entry year -> how many semesters they have in the dataset
# entry year 2021 = 400L now, 2022 = 300L, 2023 = 200L, 2024 = 100L
COHORTS = {2021: 30, 2022: 35, 2023: 38, 2024: 40}
CURRENT_START_YEAR = 2024  # 2024/2025 session


def level_in_session(entry_year, session_start_year):
    return (session_start_year - entry_year + 1) * 100


# ------------------------------------------------------------------ names --
FIRST = ["Abubakar", "Aisha", "Amina", "Chidi", "Chinedu", "Emeka", "Ngozi", "Funmi", "Tunde", "Kemi",
         "Ibrahim", "Fatima", "Musa", "Zainab", "Yusuf", "Hauwa", "Sani", "Maryam", "Usman", "Khadija",
         "Obinna", "Chioma", "Ifeanyi", "Adaeze", "Emmanuel", "Blessing", "Samuel", "Grace", "Daniel", "Esther",
         "David", "Ruth", "Joseph", "Mercy", "Peter", "Patience", "Ahmed", "Halima", "Bashir", "Rukayya",
         "Segun", "Folake", "Bayo", "Yetunde", "Ayo", "Damilola", "Tobi", "Sade", "Uche", "Nneka",
         "Danjuma", "Salamatu", "Ishaya", "Rahila", "Monday", "Victoria", "Joshua", "Hannah", "Kabiru", "Binta"]
LAST = ["Okafor", "Bello", "Adeyemi", "Eze", "Nwosu", "Adegoke", "Okwu", "Salako", "Abdullahi", "Garba",
        "Danladi", "Yakubu", "Suleiman", "Lawal", "Ogunleye", "Balogun", "Ibrahim", "Mohammed", "Okoro", "Nnamdi",
        "Chukwu", "Onyeka", "Igwe", "Ojo", "Akinola", "Adebayo", "Umar", "Tanko", "Audu", "Gimba",
        "Ayuba", "Dogara", "Ishaku", "Iliya", "Jatau", "Kwasau", "Maikudi", "Ngbede", "Obi", "Okeke",
        "Oladipo", "Olawale", "Sambo", "Shehu", "Tijani", "Usman", "Wada", "Yahaya", "Zubairu", "Amadi"]

# ---------------------------------------------------------------- courses --
# (code, title, credit_units, level, semester_name)
F, S = "First Semester", "Second Semester"
COURSES = [
    ("CSC101", "Introduction to Computer Science", 3, 100, F),
    ("CSC103", "Programming Fundamentals", 3, 100, F),
    ("MTH101", "General Mathematics I", 3, 100, F),
    ("PHY101", "General Physics I", 3, 100, F),
    ("GST101", "Use of English I", 2, 100, F),
    ("CSC102", "Computer Applications", 3, 100, S),
    ("CSC104", "Introduction to Problem Solving", 3, 100, S),
    ("MTH102", "General Mathematics II", 3, 100, S),
    ("PHY102", "General Physics II", 3, 100, S),
    ("GST102", "Logic and Philosophy", 2, 100, S),
    ("CSC201", "Computer Programming I", 3, 200, F),
    ("CSC203", "Discrete Mathematics", 3, 200, F),
    ("CSC205", "Digital Logic Design", 3, 200, F),
    ("MTH201", "Linear Algebra", 3, 200, F),
    ("STA201", "Statistics for Computing", 2, 200, F),
    ("CSC202", "Computer Programming II", 3, 200, S),
    ("CSC204", "Computer Architecture", 3, 200, S),
    ("CSC206", "Introduction to Databases", 3, 200, S),
    ("MTH202", "Numerical Methods", 3, 200, S),
    ("GST201", "Entrepreneurship Studies", 2, 200, S),
    ("CSC301", "Data Structures and Algorithms", 3, 300, F),
    ("CSC303", "Operating Systems", 3, 300, F),
    ("CSC305", "Database Management Systems", 3, 300, F),
    ("CSC307", "Object-Oriented Programming", 3, 300, F),
    ("CSC309", "Computer Networks", 2, 300, F),
    ("CSC302", "Software Engineering", 3, 300, S),
    ("CSC304", "Theory of Computation", 3, 300, S),
    ("CSC306", "Web Application Development", 3, 300, S),
    ("CSC308", "Algorithm Analysis", 3, 300, S),
    ("CSC310", "Systems Analysis and Design", 2, 300, S),
    ("CSC401", "Artificial Intelligence", 3, 400, F),
    ("CSC403", "Compiler Construction", 3, 400, F),
    ("CSC405", "Computer Security", 3, 400, F),
    ("CSC407", "Research Methodology", 2, 400, F),
    ("CSC409", "Mobile Application Development", 3, 400, F),
    ("CSC402", "Machine Learning", 3, 400, S),
    ("CSC404", "Distributed Systems", 3, 400, S),
    ("CSC406", "Cloud Computing", 3, 400, S),
    ("CSC408", "Professional Ethics in Computing", 2, 400, S),
    ("CSC499", "Final Year Project", 6, 400, S),
]
# course difficulty offset (negative = harder)
HARD = {"MTH101": -5, "MTH102": -5, "PHY101": -4, "PHY102": -4, "CSC203": -4, "MTH201": -5, "CSC301": -6,
        "CSC303": -3, "CSC304": -4, "CSC308": -3, "CSC403": -4, "CSC201": -2, "CSC205": -3, "CSC401": -2,
        "GST101": 4, "GST102": 4, "GST201": 5, "CSC408": 4, "CSC407": 3, "CSC499": 5, "CSC310": 2}


def grade_for(score):
    for floor, letter, point in GRADE_SCALE:
        if score >= floor:
            return letter, point
    return "F", 0


# ------------------------------------------------------------------ users --
users = [
    ("U001", "Dr. A. Dike", "adike@example.com", "admin", "Admin@123"),  # HOD
    ("U002", "Prof. M. Abdullahi", "mabdullahi@example.com", "admin", "Admin@123"),
    ("U003", "Dr. S. Okonkwo", "sokonkwo@example.com", "admin", "Admin@123"),
    ("U004", "Dr. H. Garba", "hgarba@example.com", "admin", "Admin@123"),
]
lect_names = ["Dr. B. Yakubu", "Mr. T. Ogunleye", "Mrs. C. Nwankwo", "Dr. J. Danladi", "Mr. K. Lawal",
              "Dr. R. Adeniyi", "Mrs. F. Suleiman", "Mr. P. Okeke", "Dr. N. Tanko", "Mr. D. Audu"]
for i, n in enumerate(lect_names, start=5):
    users.append((f"U{i:03d}", n, n.split()[-1].lower() + f"{i}@example.com", "lecturer", "Lecturer@123"))
users_df = pd.DataFrame(users, columns=["user_id", "name", "email", "role", "dev_password"])
advisor_ids = ["U002", "U003", "U004"]
lecturer_ids = [u[0] for u in users if u[3] == "lecturer"]

# ---------------------------------------------------------------- courses --
courses_rows = []
for idx, (code, title, cu, lvl, sem) in enumerate(COURSES, start=1):
    courses_rows.append((idx, code, title, cu, lvl, sem, random.choice(lecturer_ids)))
courses_df = pd.DataFrame(courses_rows, columns=["course_id", "code", "title", "credit_units", "level",
                                                 "semester_name", "lecturer_id"])

semesters_df = pd.DataFrame(
    [(i + 1, s, n, st.isoformat(), en.isoformat(), cur) for i, (s, n, st, en, cur) in enumerate(SEMESTERS)],
    columns=["semester_id", "session", "name", "start_date", "end_date", "is_current"])

# --------------------------------------------------------------- students --
students = []
sid = 1
used = set()
for entry, count in COHORTS.items():
    for n in range(1, count + 1):
        while True:
            full = f"{random.choice(FIRST)} {random.choice(LAST)}"
            if full not in used:
                used.add(full)
                break
        matric = f"FT{str(entry)[2:]}BCMP{sid:04d}"
        # hidden traits (NOT exported): ability and attendance propensity
        ability = np.random.normal(0, 1)
        r = random.random()
        if r < 0.07:          # struggling group -> most probation cases
            ability = np.random.normal(-2.4, 0.35)
        elif r < 0.17:        # at-risk borderline group
            ability = np.random.normal(-1.3, 0.35)
        att_rate = float(np.clip(0.80 + 0.07 * ability + np.random.normal(0, 0.09), 0.30, 0.99))
        students.append(dict(student_id=sid, matric_no=matric, name=full,
                             email=full.lower().replace(" ", ".") + f"{sid}@example.com",
                             entry_year=entry, advisor_id=random.choice(advisor_ids),
                             _ability=ability, _att=att_rate))
        sid += 1

# ------------------------------------------- enrollments + attendance rows --
enroll_rows, att_rows = [], []
eid, aid = 1, 1
course_by = {(c[3], c[4]): [] for c in COURSES}
for row in courses_df.itertuples():
    course_by[(row.level, row.semester_name)].append(row)

for sem_idx, (session, sname, start, end, is_cur) in enumerate(SEMESTERS, start=1):
    start_year = int(session[:4])
    for s in students:
        lvl = level_in_session(s["entry_year"], start_year)
        if lvl < 100 or lvl > 400:
            continue
        courses_here = course_by[(lvl, sname)]
        # small per-semester wobble in performance
        wobble = np.random.normal(0, 0.25)
        for c in courses_here:
            score = None
            grade = None
            gp = None
            if not is_cur:
                raw = 62 + 9 * (s["_ability"] + wobble) + 0.6 * HARD.get(c.code, 0) + np.random.normal(0, 6.5)
                score = int(round(float(np.clip(raw, 5, 98))))
                grade, gp = grade_for(score)
            enroll_rows.append((eid, s["student_id"], c.course_id, sem_idx, score, grade, gp))
            eid += 1
            # attendance
            n_lect = LECTURES_PER_COURSE if not is_cur else 6
            for k in range(n_lect):
                d = start + timedelta(days=7 * k + random.randint(0, 3))
                p = s["_att"] + np.random.normal(0, 0.04)
                roll = random.random()
                if roll < p - 0.06:
                    status = "present"
                elif roll < p:
                    status = "late"
                else:
                    status = "absent"
                att_rows.append((aid, s["student_id"], c.course_id, sem_idx, d.isoformat(), status))
                aid += 1

students_df = pd.DataFrame([{k: v for k, v in s.items() if not k.startswith("_")} for s in students])
students_df["level"] = students_df["entry_year"].apply(lambda y: level_in_session(y, CURRENT_START_YEAR))
students_df = students_df[["student_id", "matric_no", "name", "email", "level", "entry_year", "advisor_id"]]

enroll_df = pd.DataFrame(enroll_rows, columns=["enrollment_id", "student_id", "course_id", "semester_id",
                                               "score", "grade", "grade_point"])
enroll_df["score"] = enroll_df["score"].astype("Int64")
enroll_df["grade_point"] = enroll_df["grade_point"].astype("Int64")
att_df = pd.DataFrame(att_rows, columns=["attendance_id", "student_id", "course_id", "semester_id",
                                         "date", "status"])

# ----------------------------------------- expected probation outcomes -----
# What the probation engine SHOULD produce for each completed semester.
# Use this to check/unit-test your own implementation.
cu_map = courses_df.set_index("course_id")["credit_units"]
done = enroll_df[enroll_df["score"].notna()].copy()
done["cu"] = done["course_id"].map(cu_map)
done["pts"] = done["grade_point"] * done["cu"]
done["failed"] = (done["score"] < PASS_MARK).astype(int)
agg = done.groupby(["student_id", "semester_id"]).agg(
    pts=("pts", "sum"), cu=("cu", "sum"), fails=("failed", "sum")).reset_index()
agg["gpa"] = (agg["pts"] / agg["cu"]).round(2)

exp = agg.copy()


def reasons(r):
    out = []
    if r.gpa < PROB_GPA:
        out.append(f"GPA {r.gpa:.2f} below {PROB_GPA}")
    if r.fails > PROB_FAILS:
        out.append(f"{int(r.fails)} failed courses")
    return "; ".join(out)


exp["expected_reasons"] = exp.apply(reasons, axis=1)
exp["should_be_flagged"] = (exp["expected_reasons"] != "").astype(int)
exp = exp[["student_id", "semester_id", "gpa", "fails", "should_be_flagged", "expected_reasons"]]
exp = exp.rename(columns={"fails": "failed_courses"})

# ------------------------------------- upload samples for the CSV feature --
# Current semester (id 4), one course taught at 300L: simulate lecturer upload
cur_sem = 4
target_course = courses_df[(courses_df.code == "CSC306")].iloc[0]
rows = enroll_df[(enroll_df.semester_id == cur_sem) & (enroll_df.course_id == target_course.course_id)]
stu_map = students_df.set_index("student_id")
upload_rows = []
for r in rows.itertuples():
    ab = [s for s in students if s["student_id"] == r.student_id][0]["_ability"]
    sc = int(np.clip(round(62 + 9 * ab + np.random.normal(0, 6.5)), 5, 98))
    upload_rows.append((stu_map.loc[r.student_id, "matric_no"], stu_map.loc[r.student_id, "name"], sc))
valid = pd.DataFrame(upload_rows, columns=["matric_no", "name", "score"])
valid.insert(0, "course_code", target_course.code)

bad = valid.copy()
bad["score"] = bad["score"].astype(object)
bad.loc[1, "score"] = 143                    # out of range
bad.loc[3, "score"] = -5                     # negative
bad.loc[5, "matric_no"] = "FT99BCMP9999"     # unknown student
bad.loc[7, "score"] = "absent"               # not a number
bad = pd.concat([bad, bad.iloc[[9]]], ignore_index=True)  # duplicate row
bad.loc[11, "score"] = None                  # missing score

# --------------------------------------------------------------- write out --
users_df.to_csv(f"{OUT}/users.csv", index=False)
students_df.to_csv(f"{OUT}/students.csv", index=False)
courses_df.to_csv(f"{OUT}/courses.csv", index=False)
semesters_df.to_csv(f"{OUT}/semesters.csv", index=False)
enroll_df.to_csv(f"{OUT}/enrollments.csv", index=False)
# attendance intentionally NOT exported in this variant
exp.to_csv(f"{OUT}/expected_probation_results.csv", index=False)
valid.to_csv(f"{OUT}/upload_sample_valid.csv", index=False)
bad.to_csv(f"{OUT}/upload_sample_with_errors.csv", index=False)

print("students   :", len(students_df))
print("courses    :", len(courses_df))
print("enrollments:", len(enroll_df))
print("flagged student-semesters:", int(exp.should_be_flagged.sum()), "of", len(exp))
print(exp.groupby("semester_id").should_be_flagged.agg(["sum", "count"]))

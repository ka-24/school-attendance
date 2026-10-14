import calendar
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text
from security import decrypt_data

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL) if DATABASE_URL else None

if engine:
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                encrypted_name TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER,
                month TEXT,
                day INTEGER,
                status TEXT,
                UNIQUE(student_id, month, day)
            )
        """))
        conn.commit()

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

@app.get("/", response_class=HTMLResponse)
async def read_attendance(request: Request, month: str = "October", year: int = 2026, section: str = "A"):
    if not engine:
        return HTMLResponse("<h1>Database not connected. Check environment variables!</h1>")
        
    month_num = MONTH_NAMES.index(month) + 1 if month in MONTH_NAMES else 10
    _, days_in_month = calendar.monthrange(year, month_num)
    
    day_headers = []
    for d in range(1, days_in_month + 1):
        day_abbr = calendar.day_abbr[calendar.weekday(year, month_num, d)]
        day_headers.append({"date": d, "name": day_abbr})
    
    with engine.connect() as conn:
        students_query = conn.execute(
            text("SELECT id, encrypted_name FROM students ORDER BY id")
        ).fetchall()
        all_students = [{"id": row[0], "name": decrypt_data(row[1])} for row in students_query]
        
        # Split into A and B sections (51 students each)
        if section == "A":
            students = all_students[:51]
        elif section == "B":
            students = all_students[51:102]
        else:
            students = all_students
            
        attendance_query = conn.execute(
            text("SELECT student_id, day, status FROM attendance WHERE month = :month"),
            {"month": f"{month}_{year}"}
        ).fetchall()
        
    attendance_dict = {student['id']: {} for student in students}
    present_counts = {student['id']: 0 for student in students}
    
    for record in attendance_query:
        s_id, day, status = record[0], record[1], record[2]
        # Only process attendance for students currently visible in the selected section
        if s_id in attendance_dict:
            attendance_dict[s_id][day] = status
            if status == "P":
                present_counts[s_id] += 1
            
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "students": students,
            "selected_month": month,
            "selected_year": year,
            "selected_section": section,
            "months_list": MONTH_NAMES,
            "years_list": [2025, 2026, 2027],
            "attendance": attendance_dict,
            "present_counts": present_counts,
            "day_headers": day_headers
        }
    )

@app.post("/mark")
async def mark_attendance(
    student_id: int = Form(...),
    month: str = Form(...),
    day: int = Form(...),
    status: str = Form(...)
):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO attendance (student_id, month, day, status) 
            VALUES (:student_id, :month, :day, :status)
            ON CONFLICT (student_id, month, day) 
            DO UPDATE SET status = EXCLUDED.status
        """), {"student_id": student_id, "month": month, "day": day, "status": status})
        conn.commit()
    return {"success": True}

@app.post("/clear_day")
async def clear_day(month: str = Form(...), day: int = Form(...)):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM attendance WHERE month = :month AND day = :day"), 
                     {"month": month, "day": day})
        conn.commit()
    return {"success": True}
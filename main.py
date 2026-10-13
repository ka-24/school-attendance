import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, text
from security import encrypt_data, decrypt_data

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# This pulls your Neon database link from Render securely
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def init_db():
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
        
        count = conn.execute(text("SELECT COUNT(*) FROM students")).scalar()
        if count == 0:
            conn.execute(text("INSERT INTO students (encrypted_name) VALUES (:name)"), {"name": encrypt_data("Abhishek Fakkeerappa")})
            conn.execute(text("INSERT INTO students (encrypted_name) VALUES (:name)"), {"name": encrypt_data("Anjali Basavaraj")})
        conn.commit()

# Only initialize the database if the URL is provided (prevents local crashes)
if DATABASE_URL:
    init_db()

@app.get("/", response_class=HTMLResponse)
async def read_attendance(request: Request, month: str = "September"):
    if not DATABASE_URL:
        return HTMLResponse("<h1>Database not connected. Deploy to Render first!</h1>")
        
    with engine.connect() as conn:
        students_query = conn.execute(text("SELECT id, encrypted_name FROM students")).fetchall()
        students = [{"id": row[0], "name": decrypt_data(row[1])} for row in students_query]
        
        attendance_query = conn.execute(text("SELECT student_id, day, status FROM attendance WHERE month = :month"), {"month": month}).fetchall()
        
    attendance_dict = {student['id']: {} for student in students}
    for record in attendance_query:
        attendance_dict[record[0]][record[1]] = record[2]
        
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "request": request, 
            "students": students, 
            "selected_month": month,
            "attendance": attendance_dict,
            "days_in_month": 30
        }
    )

@app.post("/mark")
async def mark_attendance(student_id: int = Form(...), month: str = Form(...), day: int = Form(...), status: str = Form(...)):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO attendance (student_id, month, day, status) 
            VALUES (:student_id, :month, :day, :status)
            ON CONFLICT (student_id, month, day) 
            DO UPDATE SET status = EXCLUDED.status
        """), {"student_id": student_id, "month": month, "day": day, "status": status})
        conn.commit()
    return {"success": True}
# upload_students.py
import os
from sqlalchemy import create_engine, text
from security import encrypt_data

# Paste your Neon connection URL here:
DATABASE_URL = "postgresql://neondb_owner:npg_q2gMWm5kADIv@ep-old-haze-b4ebtsmd.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

with open("students.txt", "r", encoding="utf-8") as f:
    names = [line.strip() for line in f if line.strip()]

with engine.connect() as conn:
    for name in names:
        conn.execute(
            text("INSERT INTO students (encrypted_name) VALUES (:name)"),
            {"name": encrypt_data(name)}
        )
    conn.commit()

print(f"Successfully added and encrypted {len(names)} students!")
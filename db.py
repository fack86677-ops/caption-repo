"""
Database layer for Kalakar Web Studio / Harsh Caption Generator.
Provides SQLite persistent storage for Users, Sessions, OTPs, Transcription Jobs, and Projects.
"""
import sqlite3
import os
import uuid
import time
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studio.db")
ADMIN_EMAILS = ["harshdhiman332@gmail.com"]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        password_hash TEXT,
        role TEXT DEFAULT 'user',
        credits INTEGER DEFAULT 100,
        is_active INTEGER DEFAULT 1,
        auth_provider TEXT DEFAULT 'email',
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # OTP Requests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        otp_code TEXT NOT NULL,
        attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        is_used INTEGER DEFAULT 0
    )
    """)
    
    # Transcription Jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcription_jobs (
        job_id TEXT PRIMARY KEY,
        user_id TEXT,
        filename TEXT,
        duration REAL DEFAULT 0,
        status TEXT DEFAULT 'completed',
        credits_deducted INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    )
    """)
    
    # Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_requests(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id)")
    
    conn.commit()
    
    # Migrate any existing users from users.json if exists
    try:
        users_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
        if os.path.exists(users_json_path):
            with open(users_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for email, info in data.items():
                        cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
                        if not cursor.fetchone():
                            uid = str(uuid.uuid4())
                            role = 'admin' if email.lower() in ADMIN_EMAILS else 'user'
                            cursor.execute("""
                            INSERT INTO users (id, email, name, role, credits, auth_provider)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (uid, email.lower(), info.get("name", email.split("@")[0]), role, info.get("credits", 100), "email"))
            conn.commit()
    except Exception as e:
        print(f"[DB] Migration notice: {e}")
        
    conn.close()

# User Management
def get_user_by_email(email):
    if not email:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    if not user_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_or_create_user(email, name="", auth_provider="email", avatar_url=""):
    clean_email = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (clean_email,))
    row = cursor.fetchone()
    
    role = 'admin' if clean_email in ADMIN_EMAILS else 'user'
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    if row:
        user_id = row["id"]
        # Update last login & ensure admin role if email matches
        target_role = 'admin' if clean_email in ADMIN_EMAILS else row["role"]
        display_name = name or row["name"] or clean_email.split("@")[0]
        avatar = avatar_url or row["avatar_url"]
        cursor.execute("""
        UPDATE users SET last_login_at = ?, role = ?, name = ?, avatar_url = ?
        WHERE id = ?
        """, (now_str, target_role, display_name, avatar, user_id))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        updated_row = cursor.fetchone()
        conn.close()
        return dict(updated_row)
    else:
        user_id = str(uuid.uuid4())
        display_name = name or clean_email.split("@")[0]
        cursor.execute("""
        INSERT INTO users (id, email, name, role, credits, is_active, auth_provider, avatar_url, created_at, last_login_at)
        VALUES (?, ?, ?, ?, 100, 1, ?, ?, ?, ?)
        """, (user_id, clean_email, display_name, role, auth_provider, avatar_url, now_str, now_str))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        new_row = cursor.fetchone()
        conn.close()
        return dict(new_row)

def update_user_credits(user_id, delta):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None, "User not found"
    
    curr = row["credits"]
    new_credits = curr + delta
    if new_credits < 0:
        conn.close()
        return curr, "Insufficient credits"
        
    cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_credits, user_id))
    conn.commit()
    conn.close()
    return new_credits, None

def set_user_role_and_status(user_id, role=None, is_active=None, credits=None):
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    if role is not None:
        updates.append("role = ?")
        params.append(role)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if is_active else 0)
    if credits is not None:
        updates.append("credits = ?")
        params.append(credits)
        
    if updates:
        params.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
        conn.commit()
    conn.close()
    return True

# Session Management
def create_session(user_id, days=7):
    conn = get_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=days)
    expires_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
    INSERT INTO sessions (session_id, user_id, expires_at)
    VALUES (?, ?, ?)
    """, (session_id, user_id, expires_str))
    conn.commit()
    conn.close()
    return session_id

def get_session(session_id):
    if not session_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
    SELECT s.session_id, s.expires_at, u.id, u.email, u.name, u.role, u.credits, u.is_active, u.avatar_url, u.auth_provider, u.created_at
    FROM sessions s
    JOIN users u ON s.user_id = u.id
    WHERE s.session_id = ? AND s.expires_at > ?
    """, (session_id, now_str))
    row = cursor.fetchone()
    conn.close()
    if row and row["is_active"] == 1:
        return dict(row)
    return None

def delete_session(session_id):
    if not session_id:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

# OTP Management
def create_otp_request(email, otp_code, expiry_minutes=10, cooldown_seconds=30):
    clean_email = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check rate limit / cooldown
    cursor.execute("""
    SELECT created_at FROM otp_requests
    WHERE email = ? AND is_used = 0
    ORDER BY id DESC LIMIT 1
    """, (clean_email,))
    last_row = cursor.fetchone()
    
    if last_row:
        try:
            last_time = datetime.strptime(last_row["created_at"], '%Y-%m-%d %H:%M:%S')
            if (datetime.utcnow() - last_time).total_seconds() < cooldown_seconds:
                conn.close()
                return False, f"Please wait {cooldown_seconds} seconds before requesting a new OTP."
        except Exception:
            pass
            
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    expires_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
    INSERT INTO otp_requests (email, otp_code, expires_at)
    VALUES (?, ?, ?)
    """, (clean_email, otp_code, expires_str))
    conn.commit()
    conn.close()
    return True, "OTP generated successfully"

def verify_otp_code(email, otp_code):
    clean_email = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
    SELECT id, otp_code, attempts, expires_at, is_used FROM otp_requests
    WHERE email = ? AND is_used = 0 AND expires_at > ?
    ORDER BY id DESC LIMIT 1
    """, (clean_email, now_str))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False, "OTP has expired or does not exist. Please request a new code."
        
    otp_id = row["id"]
    attempts = row["attempts"]
    expected_code = row["otp_code"]
    
    if attempts >= 5:
        conn.close()
        return False, "Too many failed attempts. Please request a new code."
        
    if otp_code.strip() != expected_code.strip():
        cursor.execute("UPDATE otp_requests SET attempts = attempts + 1 WHERE id = ?", (otp_id,))
        conn.commit()
        conn.close()
        return False, "Incorrect OTP code. Please try again."
        
    # Mark as used
    cursor.execute("UPDATE otp_requests SET is_used = 1 WHERE id = ?", (otp_id,))
    conn.commit()
    conn.close()
    return True, "OTP verified successfully"

# Transcription Jobs & Projects
def record_transcription_job(job_id, user_id, filename, duration=0, status='completed', credits_deducted=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transcription_jobs (job_id, user_id, filename, duration, status, credits_deducted)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (job_id, user_id, filename, duration, status, credits_deducted))
    conn.commit()
    conn.close()

def save_project(project_id, user_id, title, data_json):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("SELECT project_id FROM projects WHERE project_id = ?", (project_id,))
    if cursor.fetchone():
        cursor.execute("""
        UPDATE projects SET title = ?, data_json = ?, updated_at = ?
        WHERE project_id = ?
        """, (title, data_json, now_str, project_id))
    else:
        cursor.execute("""
        INSERT INTO projects (project_id, user_id, title, data_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, user_id, title, data_json, now_str, now_str))
    conn.commit()
    conn.close()

def get_user_projects(user_id, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT project_id, user_id, title, created_at, updated_at
    FROM projects
    WHERE user_id = ?
    ORDER BY updated_at DESC LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_jobs(user_id, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT job_id, filename, duration, status, credits_deducted, created_at
    FROM transcription_jobs
    WHERE user_id = ?
    ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Admin Analytics & Queries
def get_admin_overview():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()["total_users"]
    
    cursor.execute("SELECT COUNT(*) as active_users FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()["active_users"]
    
    cursor.execute("SELECT COUNT(*) as total_jobs FROM transcription_jobs")
    total_jobs = cursor.fetchone()["total_jobs"]
    
    cursor.execute("SELECT SUM(credits_deducted) as total_credits_spent FROM transcription_jobs")
    total_credits_spent = cursor.fetchone()["total_credits_spent"] or 0
    
    cursor.execute("SELECT COUNT(*) as total_projects FROM projects")
    total_projects = cursor.fetchone()["total_projects"]
    
    conn.close()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_jobs": total_jobs,
        "total_credits_spent": total_credits_spent,
        "total_projects": total_projects
    }

def get_all_users_list(search=""):
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        query = f"%{search.strip().lower()}%"
        cursor.execute("""
        SELECT id, email, name, role, credits, is_active, auth_provider, created_at, last_login_at
        FROM users
        WHERE email LIKE ? OR name LIKE ?
        ORDER BY created_at DESC
        """, (query, query))
    else:
        cursor.execute("""
        SELECT id, email, name, role, credits, is_active, auth_provider, created_at, last_login_at
        FROM users
        ORDER BY created_at DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Auto-initialize database on import
init_db()

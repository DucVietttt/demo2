import sqlite3
import bcrypt

DB_NAME = "app.db"

# -----------------------------
# Khởi tạo DB (nếu chưa có)
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Tạo bảng users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tạo bảng uploads
    c.execute("""
    CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        result_path TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Tạo bảng login_logs
    c.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        success BOOLEAN NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# User: Đăng ký
# -----------------------------
def add_user(username, password, email=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        c.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                  (username, password_hash, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# -----------------------------
# User: Đăng nhập
# -----------------------------
def check_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row:
        user_id, stored_hash = row
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return user_id
    return None


# -----------------------------
# Uploads: Lưu file upload
# -----------------------------
def add_upload(user_id, file_name, file_path, file_type, result_path=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO uploads (user_id, file_name, file_path, file_type, result_path) 
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, file_name, file_path, file_type, result_path))
    conn.commit()
    conn.close()


# -----------------------------
# Login logs: Ghi lại log
# -----------------------------
def log_login(user_id, success, ip_address=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO login_logs (user_id, success, ip_address) 
                 VALUES (?, ?, ?)""", (user_id, success, ip_address))
    conn.commit()
    conn.close()

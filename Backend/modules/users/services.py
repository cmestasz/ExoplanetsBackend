import sqlite3
from fastapi import HTTPException
from .models import AuthRequest, AuthResponse

DB_NAME = "users.db"

def init_bd ():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    connection.commit()
    connection.close()

def get_connection ():
    return sqlite3.connect(DB_NAME)

async def registerUser (request: AuthRequest) -> AuthResponse:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (request.username, request.password))
        connection.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        connection.close()

    return AuthResponse(username=request.username, messsage="User registered succesfully")

async def loginUser (request: AuthRequest) -> AuthResponse:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (request.username, request.password))
    user = cursor.fetchone()
    
    connection.close()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return AuthResponse(username=request.username, message="Login successful")

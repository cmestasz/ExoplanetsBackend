from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import hashlib
from dotenv import load_dotenv
import os
from .models import *

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_KEY = os.getenv("DATABASE_KEY")

DATABASE_URL = "postgresql://pgplnzamgqqzcoezrkxf.supabase.co"
DATABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBncGxuemFtZ3FxemNvZXpya3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE2MDMwMzUsImV4cCI6MjA0NzE3OTAzNX0.yxHX1VBmT-XfVgmsxFmIvWIwx1NcitP4VZkH1bsg9FQ"

# Configuración del motor de PostgreSQL
engine = create_engine(f"postgresql://{DATABASE_URL}", pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas si no existen
def init_db():
    with engine.connect() as connection:
        connection.execute(
            text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS constellations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                user_id INTEGER REFERENCES users(id),
                ra FLOAT NOT NULL,
                dec FLOAT NOT NULL,
                dist FLOAT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stars (
                id SERIAL PRIMARY KEY,
                ext_id VARCHAR(100) NOT NULL,
                constellation_id INTEGER REFERENCES constellations(id)
            );
            CREATE TABLE IF NOT EXISTS star_connections (
                id SERIAL PRIMARY KEY,
                star_id INTEGER REFERENCES stars(id),
                connected_star_id INTEGER
            );
            """
            )
        )

# Funciones auxiliares
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(sent: str, original: str):
    return hash_password(sent) == original

# Operaciones principales
async def registerUser(request: User) -> str:
    session = SessionLocal()
    h_password = hash_password(request.password)
    try:
        session.execute(
            text("INSERT INTO users (username, password) VALUES (:username, :password)"),
            {"username": request.username, "password": h_password},
        )
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        session.close()
    return "User registered successfully"

async def loginUser(request: AuthRequest) -> str:
    session = SessionLocal()
    user = session.execute(
        text("SELECT * FROM users WHERE username = :username"),
        {"username": request.username},
    ).fetchone()
    session.close()

    if not user or not check_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return user["id"]

async def createConstellation(user_id: int, constellation: Constellation) -> str:
    session = SessionLocal()
    try:
        result = session.execute(
            text(
                "INSERT INTO constellations (name, user_id, ra, dec, dist) "
                "VALUES (:name, :user_id, :ra, :dec, :dist) RETURNING id"
            ),
            {
                "name": constellation.name,
                "user_id": user_id,
                "ra": constellation.ra,
                "dec": constellation.dec,
                "dist": constellation.dist,
            },
        )
        constellation_id = result.fetchone()["id"]

        for star in constellation.stars:
            star_result = session.execute(
                text(
                    "INSERT INTO stars (ext_id, constellation_id) "
                    "VALUES (:ext_id, :constellation_id) RETURNING id"
                ),
                {"ext_id": star.ext_id, "constellation_id": constellation_id},
            )
            star_id = star_result.fetchone()["id"]

            for connected_star_id in star.connected_stars:
                session.execute(
                    text(
                        "INSERT INTO star_connections (star_id, connected_star_id) "
                        "VALUES (:star_id, :connected_star_id)"
                    ),
                    {"star_id": star_id, "connected_star_id": connected_star_id},
                )

        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database error")
    finally:
        session.close()
    return "Constellation created successfully"
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import hashlib
from dotenv import load_dotenv
import os
from .models import *

load_dotenv()

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# Configuración del motor de PostgreSQL
engine = create_engine(
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas si no existen
def init_db():
    session = SessionLocal()
    session.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS userst (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS constellations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            user_id INTEGER REFERENCES userst(id),
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

    session.commit()


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
            text(
                "INSERT INTO userst (username, password) VALUES (:username, :password)"
            ),
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
        text("SELECT * FROM userst WHERE username = :username"),
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


async def getActiveConstellationsByUser(
    user_id: int, ra: float, dec: float, dist: float
) -> list[Constellation]:
    return getConstellationsByQuery(
        "SELECT * FROM constellations WHERE user_id = ? AND ra = ? AND dec = ? AND dist = ?",
        (
            user_id,
            ra,
            dec,
            dist,
        ),
    )


async def getAllConstellationsByUser(user_id: int) -> list[Constellation]:
    return getConstellationsByQuery(
        "SELECT * FROM constellations WHERE user_id = ?", (user_id,)
    )


def getConstellationsByQuery(
    query: str, args: tuple
) -> tuple[str, list[Constellation]]:
    try:
        session = SessionLocal()
        # Obtener todas las constelaciones del usuario

        constellations_data = session.execute(query, args)

        constellations = []
        for constellation in constellations_data:
            constellation_id = constellation[0]
            stars_data = session.execute(
                "SELECT * FROM stars WHERE constellation_id = ?", (constellation_id,)
            )

            stars = []
            for star in stars_data:
                star_id = star[0]
                connections = session.execute(
                    "SELECT connected_star_id FROM star_connections WHERE star_id = ?",
                    (star_id,),
                )
                connected_star_ids = [conn[0] for conn in connections]

                stars.append(
                    ConstellationStar(
                        ext_id=star[1],
                        connected_stars=connected_star_ids,
                    )
                )

            constellations.append(
                Constellation(
                    id=constellation[0],
                    name=constellation[1],
                    ra=constellation[2],
                    dec=constellation[3],
                    dist=constellation[4],
                    stars=stars,
                )
            )

    except:
        session.close()
        raise HTTPException(status_code=500, detail="dberror")

    session.close()

    return constellations

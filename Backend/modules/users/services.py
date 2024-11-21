import sqlite3
from fastapi import HTTPException
import hashlib
from .models import *

DB_NAME = "users.db"


def init_bd():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Tabla de usuarios
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """
    )

    # Tabla de constelaciones
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS constellations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ra REAL NOT NULL,
            dec REAL NOT NULL,
            dist REAL NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    )

    # Tabla de estrellas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ext_id TEXT NOT NULL,
            constellation_id INTEGER,
            FOREIGN KEY (constellation_id) REFERENCES constellations(id)
        )
    """
    )

    # Tabla para conexiones entre estrellas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS star_connections (
            star_id INTEGER,
            connected_star_id INTEGER,
            FOREIGN KEY (star_id) REFERENCES stars(id),
            FOREIGN KEY (connected_star_id) REFERENCES stars(ext_id),
            PRIMARY KEY (star_id, connected_star_id)
        )
    """
    )

    connection.commit()
    connection.close()


def get_connection():
    return sqlite3.connect(DB_NAME)


def hash_password(password: str):
    hasher = hashlib.sha256(password.encode())
    return hasher.hexdigest()


def check_password(sent: str, original: str):
    return hash_password(sent) == original


async def registerUser(request: User) -> AuthResponse:
    connection = get_connection()
    cursor = connection.cursor()

    h_password = hash_password(request.password)
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (request.username, h_password),
        )
        user_id = cursor.lastrowid

        for constellation in request.constellations:
            cursor.execute(
                "INSERT INTO constellations (name, user_id) VALUES (?, ?)",
                (constellation.name, user_id),
            )
            constellation_id = cursor.lastrowid

            for star in constellation.stars:
                cursor.execute(
                    "INSERT INTO stars (name, x, y, z, constellation_id) VALUES (?, ?, ?, ?, ?)",
                    (star.name, star.x, star.y, star.z, constellation_id),
                )
                star_id = cursor.lastrowid

                # Insertar conexiones de la estrella
                for connected_star_id in star.connected_stars:
                    cursor.execute(
                        "INSERT INTO star_connections (star_id, connected_star_id) VALUES (?, ?)",
                        (star_id, connected_star_id),
                    )

        connection.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        connection.close()

    return AuthResponse(
        username=request.username, message="User registered successfully"
    )


async def loginUser(request: AuthRequest) -> User:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (request.username,),
    )
    user_data = cursor.fetchone()

    connection.close()
    if not check_password(request.password, user_data[2]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return User(
        id=user_data[0],
        username=user_data[1],
        password=user_data[2],
    )


async def createConstellation(user_id: int, constellation: Constellation) -> None:
    connection = get_connection()
    cursor = connection.cursor()

    ra = constellation.ra
    dec = constellation.dec
    dist = constellation.dist

    try:
        # Insertar la constelación
        cursor.execute(
            "INSERT INTO constellations (name, user_id, ra, dec, dist) VALUES (?, ?, ?, ?, ?)",
            (constellation.name, user_id, ra, dec, dist),
        )
        constellation_id = cursor.lastrowid

        # Insertar las estrellas de la constelación
        for star in constellation.stars:
            cursor.execute(
                "INSERT INTO stars (ext_id, constellation_id) VALUES (?, ?)",
                (star.ext_id, constellation_id),
            )
            star_id = cursor.lastrowid

            # Insertar las conexiones de la estrella
            for connected_star_id in star.connected_stars:
                cursor.execute(
                    "INSERT INTO star_connections (star_id, connected_star_id) VALUES (?, ?)",
                    (star_id, connected_star_id),
                )

        connection.commit()
    except Exception as e:
        connection.rollback()
        connection.close()
        raise HTTPException(status_code=400, detail="dberror")

    connection.close()


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
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Obtener todas las constelaciones del usuario
        cursor.execute(query, args)
        constellations_data = cursor.fetchall()

        constellations = []
        for constellation in constellations_data:
            constellation_id = constellation[0]
            cursor.execute(
                "SELECT * FROM stars WHERE constellation_id = ?", (constellation_id,)
            )
            stars_data = cursor.fetchall()

            stars = []
            for star in stars_data:
                star_id = star[0]
                cursor.execute(
                    "SELECT connected_star_id FROM star_connections WHERE star_id = ?",
                    (star_id,),
                )
                connections = cursor.fetchall()
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
        connection.close()
        raise HTTPException(status_code=500, detail="dberror")

    connection.close()

    return constellations

import sqlite3
from fastapi import HTTPException
from .models import *

DB_NAME = "users.db"

def init_bd():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Tabla de constelaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS constellations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Tabla de estrellas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            x REAL,
            y REAL,
            z REAL,
            constellation_id INTEGER,
            FOREIGN KEY (constellation_id) REFERENCES constellations(id)
        )
    """)
    
    # Tabla para conexiones entre estrellas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS star_connections (
            star_id INTEGER,
            connected_star_id INTEGER,
            FOREIGN KEY (star_id) REFERENCES stars(id),
            FOREIGN KEY (connected_star_id) REFERENCES stars(id),
            PRIMARY KEY (star_id, connected_star_id)
        )
    """)
    
    connection.commit()
    connection.close()


def get_connection ():
    return sqlite3.connect(DB_NAME)

async def registerUser(request: User) -> AuthResponse:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (request.username, request.password))
        user_id = cursor.lastrowid
        
        for constellation in request.constellations:
            cursor.execute(
                "INSERT INTO constellations (name, user_id) VALUES (?, ?)", 
                (constellation.name, user_id)
            )
            constellation_id = cursor.lastrowid
            
            for star in constellation.stars:
                cursor.execute(
                    "INSERT INTO stars (name, x, y, z, constellation_id) VALUES (?, ?, ?, ?, ?)",
                    (star.name, star.x, star.y, star.z, constellation_id)
                )
                star_id = cursor.lastrowid

                # Insertar conexiones de la estrella
                for connected_star_id in star.connected_stars:
                    cursor.execute(
                        "INSERT INTO star_connections (star_id, connected_star_id) VALUES (?, ?)",
                        (star_id, connected_star_id)
                    )
        
        connection.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        connection.close()

    return AuthResponse(username=request.username, message="User registered successfully")


async def loginUser(request: AuthRequest) -> User:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (request.username, request.password))
    user_data = cursor.fetchone()

    if user_data is None:
        connection.close()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_id = user_data[0]
    cursor.execute("SELECT * FROM constellations WHERE user_id = ?", (user_id,))
    constellations_data = cursor.fetchall()

    constellations = []
    for constellation in constellations_data:
        constellation_id = constellation[0]
        cursor.execute("SELECT * FROM stars WHERE constellation_id = ?", (constellation_id,))
        stars_data = cursor.fetchall()

        stars = []
        for star in stars_data:
            star_id = star[0]
            cursor.execute("SELECT connected_star_id FROM star_connections WHERE star_id = ?", (star_id,))
            connections = cursor.fetchall()
            connected_star_ids = [conn[0] for conn in connections]

            stars.append(Star(
                id=star[0], name=star[1], x=star[2], y=star[3], z=star[4], connected_stars=connected_star_ids
            ))
        
        constellations.append(Constellation(
            id=constellation[0], name=constellation[1], stars=stars
        ))

    connection.close()

    return User(id=user_data[0], username=user_data[1], password=user_data[2], constellations=constellations)


async def createConstellation(user_id: int, constellation: Constellation):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Insertar la constelación
        cursor.execute(
            "INSERT INTO constellations (name, user_id) VALUES (?, ?)", 
            (constellation.name, user_id)
        )
        constellation_id = cursor.lastrowid

        # Insertar las estrellas de la constelación
        for star in constellation.stars:
            cursor.execute(
                "INSERT INTO stars (name, x, y, z, constellation_id) VALUES (?, ?, ?, ?, ?)",
                (star.name, star.x, star.y, star.z, constellation_id)
            )
            star_id = cursor.lastrowid

            # Insertar las conexiones de la estrella
            for connected_star_id in star.connected_stars:
                cursor.execute(
                    "INSERT INTO star_connections (star_id, connected_star_id) VALUES (?, ?)",
                    (star_id, connected_star_id)
                )

        connection.commit()
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        connection.close()

    return {"message": "Constellation created successfully"}


async def getConstellationsByUser(user_id: int) -> list[Constellation]:
    connection = get_connection()
    cursor = connection.cursor()

    # Obtener todas las constelaciones del usuario
    cursor.execute("SELECT * FROM constellations WHERE user_id = ?", (user_id,))
    constellations_data = cursor.fetchall()

    constellations = []
    for constellation in constellations_data:
        constellation_id = constellation[0]
        cursor.execute("SELECT * FROM stars WHERE constellation_id = ?", (constellation_id,))
        stars_data = cursor.fetchall()

        stars = []
        for star in stars_data:
            star_id = star[0]
            cursor.execute("SELECT connected_star_id FROM star_connections WHERE star_id = ?", (star_id,))
            connections = cursor.fetchall()
            connected_star_ids = [conn[0] for conn in connections]

            stars.append(Star(
                id=star[0], name=star[1], x=star[2], y=star[3], z=star[4], connected_stars=connected_star_ids
            ))

        constellations.append(Constellation(
            id=constellation[0], name=constellation[1], stars=stars
        ))

    connection.close()

    return constellations


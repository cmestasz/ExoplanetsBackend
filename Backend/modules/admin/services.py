import sqlite3

DB_NAME = "users.db"


def drop_db():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("DROP TABLE users")
    cursor.execute("DROP TABLE constellations")
    cursor.execute("DROP TABLE stars")
    cursor.execute("DROP TABLE star_connections")


def start_db():
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

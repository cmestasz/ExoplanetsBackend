from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from hashlib import sha256
from dotenv import load_dotenv
import os
from .models import *

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    return sha256(password.encode()).hexdigest()


def check_password(sent: str, original: str):
    return hash_password(sent) == original

async def createConstellation(user_id: int, constellation: Constellation) -> str:
    try:
        # Insertar constelación
        constellation_response = supabase.table("constellations").insert({
            "name": constellation.name,
            "user_id": user_id,
            "ra": constellation.ra,
            "dec": constellation.dec,
            "dist": constellation.dist,
        }).execute()

        if constellation_response.error:
            raise HTTPException(status_code=400, detail="Error creating constellation")

        constellation_id = constellation_response.data[0]["id"]

        for star in constellation.stars:
            # Insertar estrellas
            star_response = supabase.table("stars").insert({
                "ext_id": star.ext_id,
                "constellation_id": constellation_id,
            }).execute()

            if star_response.error:
                raise HTTPException(status_code=400, detail="Error creating stars")

            star_id = star_response.data[0]["id"]

            # Insertar conexiones entre estrellas
            for connected_star_id in star.connected_stars:
                connection_response = supabase.table("star_connections").insert({
                    "star_id": star_id,
                    "connected_star_id": connected_star_id,
                }).execute()

                if connection_response.error:
                    raise HTTPException(status_code=400, detail="Error creating star connections")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return "Constellation created successfully"


async def getAllConstellationsByUser(user_id: int) -> list[Constellation]:
    try:
        constellations_response = supabase.table("constellations").select("*").eq("user_id", user_id).execute()

        if constellations_response.error:
            raise HTTPException(status_code=500, detail="Error fetching constellations")

        constellations = []
        for constellation in constellations_response.data:
            stars_response = supabase.table("stars").select("*").eq("constellation_id", constellation["id"]).execute()

            if stars_response.error:
                raise HTTPException(status_code=500, detail="Error fetching stars")

            stars = []
            for star in stars_response.data:
                connections_response = supabase.table("star_connections").select("connected_star_id").eq("star_id", star["id"]).execute()

                if connections_response.error:
                    raise HTTPException(status_code=500, detail="Error fetching star connections")

                connected_star_ids = [connection["connected_star_id"] for connection in connections_response.data]

                stars.append(ConstellationStar(
                    ext_id=star["ext_id"],
                    connected_stars=connected_star_ids,
                ))

            constellations.append(Constellation(
                id=constellation["id"],
                name=constellation["name"],
                ra=constellation["ra"],
                dec=constellation["dec"],
                dist=constellation["dist"],
                stars=stars,
            ))

        return constellations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def getActiveConstellationsByUser(user_id: int, ra: float, dec: float, dist: float) -> list[Constellation]:
    try:
        constellations_response = supabase.table("constellations").select("*").match({
            "user_id": user_id,
            "ra": ra,
            "dec": dec,
            "dist": dist,
        }).execute()

        if constellations_response.error:
            raise HTTPException(status_code=500, detail="Error fetching constellations")

        constellations_data = constellations_response.data
        constellations = []

        for constellation in constellations_data:
            stars = await fetchStarsAndConnections(constellation["id"])
            constellations.append(Constellation(
                id=constellation["id"],
                name=constellation["name"],
                ra=constellation["ra"],
                dec=constellation["dec"],
                dist=constellation["dist"],
                stars=stars,
            ))

        return constellations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fetchStarsAndConnections(constellation_id: int) -> list[ConstellationStar]:
    try:
        # Obtener las estrellas de la constelación
        stars_response = supabase.table("stars").select("*").eq("constellation_id", constellation_id).execute()

        if stars_response.error:
            raise HTTPException(status_code=500, detail="Error fetching stars")

        stars_data = stars_response.data
        stars = []

        for star in stars_data:
            # Obtener las conexiones de cada estrella
            connections_response = supabase.table("star_connections").select("connected_star_id").eq("star_id", star["id"]).execute()

            if connections_response.error:
                raise HTTPException(status_code=500, detail="Error fetching star connections")

            connected_star_ids = [conn["connected_star_id"] for conn in connections_response.data]

            stars.append(ConstellationStar(
                ext_id=star["ext_id"],
                connected_stars=connected_star_ids,
            ))

        return stars

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

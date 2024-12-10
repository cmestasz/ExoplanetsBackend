import astropy.table
from fastapi import HTTPException
from .models import Exoplanet, RequestExoplanets
from .utils import parse_dec_to_degrees, parse_ra_to_degrees
from pydantic import BaseModel
from astropy.table import Table
import pyvo as vo
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import json
import re


client = vo.dal.TAPService("https://exoplanetarchive.ipac.caltech.edu/TAP")


def result_to_exoplanet_list(result: astropy.table) -> list[Exoplanet]:
    exoplanets = []
    for row in result:
        exoplanets.append(
            Exoplanet(
                name=row["pl_name"],
                ra=row["ra"],
                dec=row["dec"],
                parallax=row["parallax"],
            )
        )

    return exoplanets


async def find_some_exoplanets(index: int, amount: int)->tuple[bool, str]:


    # URL base
    url = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/IceTable/nph-iceTbl"

    # Parámetros de la solicitud (ajusta según sea necesario)
    params = {
        "log": "TblView.ExoplanetArchive",
        "workspace": "2024.12.02_10.04.18_002933/TblView/2024.12.05_16.11.34_009010",
        "table": "/exodata/kvmexoweb/ExoTables/PS.tbl",
        "pltxaxis": "",
        "pltyaxis": "",
        "checkbox": "1",
        "initialcheckedval": "1",
        "splitlabel": "0",
        "wsoverride": "1",
        "rowLabel": "rowlabel",
        "connector": "true",
        "dhx_no_header": "1",
        "posStart": index,  # Inicio de las filas
        "count": amount,    # Cantidad de filas a devolver
        "dhxr1733443898337": "1"
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        root = ET.fromstring(response.text)

        # Crear una lista para almacenar los datos
        planets = []

        # Extraer información de las filas (<row>)
        for row in root.findall(".//row"):
            planet_data = {}
            cells = row.findall("cell")
            if len(cells) > 2:  # Asegúrate de que haya suficientes datos
                planet_data["id"] = row.attrib.get("id")
                #print("------------->", cells[2].text)
                planet_data["name"] = re.findall(r">([^<]+)<",cells[2].text)[0]
                planet_data["host_star"] = cells[3].text
                # Estrellas en el sistema
                planet_data["stars_amount"] = cells[5].text
                # Año de descubrimientp
                planet_data["discovery_year"] = cells[8].text
                tmp =  re.findall(r">([^<]+)<", cells[15].text)
                # Radio del planeta compoarado con la Tierra
                if (len(tmp)>0):
                    planet_data["radius"] = tmp[0]
                else: 
                    tmp = re.findall(r"\d+\.\d+(?=&)",cells[15].text)
                    if len(tmp)>0: 
                        planet_data["radius"] = tmp[0]
                    else:
                        planet_data["radius"] = ""
                # Ascención recta: Posición en el cielo, en formato sexagesimal(grados, minutos, segundos)
                planet_data["ra"] = parse_ra_to_degrees(cells[33].text)
                # Declinación, similar a la latitud,  en formato sexagesimal(grados, minutos, segundos)
                planet_data["dec"] = parse_dec_to_degrees(cells[34].text)
                tmp =  re.findall(r">([^<]+)<", cells[35].text)
                # Distancia en parsecs
                if (len(tmp) > 0):
                    planet_data["dist"] = tmp[0]
                else: 
                    tmp = re.findall(r"\d+\.\d+(?=&)",cells[35].text)
                    if len(tmp)>0: 
                        planet_data["dist"] = tmp[0]
                    else:
                        planet_data["dist"] = ""
            planets.append(planet_data)

        # Convertir a JSON
        json_data = json.dumps(planets)
        return True, json_data
    else:
        print(f"Error: {response.status_code}")
        return False, ""




async def find_exoplanets_by_name(name: str) -> str:
    global client
    name = name.replace(' ','%')
    query = f"SELECT pl_name, ra, dec, parallax FROM ps WHERE pl_name LIKE '%{name}%' LIMIT 20"
    query = f"""
    SELECT DISTINCT
        pl_name AS "name",
        hostname AS "host_star",
        sy_snum AS "stars_amount",
        disc_year AS "discovery_year",
        pl_rade AS "radius",
        rastr AS "ra",
        decstr AS "dec",
        sy_dist AS "dist"
    FROM
        ps
    WHERE pl_name LIKE '%{name}%'
    """
    result = client.search(query)
    print(result)
    planet_set = set()
    if len(result) == 0: return ""
    planets = []
    for row in result:
        p = {}
        if row['name'] in planet_set: continue
        for key in row:
            val = str( row[key] )
            p[key] = val if val != 'nan' else ""
        planets.append(p)
        planet_set.add(row['name'])
    return json.dumps(planets)


'''
    ra, dec = exoplanets[0].ra, exoplanets[0].dec
    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")

    radius = 0.1 * u.deg
    query = f"""
SELECT TOP 10
    source_id, ra, dec, parallax, pmra, pmdec
FROM gaiadr3.gaia_source
WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius.to(u.deg).value})) = 1
"""

    job = Gaia.launch_job_async(query)
    results = job.get_results()

    star_coords = SkyCoord(
        ra=results["ra"] * u.deg, dec=results["dec"] * u.deg, frame="icrs"
    )
    sep = coord.separation(star_coords)

    plt.figure(figsize=(8, 8))
    plt.scatter(
        (results["ra"] - ra) * 3600,
        (results["dec"] - dec) * 3600,
        color="blue",
        label="Stars",
    )  # Converted to arcseconds
    plt.scatter(0, 0, color="red", label="Reference Position")
    plt.xlabel("RA Offset (arcseconds)")
    plt.ylabel("Dec Offset (arcseconds)")
    plt.title("Relative Star Positions")
    plt.legend()
    plt.grid(True)
    plt.show()

    print(subtable)
    print(results)
'''

import astropy.table
from fastapi import HTTPException
from .models import Exoplanet, RequestExoplanets
from pydantic import BaseModel
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
                planet_data["planet name"] = re.findall(r">([^<]+)<",cells[2].text)[0]
                planet_data["star name"] = cells[3].text
                planet_data["number of stars"] = cells[5].text
                planet_data["discovery year"] = cells[8].text
                tmp =  re.findall(r">([^<]+)<", cells[15].text)
                if (len(tmp)>0):
                    planet_data["planet radius (Earth)"] = tmp[0]
                else: 
                    tmp = re.findall(r"\d+\.\d+(?=&)",cells[15].text)
                    if len(tmp)>0: 
                        planet_data["planet radius (Earth)"] = tmp[0]
                    else:
                        planet_data["planet radius (Earth)"] = ""
                planet_data["ra (sexagesimal)"] = cells[33].text
                planet_data["dec (sexagesimal)"] = cells[34].text
                print("----------> ", cells[35].text)
                tmp =  re.findall(r">([^<]+)<", cells[35].text)
                if (len(tmp) > 0):
                    planet_data["distance (pc)"] = tmp[0]
                else: 
                    tmp = re.findall(r"\d+\.\d+(?=&)",cells[35].text)
                    if len(tmp)>0: 
                        planet_data["distance (pc)"] = tmp[0]
                    else:
                        planet_data["distance (pc)"] = ""
            planets.append(planet_data)

        # Convertir a JSON
        json_data = json.dumps(planets)
        return True, json_data
    else:
        print(f"Error: {response.status_code}")
        return False, ""




async def find_exoplanets_by_name(name: str) -> list[Exoplanet]:
    global client
    query = f"SELECT pl_name, ra, dec, parallax FROM ps WHERE pl_name LIKE '%{name}%' LIMIT 20"
    result = client.search(query)

    a_table: astropy.table = result.to_table()
    exoplanets = result_to_exoplanet_list(a_table)
    return exoplanets


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

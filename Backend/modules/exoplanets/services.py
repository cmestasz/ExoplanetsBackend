import astropy.table
from fastapi import HTTPException
from .models import Exoplanet, RequestExoplanets
from pydantic import BaseModel
from astropy.table import Table
import pyvo as vo
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import json
import re
from typing import Any


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
    global client

    query = f"""
    SELECT DISTINCT TOP {index + amount} 
        pl_name AS "name",
        hostname AS "host_star",
        sy_snum AS "stars_amount",
        disc_year AS "discovery_year",
        pl_rade AS "radius",
        ra AS "ra",
        dec AS "dec",
        sy_dist AS "dist",
        gaia_id AS "id"
    FROM
        pscomppars
    WHERE 
        pl_name IS NOT NULL AND 
        hostname IS NOT NULL AND 
        sy_snum IS NOT NULL AND 
        disc_year IS NOT NULL AND 
        pl_rade IS NOT NULL AND 
        ra IS NOT NULL AND 
        dec IS NOT NULL AND 
        sy_dist IS NOT NULL AND 
        gaia_id IS NOT NULL
    ORDER BY pl_name ASC
    """
    result = client.search(query)
    print(result)
    if len(result) == 0: return False,""
    planets=[]
    for i in range(index, min(index+amount, len(result))):
        p: dict[Any, Any] = {}
        #print(result[i])
        for key in result[i]:
            val = str(result[i][key])
            p[key]= val 
        planets.append(p)
    #print(json.dumps(planets, indent=4))
    return True, json.dumps(planets)




async def find_exoplanets_by_name(name: str) -> str:
    global client
    name = name.replace(' ','%')
    query = f"""
    SELECT DISTINCT  
        pl_name AS "name",
        hostname AS "host_star",
        sy_snum AS "stars_amount",
        disc_year AS "discovery_year",
        pl_rade AS "radius",
        ra AS "ra",
        dec AS "dec",
        sy_dist AS "dist",
        gaia_id AS "i"
    FROM
        pscomppars
    WHERE 
        LOWER( pl_name ) LIKE LOWER( '%{name}%' ) AND 
        hostname IS NOT NULL AND 
        sy_snum IS NOT NULL AND 
        disc_year IS NOT NULL AND 
        pl_rade IS NOT NULL AND 
        ra IS NOT NULL AND 
        dec IS NOT NULL AND 
        sy_dist IS NOT NULL AND 
        gaia_id IS NOT NULL
    """
    result = client.search(query)
    #print(result)
    if len(result) == 0: return "";
    planets = []
    for row in result:
        p = {}
        for key in row:
            val = str( row[key] )
            p[key] = val if val != 'nan' else ""
        planets.append(p)
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

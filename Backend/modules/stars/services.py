from astropy.table import Table
from astropy.table import Row
from astropy.coordinates import SkyCoord
from astroquery.gaia import Gaia
from .models import Star
import pyvo
import astropy.units as u
import numpy as np
from fastapi import HTTPException


def celestial_to_cartesian(ra, dec, distance):
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)

    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)

    return x, y, z


async def load_around_position(
    ra, dec, dist, srange=20, magLimit=6.5, searchRadius=360
) -> list[Star]:

    if ra < 0 or ra > 360 or dec < -90 or dec > 90 or dist < 0:
        raise HTTPException(status_code=406, detail="invalid")

    upperBound = dist + srange
    lowerBound = 0

    query = f"""
SELECT
    gaia_source.DESIGNATION,
    gaia_source.ra,
    gaia_source.dec,
    gaia_source.distance_gspphot
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(
    POINT('ICRS', ra, dec),
    BOX('ICRS', {ra}, {dec}, {searchRadius}, {searchRadius})
)
    AND gaia_source.phot_g_mean_mag < {magLimit}
    AND gaia_source.distance_gspphot <= {upperBound}
    AND gaia_source.distance_gspphot >= {lowerBound}
    AND gaia_source.parallax IS NOT NULL
ORDER BY gaia_source.distance_gspphot ASC;
"""

    stars = []
    try:
        job = Gaia.launch_job_async(query)
        results = job.get_results()
        ra_list = results["ra"]
        dec_list = results["dec"]
        designation_list = results["DESIGNATION"]
        dist_list = results["distance_gspphot"]
        x, y, z = celestial_to_cartesian(ra_list, dec_list, dist_list)
        for i in range(len(results)):
            stars.append(
                Star(x=str(x[i]), y=str(y[i]), z=str(z[i]), id=designation_list[i])
            )

    except:
        raise HTTPException(status_code=500, detail="error")

    return stars


client = pyvo.dal.TAPService("https://exoplanetarchive.ipac.caltech.edu/TAP")


# most seem to have a gaia id
async def load_around_id(id) -> tuple[list[Star], str, float, float, float]:
    query = f"SELECT TOP 1 pl_name, ra, dec, sy_dist FROM ps WHERE gaia_id='{id}'"
    table_exoplanets = client.search(query=query).to_table()

    if len(table_exoplanets) == 0:
        raise HTTPException(status_code=406, detail="invalid")

    exoplanet_row = Row(table=table_exoplanets, index=0)
    name = exoplanet_row["pl_name"]
    ra = exoplanet_row["ra"]
    dec = exoplanet_row["dec"]
    distance = exoplanet_row["sy_dist"]
    stars = await load_around_position(ra, dec, distance)

    return stars, name, ra, dec, distance

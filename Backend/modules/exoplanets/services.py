import astropy.table
from .models import Exoplanet
from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
from astropy import units as u
import pyvo as vo

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


async def find_some_exoplanets() -> list[Exoplanet]:
    global client
    query = "SELECT pl_name, ra, dec, parallax FROM ps LIMIT 20"
    result = client.search(query)

    a_table: astropy.table = result.to_table()
    exoplanets = result_to_exoplanet_list(a_table)
    return exoplanets


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

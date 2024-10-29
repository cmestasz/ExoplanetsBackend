from astropy.table import Table
from astropy.table import Row
from astropy.coordinates import SkyCoord
from astroquery.gaia import Gaia
from .models import Star
import pyvo
import astropy.units as u
import numpy as np


def celestial_to_cartesian_parallax(
    ra, dec, parallax, center_ra, center_dec, center_parallax
):
    """
    Convert celestial coordinates to Cartesian coordinates, centered on a specific star.

    Parameters:
    ra, dec, parallax: arrays of coordinates and parallaxes for the stars
    center_ra, center_dec, center_parallax: coordinates and parallax of the center star

    All inputs should be in degrees for ra/dec, and mas for parallax.
    """
    dist = 1000 / parallax
    center_dist = 1000 / center_parallax

    # Convert everything to radians
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    center_ra_rad = np.radians(center_ra)
    center_dec_rad = np.radians(center_dec)

    # Calculate Cartesian coordinates
    x = dist * np.cos(dec_rad) * np.cos(ra_rad)
    y = dist * np.cos(dec_rad) * np.sin(ra_rad)
    z = dist * np.sin(dec_rad)

    # Calculate center star's Cartesian coordinates
    center_x = center_dist * np.cos(center_dec_rad) * np.cos(center_ra_rad)
    center_y = center_dist * np.cos(center_dec_rad) * np.sin(center_ra_rad)
    center_z = center_dist * np.sin(center_dec_rad)

    # Subtract center star's coordinates to center the system
    x -= center_x
    y -= center_y
    z -= center_z

    return x, y, z


async def load_around_position(ra, dec, parallax) -> list[Star]:
    print(f"RA: {ra}, DEC: {dec}, PARALLAX: {parallax}")
    dist = 1000 / parallax

    Gaia.ROW_LIMIT = 100

    radius = 20 * u.pc
    radius_rad = np.arctan2(radius.to(u.pc).value, dist)
    radius_deg = radius_rad * u.rad.to(u.deg)


    query = f'''
SELECT TOP 4000
    DESIGNATION, ra, dec, parallax,
    DISTANCE(
        POINT('ICRS', ra, dec),
        POINT('ICRS', {ra}, {dec})
    ) AS angular_distance,
    ABS(1000/parallax - {dist}) AS radial_distance
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(
    POINT('ICRS', ra, dec),
    CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
)
    AND parallax > 0
    AND parallax/parallax_error > 5
    AND ABS(1000/parallax - {dist}) < {radius.value}
ORDER BY radial_distance ASC
'''

    job = Gaia.launch_job_async(query)
    results = job.get_results()
    
    ra_list = results["ra"]
    dec_list = results["dec"]
    designation_list = results["DESIGNATION"]
    parallax_list = results["parallax"]
    x, y, z = celestial_to_cartesian_parallax(
        ra_list, dec_list, parallax_list, ra, dec, parallax
    )
    sector = []
    for i in range(len(designation_list)):
        sector.append(
            Star(x=str(x[i]), y=str(y[i]), z=str(z[i]), name=designation_list[i])
        )
    return sector


async def generate_around_planet_name(planet_name) -> list[Star]:
    client = pyvo.dal.TAPService("https://exoplanetarchive.ipac.caltech.edu/TAP")
    query = f"SELECT * FROM ps WHERE pl_name LIKE '%{planet_name}%'"
    table_exoplanets: Table = client.search(query=query).to_table()
    # Take first entry
    exoplanet_row: Row = Row(table=table_exoplanets, index=0)
    ra = exoplanet_row["ra"]
    dec = exoplanet_row["dec"]
    distance = exoplanet_row["sy_dist"]
    # doubious origin
    parallax = (1000 / distance) * u.mas

    print(f"Planet name: {exoplanet_row['pl_name']}")
    # perhaps:
    # pmra = 2.0  # Movimiento propio en ascensión recta (mas/año, opcional)
    # pmdec = -1.5  # Movimiento propio en declinación (mas/año, opcional)
    # radial_velocity = 10.0  # Velocidad radial (km/s, opcional)
    coord: SkyCoord = SkyCoord(
        ra=ra,
        dec=dec,
        distance=distance * u.pc,
        unit=(u.degree, u.degree, u.pc),
        frame="icrs",
    )
    Gaia.ROW_LIMIT = 100
    results: Table = Gaia.query_object_async(coordinate=coord, radius=45 * u.deg)
    ra_list = results["ra"]
    dec_list = results["dec"]
    designation_list = results["DESIGNATION"]
    parallax_list = results["parallax"]
    print(results[0]["DESIGNATION"])
    x, y, z = celestial_to_cartesian_parallax(
        ra_list, dec_list, parallax_list, ra, dec, parallax  # dubious origin
    )
    sector = []
    for i in range(len(designation_list)):
        sector.append(
            Star(x=str(x[i]), y=str(y[i]), z=str(z[i]), name=designation_list[i])
        )
    return sector


"""
from chat:
# Datos del objeto celeste
ra = 280.0  # Ascensión recta (grados)
dec = -60.0  # Declinación (grados)
distance = 100.0  # Distancia en parsecs, podrías usar 'distance_gspphot'
pmra = 5.0  # Movimiento propio en ascensión recta (mas/año)
pmdec = -3.0  # Movimiento propio en declinación (mas/año)
radial_velocity = 20.0  # Velocidad radial (km/s)

# Creamos las coordenadas del objeto en el marco ICRS
object_coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, distance=distance*u.pc,
                        pm_ra_cosdec=pmra*u.mas/u.yr, pm_dec=pmdec*u.mas/u.yr,
                        radial_velocity=radial_velocity*u.km/u.s, frame='icrs')

# Definir el área de búsqueda en torno a esta posición
width = u.Quantity(0.1, u.deg)
height = u.Quantity(0.1, u.deg)

# Hacer la consulta Gaia desde la posición del objeto
# Esto devolverá los objetos cercanos desde el punto de vista terrestre, pero en tu caso
# luego puedes hacer transformaciones
r = Gaia.query_object_async(coordinate=object_coord, width=width, height=height)
"""

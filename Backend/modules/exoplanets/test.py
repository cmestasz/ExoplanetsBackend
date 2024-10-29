import astropy.table
from astropy.table import Table
from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
from astropy import units as u
import pyvo as vo
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D


def celestial_to_cartesian(ra, dec, parallax, center_ra, center_dec, center_parallax):
    """
    Convert celestial coordinates to Cartesian coordinates, centered on a specific star.

    Parameters:
    ra, dec, parallax: arrays of coordinates and parallaxes for the stars
    center_ra, center_dec, center_parallax: coordinates and parallax of the center star

    All inputs should be in degrees for ra/dec, and mas for parallax.
    """
    # Convert everything to radians
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)
    center_ra_rad = np.radians(center_ra)
    center_dec_rad = np.radians(center_dec)

    # Convert parallax to distance in parsecs
    dist = 1000 / parallax
    center_dist = 1000 / center_parallax

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


def test():
    client = vo.dal.TAPService("https://exoplanetarchive.ipac.caltech.edu/TAP")
    query = f"SELECT * FROM ps WHERE pl_name LIKE '%Boo%'"
    result = client.search(query=query)

    a_table: Table = result.to_table()

    name = a_table["pl_name"][0]
    print(f"Planet name: {name}")


    ra = a_table["ra"][0]
    dec = a_table["dec"][0]
    distance = a_table["sy_dist"][0]
    distance_error = a_table["sy_disterr1"][0]

    parallax = (1000 / distance) * u.mas
    parallax_error = (1000 * distance_error / (distance ** 2)) * u.mas

    radius = 20 * u.pc
    radius_rad = np.arctan2(radius.to(u.pc).value, distance)
    radius_deg = radius_rad * u.rad.to(u.deg)

    query = f'''
SELECT TOP 4000
    source_id, ra, dec, parallax, pmra, pmdec,
    DISTANCE(
        POINT('ICRS', ra, dec),
        POINT('ICRS', {ra}, {dec})
    ) AS angular_distance,
    ABS(1000/parallax - {distance}) AS radial_distance
FROM gaiadr3.gaia_source
WHERE 1=CONTAINS(
    POINT('ICRS', ra, dec),
    CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
)
    AND parallax > 0
    AND parallax/parallax_error > 5
    AND ABS(1000/parallax - {distance}) < {radius.value}
ORDER BY radial_distance ASC
'''

    job = Gaia.launch_job_async(query)
    results = job.get_results()

    ra_list = results['ra']  # Right Ascension in degrees
    dec_list = results['dec']  # Declination in degrees
    parallax_list = results['parallax']  # Parallax in milliarcseconds (mas)

    print(f"Number of stars found: {len(ra_list)}")

    center_ra = ra
    center_dec = dec
    center_parallax = parallax.value  # assuming parallax is an astropy Quantity

    x, y, z = celestial_to_cartesian(
        ra_list, dec_list, parallax_list, center_ra, center_dec, center_parallax)

    #print(x)
    #print("-----")
    #print(y)
    #print("-----")
    #print(z)
    #print("-----")

    # Set up 3D plot
    #fig = plt.figure(figsize=(8, 8))
    #ax = fig.add_subplot(111, projection='3d')

    ## Plot the stars
    #ax.scatter(x, y, z, c='blue', marker='o', label='Stars')

    ## Plot the reference position at the origin (0, 0, 0)
    #ax.scatter(0, 0, 0, c='red', marker='x', s=100,
    #           label='Reference Point (Origin)')

    ## Set labels
    #ax.set_xlabel('X (pc)')
    #ax.set_ylabel('Y (pc)')
    #ax.set_zlabel('Z (pc)')

    ## Add title and legend
    #ax.set_title('3D Plot of Star Positions Relative to Reference Point')
    #ax.legend()

    ## Show plot
    #plt.show()


test()

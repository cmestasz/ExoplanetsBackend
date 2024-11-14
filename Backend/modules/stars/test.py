import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from astroquery.gaia import Gaia
from models import Star


def celestial_to_cartesian(ra, dec, distance):
    # Convert everything to radians
    ra_rad = np.radians(ra)
    dec_rad = np.radians(dec)

    # Calculate Cartesian coordinates
    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)

    avg_x = np.mean(x)
    avg_y = np.mean(y)
    avg_z = np.mean(z)

    # Subtract center star's coordinates to center the system
    # x -= avg_x    
    # y -= avg_y
    # z -= avg_z

    return x, y, z


def load_around_position(
    ra, dec, dist, plusminus=20, magLimit=6.5, searchRadius=360
) -> list[Star]:
    print(f"RA: {ra}, DEC: {dec}, DIST: {dist}")

    if ra < 0 or ra > 360 or dec < -90 or dec > 90 or dist < 0:
        print("nuh uh not doing it")
        return []

    upperBound = dist + plusminus
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

    job = Gaia.launch_job_async(query)
    results = job.get_results()
    print(f"We got {len(results)}")

    ra_list = results["ra"]
    dec_list = results["dec"]
    designation_list = results["DESIGNATION"]
    dist_list = results["distance_gspphot"]
    x, y, z = celestial_to_cartesian(ra_list, dec_list, dist_list)
    sector = []
    for i in range(len(designation_list)):
        sector.append(
            Star(x=str(x[i]), y=str(y[i]), z=str(z[i]), name=designation_list[i])
        )

    plot_stars_in_3d(x, y, z)
    
    return sector


def plot_stars_in_3d(x, y, z):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(x, y, z, c="white", s=1)

    # Set axis labels
    ax.set_xlabel("X (pc)")
    ax.set_ylabel("Y (pc)")
    ax.set_zlabel("Z (pc)")

    # Optional: customize the plot for better visualization
    ax.set_facecolor("black")
    ax.grid(False)
    ax.set_title("3D Star Positions")

    plt.show()


load_around_position(53.6511231, 20.5990205, 179.461)

# anomalies
# maybe a huge exoplanet: 53.6511231, 20.5990205, 179.461

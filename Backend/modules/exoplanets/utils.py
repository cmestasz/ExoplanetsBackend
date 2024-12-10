def parse_ra_to_degrees(ra_string):
    parts = ra_string.replace("h", " ").replace("m", " ").replace("s", "").split()
    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    
    return (hours * 15) + (minutes * 15 / 60) + (seconds * 15 / 3600)

def parse_dec_to_degrees(dec_string):
    parts = dec_string.replace("d", " ").replace("m", " ").replace("s", "").split()
    degrees = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    
    sign = -1 if degrees < 0 else 1
    return sign * (abs(degrees) + (minutes / 60) + (seconds / 3600))
from math import radians, cos, sin, asin, sqrt


def is_within_radius(self, lat2, lon2, center_lat=31.473664, center_lon=74.3440384, radius_meters=360):
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [center_lat, center_lon, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of Earth in meters

    distance = r * c
    return distance <= radius_meters


print(is_within_radius(31.4758742, 74.3425123))
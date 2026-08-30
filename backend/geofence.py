import math

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in meters between two points 
    on the earth specified in decimal degrees.
    """
    # Earth radius in meters
    R = 6371000.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return round(distance, 2)

def verify_geofence(farmer_lat: float, farmer_lon: float, mandi_lat: float, mandi_lon: float, threshold_meters: float = 500.0):
    """
    Checks if the farmer is within the specified distance threshold (default: 500m) of the Mandi gate.
    """
    distance = haversine_distance(farmer_lat, farmer_lon, mandi_lat, mandi_lon)
    is_valid = distance <= threshold_meters
    return {
        "distance_meters": distance,
        "is_within_geofence": is_valid,
        "threshold_meters": threshold_meters,
        "message": "Token Activated! Welcome to Mandi." if is_valid else f"You are {round(distance - threshold_meters, 1)}m outside the 500m geofence perimeter."
    }

if __name__ == "__main__":
    # Test case: Mandi at (18.5204, 73.8567) Pune Mandi
    # Farmer at (18.5220, 73.8575) -> ~200m away
    result = verify_geofence(18.5220, 73.8575, 18.5204, 73.8567)
    print("Geofence test result:", result)

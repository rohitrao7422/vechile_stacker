import math
from datetime import datetime

def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371.0
    lat1, lng1 = math.radians(lat1), math.radians(lng1)
    lat2, lng2 = math.radians(lat2), math.radians(lng2)
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

previous_location = {
    "lat": None,
    "lng": None,
    "timestamp": None
}

def check_spoofing(new_lat, new_lng):
    global previous_location

    # Pehli baar — koi check nahi
    if previous_location["lat"] is None:
        previous_location = {
            "lat": new_lat,
            "lng": new_lng,
            "timestamp": datetime.now()
        }
        return False, "First location — no check"

    # Time difference nikalo
    time_diff = (datetime.now() - previous_location["timestamp"]).total_seconds()

    # 2 sec se kam — skip karo
    if time_diff < 2:
        previous_location = {
            "lat": new_lat,
            "lng": new_lng,
            "timestamp": datetime.now()
        }
        return False, "Safe"

    # Distance nikalo
    distance_km = calculate_distance(
        previous_location["lat"],
        previous_location["lng"],
        new_lat,
        new_lng
    )

    # Speed calculate karo
    if time_diff > 0:
        speed_kmh = (distance_km / time_diff) * 3600
    else:
        speed_kmh = 0

    print(f"Distance: {distance_km:.3f} km")
    print(f"Time: {time_diff:.1f} sec")
    print(f"Calculated Speed: {speed_kmh:.1f} km/h")

    # Check 1: Speed physically impossible
    if speed_kmh > 200:
        previous_location = {
            "lat": new_lat,
            "lng": new_lng,
            "timestamp": datetime.now()
        }
        return True, f"SPOOFING: Speed {speed_kmh:.1f} km/h — physically impossible"

    # Check 2: Location jump
    if distance_km > 10:
        previous_location = {
            "lat": new_lat,
            "lng": new_lng,
            "timestamp": datetime.now()
        }
        return True, f"SPOOFING: Location jumped {distance_km:.1f} km instantly"

    # Check 3: Safe
    previous_location = {
        "lat": new_lat,
        "lng": new_lng,
        "timestamp": datetime.now()
    }
    return False, f"Safe — Speed: {speed_kmh:.1f} km/h"


def get_previous_location():
    return previous_location
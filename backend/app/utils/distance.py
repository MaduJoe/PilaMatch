"""Distance calculation utilities for hyper-local matching."""
import math
from typing import Optional


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Calculate distance between two points in kilometers using Haversine formula.

    Args:
        lat1: Latitude of the first point in degrees.
        lon1: Longitude of the first point in degrees.
        lat2: Latitude of the second point in degrees.
        lon2: Longitude of the second point in degrees.

    Returns:
        Distance in kilometers.
    """
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def estimate_travel_time(distance_km: float) -> int:
    """Estimate travel time in minutes based on distance.

    Uses average urban speed of ~20 km/h (Seoul traffic).

    Args:
        distance_km: Distance in kilometers.

    Returns:
        Estimated travel time in minutes.
    """
    if distance_km <= 0:
        return 0
    # Average urban speed ~20 km/h in Seoul
    return max(1, round(distance_km / 20 * 60))


def format_distance(distance_km: float) -> str:
    """Format distance for display.

    Args:
        distance_km: Distance in kilometers.

    Returns:
        Formatted string like "1.2km" or "800m".
    """
    if distance_km < 1:
        return f"{int(distance_km * 1000)}m"
    return f"{distance_km:.1f}km"

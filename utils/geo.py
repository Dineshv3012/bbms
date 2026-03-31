"""Geolocation utilities for donor locator.

Uses Haversine formula for distance calculation between coordinates.
"""
import math
from models import Donor


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on Earth.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (in degrees)
        lat2, lon2: Latitude and longitude of point 2 (in degrees)

    Returns:
        float: Distance in kilometers
    """
    earth_radius = 6371  # Earth's radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def find_nearby_donors(blood_group=None, lat=None, lon=None, radius_km=50, limit=20):
    """Find donors near the given coordinates, optionally filtered by blood group.

    Args:
        blood_group: Filter by blood group (None for all)
        lat: Center latitude
        lon: Center longitude
        radius_km: Search radius in kilometers
        limit: Maximum number of results

    Returns:
        list[dict]: Donors sorted by distance, each with distance_km added
    """
    query = Donor.query.filter(
        Donor.latitude.isnot(None),
        Donor.longitude.isnot(None)
    )

    if blood_group:
        query = query.filter_by(blood_group=blood_group)

    donors = query.all()
    results = []

    for donor in donors:
        if lat is not None and lon is not None:
            dist = haversine(lat, lon, donor.latitude, donor.longitude)
            if dist <= radius_km:
                results.append({
                    'id': donor.id,
                    'name': donor.name,
                    'blood_group': donor.blood_group,
                    'contact': donor.contact,
                    'email': donor.email or '',
                    'address': donor.address or '',
                    'latitude': donor.latitude,
                    'longitude': donor.longitude,
                    'distance_km': round(dist, 1),
                    'last_donation': donor.last_donation_date.strftime('%b %d, %Y') if donor.last_donation_date else 'N/A'
                })
        else:
            results.append({
                'id': donor.id,
                'name': donor.name,
                'blood_group': donor.blood_group,
                'contact': donor.contact,
                'email': donor.email or '',
                'address': donor.address or '',
                'latitude': donor.latitude,
                'longitude': donor.longitude,
                'distance_km': 0,
                'last_donation': donor.last_donation_date.strftime('%b %d, %Y') if donor.last_donation_date else 'N/A'
            })

    # Sort by distance
    results.sort(key=lambda d: d['distance_km'])
    return results[:limit]


def get_all_donor_locations(blood_group=None):
    """Get all donors with valid coordinates for map display.

    Args:
        blood_group: Optional filter by blood group

    Returns:
        list[dict]: All donors with lat/lng
    """
    query = Donor.query.filter(
        Donor.latitude.isnot(None),
        Donor.longitude.isnot(None)
    )

    if blood_group:
        query = query.filter_by(blood_group=blood_group)

    donors = query.all()
    return [{
        'id': d.id,
        'name': d.name,
        'blood_group': d.blood_group,
        'contact': d.contact,
        'address': d.address or '',
        'latitude': d.latitude,
        'longitude': d.longitude,
        'last_donation': d.last_donation_date.strftime('%b %d, %Y') if d.last_donation_date else 'N/A'
    } for d in donors]

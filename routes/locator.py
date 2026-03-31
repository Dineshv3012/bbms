from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from utils.geo import find_nearby_donors, get_all_donor_locations
from models import BLOOD_GROUPS

locator_bp = Blueprint('locator', __name__)

@locator_bp.route('/locator')
@login_required
def index():
    return render_template('locator.html', blood_groups=BLOOD_GROUPS)

@locator_bp.route('/api/nearby-donors')
@login_required
def nearby_donors_api():
    blood_group = request.args.get('blood_group')
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', 50, type=float)
    donors = find_nearby_donors(blood_group=blood_group, lat=lat, lon=lon, radius_km=radius)
    return jsonify(donors)
@locator_bp.route('/api/all-donor-locations')
@login_required
def all_donor_locations_api():
    blood_group = request.args.get('blood_group')
    locations = get_all_donor_locations(blood_group=blood_group)
    return jsonify(locations)

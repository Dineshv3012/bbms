from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from sqlalchemy import func, extract
from models import db, Donor, BloodInventory, BloodRequest
from utils.alerts import get_all_alerts, get_eligible_donors_count
from utils.prediction import get_shortage_alerts

dashboard_bp = Blueprint('dashboard', __name__)


def get_blood_group_distribution_data():
    """
    Returns the data for the blood group distribution chart.
    """
    inventory = BloodInventory.query.all()
    bg_labels = [i.blood_group for i in inventory]
    bg_values = [i.units_available for i in inventory]
    return bg_labels, bg_values


def get_monthly_registrations_data():
    """
    Returns the data for the monthly registrations chart.
    """
    now = datetime.now(timezone.utc)
    monthly_labels = []
    monthly_values = []
    for i in range(5, -1, -1):
        dt = now - timedelta(days=30 * i)
        month_name = dt.strftime('%b %Y')
        count = Donor.query.filter(
            extract('month', Donor.created_at) == dt.month,
            extract('year', Donor.created_at) == dt.year
        ).count()
        monthly_labels.append(month_name)
        monthly_values.append(count)
    return monthly_labels, monthly_values


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """
    Renders the dashboard page.
    """
    total_units = db.session.query(func.sum(BloodInventory.units_available)).scalar() or 0
    total_donors = Donor.query.count()
    total_requests = BloodRequest.query.count()
    low_stock = BloodInventory.query.filter(BloodInventory.units_available <= 5).count()
    eligible_donors = get_eligible_donors_count()
    
    prediction_alerts = [a for a in get_shortage_alerts() if a['risk_level'] == 'critical' and a['predicted_demand'] > 0]
    recent_donors = Donor.query.order_by(Donor.created_at.desc()).limit(10).all()
    pending_requests = BloodRequest.query.filter_by(status='pending').order_by(
        BloodRequest.created_at.desc()).limit(10).all()

    bg_labels, bg_values = get_blood_group_distribution_data()
    monthly_labels, monthly_values = get_monthly_registrations_data()

    return render_template('dashboard.html',
                           total_units=total_units,
                           total_donors=total_donors,
                           total_requests=total_requests,
                           low_stock=low_stock,
                           eligible_donors=eligible_donors,
                           prediction_alerts=prediction_alerts,
                           recent_donors=recent_donors,
                           pending_requests=pending_requests,
                           bg_labels=bg_labels,
                           bg_values=bg_values,
                           monthly_labels=monthly_labels,
                           monthly_values=monthly_values)


@dashboard_bp.route('/api/search')
@login_required
def global_search():
    """
    Performs a global search for donors and requests.
    """
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    results = []
    donors = Donor.query.filter(
        Donor.name.ilike(f'%{q}%') | Donor.blood_group.ilike(f'%{q}%')
    ).limit(5).all()
    for d in donors:
        results.append({'type': 'donor', 'name': d.name, 'detail': d.blood_group,
                        'url': '/donors'})

    requests_found = BloodRequest.query.filter(
        BloodRequest.patient_name.ilike(f'%{q}%')
    ).limit(5).all()
    for r in requests_found:
        results.append({'type': 'request', 'name': r.patient_name,
                        'detail': f'{r.blood_group} - {r.status}', 'url': '/requests'})

    return jsonify(results)


@dashboard_bp.route('/api/notifications')
@login_required
def notifications():
    """
    Returns all notifications.
    """
    alerts = get_all_alerts()
    return jsonify({'count': len(alerts), 'items': alerts})

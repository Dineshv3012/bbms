"""Smart Alert & Notification System.

Aggregates alerts from multiple sources: inventory, predictions,
donor eligibility, and urgent requests.
"""
from datetime import datetime, timezone, timedelta
from models import Donor, BloodInventory, BloodRequest
from utils.prediction import get_shortage_alerts


def get_all_alerts():
    """Aggregate alerts from all sources.

    Returns:
        list[dict]: Each alert has: type, severity, message, icon, action_url
    """
    alerts = []

    # --- 1. Low Stock Alerts ---
    low_stock = BloodInventory.query.filter(BloodInventory.units_available <= 5).all()
    for inv in low_stock:
        if inv.units_available <= 2:
            severity = 'critical'
            icon = '🔴'
        else:
            severity = 'warning'
            icon = '🟡'
        alerts.append({
            'type': 'low_stock',
            'severity': severity,
            'message': f'{inv.blood_group} stock is {inv.status} ({inv.units_available} units)',
            'icon': icon,
            'action_url': '/inventory'
        })

    # --- 2. Predicted Shortage Alerts ---
    try:
        shortage_alerts = get_shortage_alerts()
        for sa in shortage_alerts:
            if sa['risk_level'] == 'critical' and sa['predicted_demand'] > 0:
                alerts.append({
                    'type': 'prediction',
                    'severity': 'critical',
                    'message': f'{sa["blood_group"]} predicted to run low in ~{sa["days_until_shortage"]:.0f} days (demand: {sa["predicted_demand"]} units)',
                    'icon': '🧠',
                    'action_url': '/analytics'
                })
            elif sa['risk_level'] == 'warning' and sa['predicted_demand'] > 0:
                alerts.append({
                    'type': 'prediction',
                    'severity': 'warning',
                    'message': f'{sa["blood_group"]} demand is {sa["trend"]} — monitor closely',
                    'icon': '📈',
                    'action_url': '/analytics'
                })
    except ImportError:
        pass  # Graceful fallback if prediction module isn't ready

    # --- 3. Donor Eligibility Reminders ---
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=56)).date()
    eligible_donors = Donor.query.filter(
        Donor.last_donation_date <= cutoff_date
    ).count()
    if eligible_donors > 0:
        alerts.append({
            'type': 'donor_eligible',
            'severity': 'info',
            'message': f'{eligible_donors} donor(s) are eligible to donate again',
            'icon': '💉',
            'action_url': '/donors'
        })

    # --- 4. Urgent/Critical Pending Requests ---
    urgent_pending = BloodRequest.query.filter(
        BloodRequest.status == 'pending',
        BloodRequest.urgency.in_(['urgent', 'critical'])
    ).count()
    if urgent_pending > 0:
        alerts.append({
            'type': 'urgent_request',
            'severity': 'critical',
            'message': f'{urgent_pending} urgent/critical request(s) awaiting review',
            'icon': '🚨',
            'action_url': '/requests'
        })

    # --- 5. Regular Pending Requests ---
    normal_pending = BloodRequest.query.filter_by(status='pending').count() - urgent_pending
    if normal_pending > 0:
        alerts.append({
            'type': 'pending_request',
            'severity': 'info',
            'message': f'{normal_pending} pending request(s) awaiting review',
            'icon': '📋',
            'action_url': '/requests'
        })

    # Sort: critical first, then warning, then info
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    alerts.sort(key=lambda a: severity_order.get(a['severity'], 3))

    return alerts

def get_eligible_donors_count():
    """Count donors who are eligible to donate again (56+ days since last donation)."""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=56)).date()
    return Donor.query.filter(
        Donor.last_donation_date <= cutoff_date
    ).count()

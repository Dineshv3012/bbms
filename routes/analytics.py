from flask import Blueprint, render_template
from flask_login import login_required
from utils.prediction import get_demand_trends, get_shortage_alerts

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    trends = get_demand_trends()
    shortage_alerts = get_shortage_alerts()
    
    # Calculate some summary stats for the analytics page
    critical_count = sum(1 for a in shortage_alerts if a['risk_level'] == 'critical')
    warning_count = sum(1 for a in shortage_alerts if a['risk_level'] == 'warning')
    
    return render_template('analytics.html', 
                           trends=trends, 
                           shortage_alerts=shortage_alerts,
                           critical_count=critical_count,
                           warning_count=warning_count)

"""Smart Blood Demand Prediction Engine.

Uses numpy-based linear regression on historical request data
to forecast future blood demand per blood group.
"""
from datetime import datetime, timezone, timedelta
import numpy as np
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError
from models import db, BloodRequest, BloodInventory, BLOOD_GROUPS, AnalyticsAlert


def _get_weekly_demand(blood_group, weeks_back=12):
    """Get weekly demand counts for a blood group over the past N weeks."""
    now = datetime.now(timezone.utc)
    weekly_counts = []

    for i in range(weeks_back, 0, -1):
        week_start = now - timedelta(weeks=i)
        week_end = now - timedelta(weeks=i - 1)
        res = BloodRequest.query.filter(
            and_(
                BloodRequest.blood_group == blood_group,
                BloodRequest.created_at >= week_start,
                BloodRequest.created_at < week_end,
                BloodRequest.status.in_(['approved', 'pending'])
            )
        ).with_entities(func.coalesce(func.sum(BloodRequest.units_required), 0)).scalar()
        
        count = int(res) if res is not None else 0
        weekly_counts.append(count)

    return weekly_counts


def _linear_regression(x, y):
    """
    Calculates the linear regression of y on x.
    Returns slope, intercept, and r-squared.
    """
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)

    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        slope = 0
        intercept = np.mean(y)
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

    # Calculate R-squared for confidence
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = max(0, 1 - (ss_res / ss_tot)) if ss_tot > 0 else 0

    return slope, intercept, r_squared


def predict_demand(blood_group, days_ahead=7):
    """Predict demand for a blood group over the next N days using linear regression.

    Returns:
        dict: {
            'blood_group': str,
            'predicted_units': float,
            'trend': 'rising' | 'falling' | 'stable',
            'confidence': float (0-1),
            'weekly_history': list[int]
        }
    """
    weekly_data = _get_weekly_demand(blood_group, weeks_back=12)

    if not any(weekly_data):
        return {
            'blood_group': blood_group,
            'predicted_units': 0,
            'trend': 'stable',
            'confidence': 0.0,
            'weekly_history': weekly_data
        }

    # Linear regression using numpy
    x = np.arange(len(weekly_data), dtype=float)
    y = np.array(weekly_data, dtype=float)

    slope, intercept, r_squared = _linear_regression(x, y)

    # Predict for next period (convert days to weeks fraction)
    future_x = len(x) + (days_ahead / 7.0)
    predicted = max(0, slope * future_x + intercept)

    # Determine trend
    if slope > 0.3:
        trend = 'rising'
    elif slope < -0.3:
        trend = 'falling'
    else:
        trend = 'stable'

    return {
        'blood_group': blood_group,
        'predicted_units': round(predicted, 1),
        'trend': trend,
        'confidence': round(r_squared, 2),
        'weekly_history': weekly_data,
        'slope': round(slope, 3)
    }


def _calculate_risk(current_stock, predicted_demand):
    """
    Calculates the risk level and the number of days until shortage.
    """
    if current_stock <= 0:
        risk = 'critical'
        days_left = 0
    elif predicted_demand > 0 and current_stock > 0:
        # Estimate days until shortage
        daily_rate = predicted_demand / 7.0
        days_left = round(current_stock / daily_rate, 1) if daily_rate > 0 else 999
        if days_left <= 3:
            risk = 'critical'
        elif days_left <= 7:
            risk = 'warning'
        else:
            risk = 'safe'
    else:
        risk = 'safe'
        days_left = 999
    return risk, days_left


def get_shortage_alerts():
    """Compare predicted demand against current inventory to find shortage risks.

    Returns:
        list[dict]: Each alert has: blood_group, current_stock, predicted_demand,
                    risk_level ('critical'|'warning'|'safe'), days_until_shortage
    """
    alerts = []

    for bg in BLOOD_GROUPS:
        inv = BloodInventory.query.filter_by(blood_group=bg).first()
        current_stock = inv.units_available if inv else 0

        prediction = predict_demand(bg, days_ahead=7)
        predicted = prediction['predicted_units']

        risk, days_left = _calculate_risk(current_stock, predicted)

        alerts.append({
            'blood_group': bg,
            'current_stock': current_stock,
            'predicted_demand': predicted,
            'trend': prediction['trend'],
            'risk_level': risk,
            'days_until_shortage': min(days_left, 999),
            'confidence': prediction['confidence']
        })

    # Sort by risk (critical first)
    risk_order = {'critical': 0, 'warning': 1, 'safe': 2}
    alerts.sort(key=lambda a: (risk_order.get(a['risk_level'], 3), -a['predicted_demand']))

    # Store the results persistently to ensure we 'store all data in website'
    try:
        for alert in alerts:
            # Check if we already added a similar alert for this group in the last 6 hours to avoid redundancy
            six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6)
            existing = AnalyticsAlert.query.filter(
                AnalyticsAlert.blood_group == alert['blood_group'],
                AnalyticsAlert.timestamp >= six_hours_ago
            ).first()
            
            if not existing:
                new_record = AnalyticsAlert(
                    blood_group=alert['blood_group'],
                    current_stock=alert['current_stock'],
                    predicted_demand=alert['predicted_demand'],
                    risk_level=alert['risk_level'],
                    days_until_shortage=alert['days_until_shortage']
                )
                db.session.add(new_record)
        
        db.session.commit()
    except SQLAlchemyError as e:
        print(f"Persistence error: {e}")
        db.session.rollback()

    return alerts


def get_demand_trends():
    """Get demand trend data for all blood groups (for charting).

    Returns:
        dict: {
            'labels': list[str] (week labels),
            'datasets': list[dict] (per blood group with history + forecast)
        }
    """
    now = datetime.now(timezone.utc)
    labels = []
    for i in range(12, 0, -1):
        dt = now - timedelta(weeks=i)
        labels.append(dt.strftime('%b %d'))
    labels.append('Next 7d')

    colors = {
        'A+': '#dc2626', 'A-': '#ef4444',
        'B+': '#2563eb', 'B-': '#3b82f6',
        'AB+': '#7c3aed', 'AB-': '#8b5cf6',
        'O+': '#059669', 'O-': '#10b981'
    }

    datasets = []
    for bg in BLOOD_GROUPS:
        prediction = predict_demand(bg, days_ahead=7)
        history = prediction['weekly_history']
        forecast = prediction['predicted_units']

        datasets.append({
            'label': bg,
            'data': history + [forecast],
            'borderColor': colors.get(bg, '#6b7280'),
            'backgroundColor': colors.get(bg, '#6b7280') + '20',
            'tension': 0.4,
            'pointRadius': 3,
            'borderWidth': 2
        })

    return {'labels': labels, 'datasets': datasets}

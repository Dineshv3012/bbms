import csv
import io
from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from models import AuditLog

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/logs')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))

    logs = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=25, error_out=False)

    action_types = [r[0] for r in
                    AuditLog.query.with_entities(AuditLog.action).distinct().all()]

    return render_template('logs.html', logs=logs, action_types=action_types,
                           action_filter=action_filter)


@logs_bp.route('/logs/export')
@login_required
def export():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'User', 'Action', 'Details', 'Timestamp'])
    for log in logs:
        writer.writerow([
            log.id,
            log.user.username if log.user else 'System',
            log.action,
            log.details or '',
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=audit_logs.csv'}
    )

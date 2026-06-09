"""
Export Module: CSV export for Donors, Blood Requests, Inventory, and Audit Logs.
No extra dependencies needed — uses Python's built-in csv module.
"""
import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, make_response, request, jsonify
from flask_login import login_required, current_user
from models import db, Donor, BloodRequest, BloodInventory, AuditLog, BLOOD_GROUPS
from utils.audit import log_action

export_bp = Blueprint('export', __name__)


def _csv_response(filename, headers, rows):
    """Helper: build a CSV HTTP response."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


@export_bp.route('/export/donors')
@login_required
def export_donors():
    """Export all donors to CSV with optional blood_group filter."""
    blood_group = request.args.get('blood_group', '').strip()
    query = Donor.query
    if blood_group and blood_group in BLOOD_GROUPS:
        query = query.filter_by(blood_group=blood_group)
    donors = query.order_by(Donor.name).all()

    headers = ['ID', 'Name', 'Blood Group', 'Contact', 'Email', 'Address',
               'Last Donation Date', 'Eligible to Donate', 'Registered At']
    rows = []
    cutoff = (datetime.now(timezone.utc).date())
    from datetime import timedelta
    eligibility_cutoff = (datetime.now(timezone.utc) - timedelta(days=56)).date()

    for d in donors:
        eligible = 'Yes' if (d.last_donation_date is None or d.last_donation_date <= eligibility_cutoff) else 'No'
        rows.append([
            d.id, d.name, d.blood_group, d.contact, d.email or '',
            d.address or '',
            d.last_donation_date.strftime('%Y-%m-%d') if d.last_donation_date else 'Never',
            eligible,
            d.created_at.strftime('%Y-%m-%d %H:%M') if d.created_at else ''
        ])

    log_action('EXPORT_DONORS', f'Exported {len(rows)} donor records to CSV')
    fname = f'donors_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    return _csv_response(fname, headers, rows)


@export_bp.route('/export/requests')
@login_required
def export_requests():
    """Export blood requests to CSV with optional status filter."""
    status = request.args.get('status', '').strip()
    query = BloodRequest.query
    if status:
        query = query.filter_by(status=status)
    reqs = query.order_by(BloodRequest.created_at.desc()).all()

    headers = ['ID', 'Patient Name', 'Blood Group', 'Units Required',
               'Urgency', 'Status', 'Requested By', 'Approved By', 'Created At', 'Updated At']
    rows = []
    for r in reqs:
        rows.append([
            r.id, r.patient_name, r.blood_group, r.units_required,
            r.urgency, r.status,
            r.requester.username if r.requester else '',
            r.approver.username if r.approver else '',
            r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else '',
            r.updated_at.strftime('%Y-%m-%d %H:%M') if r.updated_at else '',
        ])

    log_action('EXPORT_REQUESTS', f'Exported {len(rows)} request records to CSV')
    fname = f'requests_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    return _csv_response(fname, headers, rows)


@export_bp.route('/export/inventory')
@login_required
def export_inventory():
    """Export blood inventory snapshot to CSV."""
    inventory = BloodInventory.query.order_by(BloodInventory.blood_group).all()
    headers = ['Blood Group', 'Units Available', 'Status', 'Managed By', 'Last Updated']
    rows = []
    for inv in inventory:
        rows.append([
            inv.blood_group, inv.units_available, inv.status,
            inv.manager.username if inv.manager else '',
            inv.last_updated.strftime('%Y-%m-%d %H:%M') if inv.last_updated else ''
        ])
    log_action('EXPORT_INVENTORY', 'Exported inventory snapshot to CSV')
    fname = f'inventory_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    return _csv_response(fname, headers, rows)


@export_bp.route('/export/audit')
@login_required
def export_audit():
    """Export audit logs to CSV (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5000).all()
    headers = ['ID', 'User', 'Action', 'Details', 'Timestamp']
    rows = []
    for lg in logs:
        rows.append([
            lg.id,
            lg.user.username if lg.user else 'System',
            lg.action, lg.details or '',
            lg.timestamp.strftime('%Y-%m-%d %H:%M:%S') if lg.timestamp else ''
        ])
    log_action('EXPORT_AUDIT', f'Exported {len(rows)} audit log records')
    fname = f'audit_logs_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    return _csv_response(fname, headers, rows)


@export_bp.route('/export/eligible-donors')
@login_required
def export_eligible_donors():
    """Export donors eligible to donate right now."""
    from datetime import timedelta
    eligibility_cutoff = (datetime.now(timezone.utc) - timedelta(days=56)).date()
    donors = Donor.query.filter(
        (Donor.last_donation_date == None) | (Donor.last_donation_date <= eligibility_cutoff)
    ).order_by(Donor.blood_group, Donor.name).all()

    headers = ['Name', 'Blood Group', 'Contact', 'Email', 'Last Donation', 'Days Since Donation']
    rows = []
    today = datetime.now(timezone.utc).date()
    for d in donors:
        if d.last_donation_date:
            days_ago = (today - d.last_donation_date).days
        else:
            days_ago = 'Never donated'
        rows.append([
            d.name, d.blood_group, d.contact, d.email or '',
            d.last_donation_date.strftime('%Y-%m-%d') if d.last_donation_date else 'Never',
            days_ago
        ])

    log_action('EXPORT_ELIGIBLE', f'Exported {len(rows)} eligible donors')
    fname = f'eligible_donors_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    return _csv_response(fname, headers, rows)

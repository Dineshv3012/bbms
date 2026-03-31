from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, BloodRequest, BloodInventory, BLOOD_GROUPS
from utils.audit import log_action

requests_bp = Blueprint('requests', __name__)


@requests_bp.route('/requests')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '').strip()

    query = BloodRequest.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    blood_requests = query.order_by(BloodRequest.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False)
    return render_template('requests.html', requests=blood_requests,
                           blood_groups=BLOOD_GROUPS, status_filter=status_filter)


@requests_bp.route('/requests/add', methods=['POST'])
@login_required
def add():
    patient_name = request.form.get('patient_name', '').strip()
    blood_group = request.form.get('blood_group', '').strip()
    units = request.form.get('units_required', 1, type=int)
    urgency = request.form.get('urgency', 'normal').strip()

    if not patient_name or not blood_group:
        flash('Patient name and blood group are required.', 'error')
        return redirect(url_for('requests.index'))

    br = BloodRequest(
        patient_name=patient_name,
        blood_group=blood_group,
        units_required=units,
        urgency=urgency,
        requested_by=current_user.id
    )
    db.session.add(br)
    db.session.commit()
    log_action('ADD_REQUEST', f'Blood request for {patient_name}: {units} units of {blood_group}')
    flash('Blood request submitted!', 'success')
    return redirect(url_for('requests.index'))


@requests_bp.route('/requests/<int:req_id>/approve', methods=['POST'])
@login_required
def approve(req_id):
    br = BloodRequest.query.get_or_404(req_id)
    if br.status != 'pending':
        flash('This request has already been processed.', 'error')
        return redirect(url_for('requests.index'))

    # Check inventory
    inv = BloodInventory.query.filter_by(blood_group=br.blood_group).first()
    if not inv or inv.units_available < br.units_required:
        flash(f'Insufficient {br.blood_group} stock to approve this request.', 'error')
        return redirect(url_for('requests.index'))

    # Deduct from inventory
    inv.units_available -= br.units_required
    br.status = 'approved'
    br.approved_by = current_user.id
    db.session.commit()
    log_action('APPROVE_REQUEST',
               f'Approved request #{br.id} for {br.patient_name}: '
               f'{br.units_required} units of {br.blood_group}')
    flash(f'Request for {br.patient_name} approved! Inventory updated.', 'success')
    return redirect(url_for('requests.index'))


@requests_bp.route('/requests/<int:req_id>/reject', methods=['POST'])
@login_required
def reject(req_id):
    br = BloodRequest.query.get_or_404(req_id)
    if br.status != 'pending':
        flash('This request has already been processed.', 'error')
        return redirect(url_for('requests.index'))

    br.status = 'rejected'
    br.approved_by = current_user.id
    db.session.commit()
    log_action('REJECT_REQUEST',
               f'Rejected request #{br.id} for {br.patient_name}')
    flash(f'Request for {br.patient_name} rejected.', 'success')
    return redirect(url_for('requests.index'))

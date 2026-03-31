import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from models import db, Donor, BLOOD_GROUPS
from utils.audit import log_action

donors_bp = Blueprint('donors', __name__)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@donors_bp.route('/donors')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    blood_group = request.args.get('blood_group', '').strip()

    query = Donor.query
    if search:
        query = query.filter(Donor.name.ilike(f'%{search}%') | Donor.contact.ilike(f'%{search}%'))
    if blood_group:
        query = query.filter_by(blood_group=blood_group)

    donors = query.order_by(Donor.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('donors.html', donors=donors, blood_groups=BLOOD_GROUPS,
                           search=search, selected_group=blood_group)


@donors_bp.route('/donors/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name', '').strip()
    blood_group = request.form.get('blood_group', '').strip()
    contact = request.form.get('contact', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    last_donation = request.form.get('last_donation_date')

    if not name or not blood_group or not contact:
        flash('Name, blood group, and contact are required.', 'error')
        return redirect(url_for('donors.index'))

    donor = Donor(name=name, blood_group=blood_group, contact=contact,
                  email=email or None, address=address or None,
                  latitude=float(latitude) if latitude else None,
                  longitude=float(longitude) if longitude else None)
    if last_donation:
        try:
            donor.last_donation_date = datetime.strptime(last_donation, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Handle file upload
    if 'id_proof' in request.files:
        file = request.files['id_proof']
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(f"donor_{contact}_{file.filename}")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            donor.id_proof_path = filename

    db.session.add(donor)
    db.session.commit()
    log_action('ADD_DONOR', f'Added donor: {name} ({blood_group})')
    flash(f'Donor {name} added successfully!', 'success')
    return redirect(url_for('donors.index'))


@donors_bp.route('/donors/<int:donor_id>/edit', methods=['POST'])
@login_required
def edit(donor_id):
    donor = Donor.query.get_or_404(donor_id)
    donor.name = request.form.get('name', donor.name).strip()
    donor.blood_group = request.form.get('blood_group', donor.blood_group).strip()
    donor.contact = request.form.get('contact', donor.contact).strip()
    donor.email = request.form.get('email', '').strip() or None
    donor.address = request.form.get('address', '').strip() or None
    
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    if latitude:
        donor.latitude = float(latitude)
    if longitude:
        donor.longitude = float(longitude)

    last_donation = request.form.get('last_donation_date')
    if last_donation:
        try:
            donor.last_donation_date = datetime.strptime(last_donation, '%Y-%m-%d').date()
        except ValueError:
            pass

    if 'id_proof' in request.files:
        file = request.files['id_proof']
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(f"donor_{donor.contact}_{file.filename}")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            donor.id_proof_path = filename

    db.session.commit()
    log_action('EDIT_DONOR', f'Edited donor: {donor.name} ({donor.blood_group})')
    flash(f'Donor {donor.name} updated successfully!', 'success')
    return redirect(url_for('donors.index'))


@donors_bp.route('/donors/<int:donor_id>/delete', methods=['POST'])
@login_required
def delete(donor_id):
    donor = Donor.query.get_or_404(donor_id)
    name = donor.name
    db.session.delete(donor)
    db.session.commit()
    log_action('DELETE_DONOR', f'Deleted donor: {name}')
    flash(f'Donor {name} deleted.', 'success')
    return redirect(url_for('donors.index'))

import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
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


@donors_bp.route('/donors/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Bulk delete donors by ID list."""
    ids = request.json.get('ids', []) if request.is_json else request.form.getlist('ids')
    if not ids:
        if request.is_json:
            return jsonify({'error': 'No IDs provided'}), 400
        flash('No donors selected.', 'error')
        return redirect(url_for('donors.index'))

    deleted = Donor.query.filter(Donor.id.in_(ids)).all()
    count = len(deleted)
    for d in deleted:
        db.session.delete(d)
    db.session.commit()
    log_action('BULK_DELETE_DONORS', f'Bulk deleted {count} donors: IDs {ids}')

    if request.is_json:
        return jsonify({'deleted': count})
    flash(f'Deleted {count} donor(s).', 'success')
    return redirect(url_for('donors.index'))


@donors_bp.route('/donors/<int:donor_id>/profile')
@login_required
def profile(donor_id):
    """Return donor profile as JSON for modal display."""
    from datetime import datetime, timezone, timedelta
    donor = Donor.query.get_or_404(donor_id)
    today = datetime.now(timezone.utc).date()
    eligibility_cutoff = (datetime.now(timezone.utc) - timedelta(days=56)).date()

    if donor.last_donation_date:
        days_since = (today - donor.last_donation_date).days
        eligible = days_since >= 56
    else:
        days_since = None
        eligible = True

    return jsonify({
        'id': donor.id,
        'name': donor.name,
        'blood_group': donor.blood_group,
        'contact': donor.contact,
        'email': donor.email,
        'address': donor.address,
        'last_donation_date': donor.last_donation_date.isoformat() if donor.last_donation_date else None,
        'days_since_donation': days_since,
        'eligible_to_donate': eligible,
        'id_proof_path': donor.id_proof_path,
        'created_at': donor.created_at.isoformat() if donor.created_at else None
    })


@donors_bp.route('/donors/stats')
@login_required
def stats():
    """Return donor statistics as JSON for dashboard widgets."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func
    from models import BloodInventory

    by_group = db.session.query(Donor.blood_group, func.count(Donor.id)).group_by(Donor.blood_group).all()
    eligibility_cutoff = (datetime.now(timezone.utc) - timedelta(days=56)).date()
    eligible_count = Donor.query.filter(
        (Donor.last_donation_date == None) | (Donor.last_donation_date <= eligibility_cutoff)
    ).count()

    return jsonify({
        'total': Donor.query.count(),
        'by_group': {bg: cnt for bg, cnt in by_group},
        'eligible': eligible_count,
    })


# ---- Donor Notes ----
@donors_bp.route('/donors/<int:donor_id>/notes', methods=['GET'])
@login_required
def get_notes(donor_id):
    from models import DonorNote
    Donor.query.get_or_404(donor_id)
    notes = DonorNote.query.filter_by(donor_id=donor_id).order_by(DonorNote.created_at.desc()).all()
    return jsonify([{
        'id': n.id,
        'note': n.note,
        'author': n.author.username if n.author else 'Unknown',
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M') if n.created_at else ''
    } for n in notes])


@donors_bp.route('/donors/<int:donor_id>/notes', methods=['POST'])
@login_required
def add_note(donor_id):
    from models import DonorNote
    Donor.query.get_or_404(donor_id)
    note_text = (request.json or {}).get('note', '').strip() if request.is_json else request.form.get('note', '').strip()
    if not note_text:
        return jsonify({'error': 'Note cannot be empty'}), 400
    note = DonorNote(donor_id=donor_id, note=note_text, created_by=current_user.id)
    db.session.add(note)
    db.session.commit()
    log_action('ADD_DONOR_NOTE', f'Added note to donor #{donor_id}')
    return jsonify({'id': note.id, 'note': note.note, 'author': current_user.username})


@donors_bp.route('/donors/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    from models import DonorNote
    note = DonorNote.query.get_or_404(note_id)
    if note.created_by != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403
    db.session.delete(note)
    db.session.commit()
    return jsonify({'deleted': True})

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, User
from utils.decorators import admin_required
from utils.audit import log_action

staff_bp = Blueprint('staff', __name__)


@staff_bp.route('/staff')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    staff = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False)
    return render_template('staff.html', staff=staff)


@staff_bp.route('/staff/add', methods=['POST'])
@login_required
@admin_required
def add():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'staff').strip()

    if not username or not email or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('staff.index'))

    if User.query.filter((User.email == email) | (User.username == username)).first():
        flash('Username or email already exists.', 'error')
        return redirect(url_for('staff.index'))

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    log_action('ADD_STAFF', f'Added staff: {username} ({role})')
    flash(f'Staff member {username} added!', 'success')
    return redirect(url_for('staff.index'))


@staff_bp.route('/staff/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit(user_id):
    user = User.query.get_or_404(user_id)
    user.username = request.form.get('username', user.username).strip()
    user.email = request.form.get('email', user.email).strip()
    user.role = request.form.get('role', user.role).strip()

    password = request.form.get('password', '').strip()
    if password:
        user.set_password(password)

    db.session.commit()
    log_action('EDIT_STAFF', f'Edited staff: {user.username}')
    flash(f'Staff member {user.username} updated!', 'success')
    return redirect(url_for('staff.index'))


@staff_bp.route('/staff/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_user = not user.is_active_user
    db.session.commit()
    status = 'activated' if user.is_active_user else 'deactivated'
    log_action('TOGGLE_STAFF', f'{status} staff: {user.username}')
    flash(f'{user.username} has been {status}.', 'success')
    return redirect(url_for('staff.index'))

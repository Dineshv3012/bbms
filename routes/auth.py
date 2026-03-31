"""
This module handles user authentication.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from utils.audit import log_action

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()
        
        # Auto-create admin if database is empty and this is the first admin login attempt
        if not user and email == 'admin@bbms.com':
            from models import db
            from werkzeug.security import generate_password_hash
            new_admin = User(username='admin', email='admin@bbms.com', role='admin')
            new_admin.password_hash = generate_password_hash('admin123')
            db.session.add(new_admin)
            db.session.commit()
            user = new_admin

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            log_action('LOGIN', f'{user.username} logged in')
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))

        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handles user signup.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/signup.html')

        user_exists = User.query.filter((User.email == email) | (User.username == username)).first()
        if user_exists:
            flash('Username or email already exists.', 'error')
            return render_template('auth/signup.html')

        from models import db
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        new_user.role = 'staff'  # Default role for signups
        
        try:
            db.session.add(new_user)
            db.session.commit()
            log_action('SIGNUP', f'New user {username} signed up')
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')

    return render_template('auth/signup.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Handles user logout.
    """
    log_action('LOGOUT', f'{current_user.username} logged out')
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

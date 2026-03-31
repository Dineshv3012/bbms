"""
This module initializes the Flask application and registers all the blueprints.
"""
import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.donors import donors_bp
from routes.inventory import inventory_bp
from routes.requests import requests_bp
from routes.staff import staff_bp
from routes.logs import logs_bp
from routes.analytics import analytics_bp
from routes.locator import locator_bp

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    """
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    @login_manager.user_loader
    def load_user(user_id):
        """
        Loads a user from the database.
        """
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(donors_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(locator_bp)

    # Root redirect
    @app.route('/')
    def root():
        """
        Redirects the root URL to the login page.
        """
        return redirect(url_for('auth.login'))

    # Handle common favicon paths
    @app.route('/favicon.ico')
    @app.route('/favicon.png')
    def favicon():
        """
        Suppresses 404 log warnings for common favicon paths.
        """
        return '', 204

    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Create uploads folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)

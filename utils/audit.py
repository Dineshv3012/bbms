from flask_login import current_user
from models import db, AuditLog


def log_action(action, details=None):
    """Log an action to the audit trail."""
    user_id = current_user.id if current_user and current_user.is_authenticated else None
    entry = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()

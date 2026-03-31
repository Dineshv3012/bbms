from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, BloodInventory, BLOOD_GROUPS
from utils.audit import log_action

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory')
@login_required
def index():
    inventory = BloodInventory.query.order_by(BloodInventory.blood_group).all()
    return render_template('inventory.html', inventory=inventory, blood_groups=BLOOD_GROUPS)


@inventory_bp.route('/inventory/update', methods=['POST'])
@login_required
def update():
    blood_group = request.form.get('blood_group', '').strip()
    units = request.form.get('units', 0, type=int)
    action = request.form.get('action', 'set')  # set / add / subtract

    if blood_group not in BLOOD_GROUPS:
        flash('Invalid blood group.', 'error')
        return redirect(url_for('inventory.index'))

    inv = BloodInventory.query.filter_by(blood_group=blood_group).first()
    if not inv:
        inv = BloodInventory(blood_group=blood_group, units_available=0)
        db.session.add(inv)

    old_units = inv.units_available
    if action == 'add':
        inv.units_available += units
    elif action == 'subtract':
        inv.units_available = max(0, inv.units_available - units)
    else:
        inv.units_available = max(0, units)

    inv.managed_by = current_user.id
    inv.last_updated = datetime.now(timezone.utc)
    db.session.commit()
    log_action('UPDATE_INVENTORY',
               f'{blood_group}: {old_units} → {inv.units_available} units ({action})')
    flash(f'{blood_group} inventory updated to {inv.units_available} units.', 'success')
    return redirect(url_for('inventory.index'))

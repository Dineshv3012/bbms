from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, BloodInventory, InventoryHistory, BLOOD_GROUPS
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

    # Record history
    hist = InventoryHistory(
        blood_group=blood_group,
        units_before=old_units,
        units_after=inv.units_available,
        action=action,
        changed_by=current_user.id
    )
    db.session.add(hist)
    db.session.commit()
    log_action('UPDATE_INVENTORY',
               f'{blood_group}: {old_units} → {inv.units_available} units ({action})')
    flash(f'{blood_group} inventory updated to {inv.units_available} units.', 'success')
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/inventory/history')
@login_required
def history():
    """Return last 100 inventory changes as JSON."""
    hist = InventoryHistory.query.order_by(InventoryHistory.timestamp.desc()).limit(100).all()
    return jsonify([{
        'id': h.id,
        'blood_group': h.blood_group,
        'units_before': h.units_before,
        'units_after': h.units_after,
        'change': h.units_after - h.units_before,
        'action': h.action,
        'changed_by': h.changer.username if h.changer else 'System',
        'timestamp': h.timestamp.strftime('%Y-%m-%d %H:%M') if h.timestamp else ''
    } for h in hist])


@inventory_bp.route('/inventory/summary')
@login_required
def summary():
    """Return inventory summary stats as JSON."""
    inventory = BloodInventory.query.all()
    total_units = sum(i.units_available for i in inventory)
    critical = [i.blood_group for i in inventory if i.status == 'critical']
    low = [i.blood_group for i in inventory if i.status == 'low']
    return jsonify({
        'total_units': total_units,
        'critical_groups': critical,
        'low_groups': low,
        'by_group': {i.blood_group: {'units': i.units_available, 'status': i.status} for i in inventory}
    })

import math
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from extensions import db
from models.farm import Farm
from routes.auth import login_required, role_required

farms_bp = Blueprint('farms', __name__)

@farms_bp.route('/farms')
@login_required
@role_required('FARMER')
def farms_view():
    user_id = session['user_id']
    farms = Farm.query.filter_by(user_id=user_id).order_by(Farm.created_at.desc()).all()
    return render_template('farms.html', farms=farms)

@farms_bp.route('/farms/add', methods=['POST'])
@login_required
@role_required('FARMER')
def add_farm():
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    land_area = request.form.get('land_area', '').strip()
    soil_type = request.form.get('soil_type', '').strip()
    irrigation_method = request.form.get('irrigation_method', '').strip()

    if not name or not location or not land_area or not soil_type or not irrigation_method:
        flash('All farm fields are required.', 'danger')
        return redirect(url_for('farms.farms_view'))

    try:
        area_float = float(land_area)
        if math.isnan(area_float) or math.isinf(area_float) or area_float <= 0:
            flash('Land area must be greater than zero.', 'danger')
            return redirect(url_for('farms.farms_view'))
    except (ValueError, TypeError):
        flash('Invalid numeric value for land area.', 'danger')
        return redirect(url_for('farms.farms_view'))

    new_farm = Farm(
        user_id=user_id,
        name=name,
        location=location,
        land_area=area_float,
        soil_type=soil_type,
        irrigation_method=irrigation_method
    )
    db.session.add(new_farm)
    db.session.commit()
    flash(f"Farm '{new_farm.name}' added successfully!", 'success')
    return redirect(url_for('farms.farms_view'))

@farms_bp.route('/farms/<int:id>/edit', methods=['POST'])
@login_required
@role_required('FARMER')
def edit_farm(id):
    farm = db.session.get(Farm, id)
    if not farm:
        abort(404)
    # Strict ownership check
    if farm.user_id != session['user_id']:
        abort(403)

    farm.name = request.form.get('name', farm.name).strip()
    farm.location = request.form.get('location', farm.location).strip()
    farm.soil_type = request.form.get('soil_type', farm.soil_type).strip()
    farm.irrigation_method = request.form.get('irrigation_method', farm.irrigation_method).strip()
    
    # VAL-03: Validate that updated land_area is strictly positive
    try:
        new_area = float(request.form.get('land_area', farm.land_area))
        if math.isnan(new_area) or math.isinf(new_area) or new_area <= 0:
            flash('Land area must be greater than zero.', 'danger')
            return redirect(url_for('farms.farms_view'))
        farm.land_area = new_area
    except (ValueError, TypeError):
        flash('Invalid numeric value for land area.', 'danger')
        return redirect(url_for('farms.farms_view'))

    db.session.commit()
    flash(f"Farm '{farm.name}' updated successfully.", 'success')
    return redirect(url_for('farms.farms_view'))

@farms_bp.route('/farms/<int:id>/delete', methods=['POST'])
@login_required
@role_required('FARMER')
def delete_farm(id):
    farm = db.session.get(Farm, id)
    if not farm:
        abort(404)
    if farm.user_id != session['user_id']:
        abort(403)

    name = farm.name
    db.session.delete(farm)
    db.session.commit()
    flash(f"Farm '{name}' was deleted.", 'info')
    return redirect(url_for('farms.farms_view'))

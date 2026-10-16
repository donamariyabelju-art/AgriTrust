import math
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from extensions import db
from models.crop import Crop
from models.farm import Farm
from routes.auth import login_required, role_required

crops_bp = Blueprint('crops', __name__)

@crops_bp.route('/crops')
@login_required
@role_required('FARMER')
def crops_view():
    user_id = session['user_id']
    crops = Crop.query.filter_by(user_id=user_id).order_by(Crop.created_at.desc()).all()
    farms = Farm.query.filter_by(user_id=user_id).all()
    return render_template('crops.html', crops=crops, farms=farms)

@crops_bp.route('/crops/add', methods=['POST'])
@login_required
@role_required('FARMER')
def add_crop():
    user_id = session['user_id']
    crop_name = request.form.get('crop_name', '').strip()
    farm_id = request.form.get('farm_id')
    planting_date_str = request.form.get('planting_date')
    growth_stage = request.form.get('growth_stage', 'Vegetative')
    growth_percentage = request.form.get('growth_percentage', 10)
    harvest_date_str = request.form.get('expected_harvest_date')
    expected_yield = request.form.get('expected_yield', 0)
    production_cost = request.form.get('production_cost', 0)
    expected_revenue = request.form.get('expected_revenue', 0)
    health_status = request.form.get('health_status', 'Healthy')

    if not crop_name or not planting_date_str or not harvest_date_str:
        flash('Crop name, planting date, and harvest date are required.', 'danger')
        return redirect(url_for('crops.crops_view'))

    try:
        p_date = datetime.strptime(planting_date_str, '%Y-%m-%d').date()
        h_date = datetime.strptime(harvest_date_str, '%Y-%m-%d').date()
        exp_yield = float(expected_yield)
        prod_cost = float(production_cost) if production_cost else 0.0
        exp_rev = float(expected_revenue) if expected_revenue else 0.0
        pct = int(growth_percentage)
    except (ValueError, TypeError):
        flash('Invalid date or numeric values provided.', 'danger')
        return redirect(url_for('crops.crops_view'))

    # VAL-04: Chronological date check
    if h_date < p_date:
        flash('Expected harvest date cannot be earlier than planting date.', 'danger')
        return redirect(url_for('crops.crops_view'))

    # VAL-03: Non-negative numeric validation
    if (math.isnan(exp_yield) or math.isinf(exp_yield) or exp_yield < 0 or
        math.isnan(prod_cost) or math.isinf(prod_cost) or prod_cost < 0 or
        math.isnan(exp_rev) or math.isinf(exp_rev) or exp_rev < 0 or
        pct < 0 or pct > 100):
        flash('Yield, cost, and revenue cannot be negative.', 'danger')
        return redirect(url_for('crops.crops_view'))

    # SEC-03: Validate farm ownership
    assigned_farm_id = None
    if farm_id:
        try:
            f_id = int(farm_id)
            farm = Farm.query.filter_by(id=f_id, user_id=user_id).first()
            if not farm:
                flash('Selected farm does not exist or does not belong to you.', 'danger')
                return redirect(url_for('crops.crops_view'))
            assigned_farm_id = farm.id
        except (ValueError, TypeError):
            flash('Invalid farm ID format.', 'danger')
            return redirect(url_for('crops.crops_view'))

    new_crop = Crop(
        user_id=user_id,
        farm_id=assigned_farm_id,
        crop_name=crop_name,
        planting_date=p_date,
        growth_stage=growth_stage,
        growth_percentage=pct,
        expected_harvest_date=h_date,
        expected_yield=exp_yield,
        production_cost=prod_cost,
        expected_revenue=exp_rev,
        health_status=health_status
    )
    db.session.add(new_crop)
    db.session.commit()
    flash(f"Crop '{new_crop.crop_name}' added to monitoring schedule.", 'success')
    return redirect(url_for('crops.crops_view'))

@crops_bp.route('/crops/<int:id>/edit', methods=['POST'])
@login_required
@role_required('FARMER')
def edit_crop(id):
    crop = db.session.get(Crop, id)
    if not crop:
        abort(404)
    if crop.user_id != session['user_id']:
        abort(403)

    crop.crop_name = request.form.get('crop_name', crop.crop_name).strip()
    crop.growth_stage = request.form.get('growth_stage', crop.growth_stage)
    crop.health_status = request.form.get('health_status', crop.health_status)

    try:
        if request.form.get('growth_percentage') is not None:
            pct_val = int(request.form.get('growth_percentage'))
            if pct_val < 0 or pct_val > 100:
                flash('Growth percentage must be between 0 and 100.', 'danger')
                return redirect(url_for('crops.crops_view'))
            crop.growth_percentage = pct_val

        if request.form.get('expected_yield') is not None:
            yield_val = float(request.form.get('expected_yield'))
            if math.isnan(yield_val) or math.isinf(yield_val) or yield_val < 0:
                flash('Expected yield cannot be negative.', 'danger')
                return redirect(url_for('crops.crops_view'))
            crop.expected_yield = yield_val

        if request.form.get('production_cost') is not None:
            cost_val = float(request.form.get('production_cost'))
            if math.isnan(cost_val) or math.isinf(cost_val) or cost_val < 0:
                flash('Production cost cannot be negative.', 'danger')
                return redirect(url_for('crops.crops_view'))
            crop.production_cost = cost_val

        if request.form.get('expected_revenue') is not None:
            rev_val = float(request.form.get('expected_revenue'))
            if math.isnan(rev_val) or math.isinf(rev_val) or rev_val < 0:
                flash('Expected revenue cannot be negative.', 'danger')
                return redirect(url_for('crops.crops_view'))
            crop.expected_revenue = rev_val

        if request.form.get('expected_harvest_date'):
            new_h_date = datetime.strptime(request.form.get('expected_harvest_date'), '%Y-%m-%d').date()
            if crop.planting_date and new_h_date < crop.planting_date:
                flash('Expected harvest date cannot be earlier than planting date.', 'danger')
                return redirect(url_for('crops.crops_view'))
            crop.expected_harvest_date = new_h_date
    except (ValueError, TypeError):
        flash('Invalid numeric or date format.', 'danger')
        return redirect(url_for('crops.crops_view'))

    db.session.commit()
    flash(f"Crop '{crop.crop_name}' details updated.", 'success')
    return redirect(url_for('crops.crops_view'))

@crops_bp.route('/crops/<int:id>/delete', methods=['POST'])
@login_required
@role_required('FARMER')
def delete_crop(id):
    crop = db.session.get(Crop, id)
    if not crop:
        abort(404)
    if crop.user_id != session['user_id']:
        abort(403)

    name = crop.crop_name
    db.session.delete(crop)
    db.session.commit()
    flash(f"Crop record '{name}' deleted.", 'info')
    return redirect(url_for('crops.crops_view'))

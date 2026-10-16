import math
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, abort
from extensions import db
from models.order import Order
from models.product import Product
from models.crop import Crop
from models.reservation import FutureHarvest
from services.marketplace_service import MarketplaceService
from routes.auth import login_required, role_required

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
@role_required('FARMER')
def analytics_view():
    user_id = session['user_id']
    
    # Orders for this farmer's products
    orders = Order.query.join(Order.product).filter(
        Order.product.has(user_id=user_id)
    ).all()

    delivered_orders = [o for o in orders if o.status == 'Delivered']
    total_revenue = sum(o.total_amount for o in delivered_orders)
    total_sold_kg = sum(o.quantity for o in delivered_orders)
    avg_price = round(total_revenue / total_sold_kg, 2) if total_sold_kg > 0 else 0.0

    # Crop products and inventory
    products = Product.query.filter_by(user_id=user_id).all()
    total_unsold_kg = sum(p.quantity for p in products if p.availability_status == 'Available')

    # Future harvests and reserved quantity
    future_harvests = FutureHarvest.query.filter_by(farmer_id=user_id).all()
    total_reserved_kg = sum(fh.reserved_quantity for fh in future_harvests)

    # RUN-02: Crop-wise revenue calculation with null-safe product checks
    crop_revenue = {}
    for o in delivered_orders:
        if o.product and o.product.title:
            crop_title = o.product.title.split('(')[0].strip()
        else:
            crop_title = 'Unspecified Produce'
        crop_revenue[crop_title] = crop_revenue.get(crop_title, 0.0) + o.total_amount

    # Fallback sample data if brand new farmer has zero historical orders
    has_real_order_history = len(delivered_orders) > 0
    if not has_real_order_history:
        crop_revenue = {'Tomatoes': 6600.0, 'Cucumbers': 3200.0, 'Rice Paddy': 8500.0}
        total_revenue = 18300.0
        total_sold_kg = 750.0
        avg_price = 24.4

    return render_template(
        'analytics.html',
        total_revenue=total_revenue,
        total_sold_kg=total_sold_kg,
        avg_price=avg_price,
        total_unsold_kg=total_unsold_kg,
        total_reserved_kg=total_reserved_kg,
        crop_revenue_labels=list(crop_revenue.keys()),
        crop_revenue_values=list(crop_revenue.values()),
        has_real_order_history=has_real_order_history,
        delivered_orders=delivered_orders
    )

@analytics_bp.route('/waste-reduction')
@login_required
@role_required('FARMER')
def waste_reduction_view():
    user_id = session['user_id']
    insights = MarketplaceService.get_waste_reduction_insights(user_id)
    return render_template('waste_reduction.html', insights=insights)

@analytics_bp.route('/products/<int:id>/discount', methods=['POST'])
@login_required
@role_required('FARMER')
def apply_discount(id):
    product = db.session.get(Product, id)
    if not product:
        abort(404)
    if product.user_id != session['user_id']:
        abort(403)

    # VAL-02: Validate discount value range and catch conversion exceptions gracefully
    try:
        discount_pct = float(request.form.get('discount_pct', 15))
        if math.isnan(discount_pct) or math.isinf(discount_pct) or discount_pct <= 0 or discount_pct > 90:
            flash('Discount percentage must be between 1% and 90%.', 'danger')
            return redirect(url_for('analytics.waste_reduction_view'))
    except (ValueError, TypeError):
        flash('Invalid numeric discount percentage value provided.', 'danger')
        return redirect(url_for('analytics.waste_reduction_view'))

    old_price = product.price_per_unit
    new_price = round(old_price * (1 - discount_pct / 100), 2)
    product.price_per_unit = max(1.0, new_price)
    db.session.commit()

    flash(f"Quick-sale price applied to '{product.title}'! Price adjusted from ₹{old_price}/kg to ₹{new_price}/kg to accelerate clearance.", 'success')
    return redirect(url_for('analytics.waste_reduction_view'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from extensions import db
from models.order import Order
from models.product import Product
from models.review import Review
from models.user import User
from services.marketplace_service import MarketplaceService
from routes.auth import login_required, role_required

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders')
@login_required
def orders_view():
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    
    if user.role == 'BUYER':
        # Orders placed by this buyer
        orders = Order.query.filter_by(buyer_id=user_id).order_by(Order.created_at.desc()).all()
        return render_template('orders.html', orders=orders, user_role='BUYER')
    elif user.role == 'FARMER':
        # Orders received for this farmer's products
        orders = Order.query.join(Order.product).filter(
            Order.product.has(user_id=user_id)
        ).order_by(Order.created_at.desc()).all()
        return render_template('orders.html', orders=orders, user_role='FARMER')
    else:
        # Admin views all orders
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template('orders.html', orders=orders, user_role='ADMIN')

@orders_bp.route('/orders/create', methods=['POST'])
@login_required
@role_required('BUYER')
def create_order():
    buyer_id = session['user_id']
    product_id = request.form.get('product_id')
    quantity_str = request.form.get('quantity')
    delivery_address = request.form.get('delivery_address', '').strip()
    contact_phone = request.form.get('contact_phone', '').strip()
    notes = request.form.get('notes', '').strip()

    if not product_id or not quantity_str or not delivery_address or not contact_phone:
        flash('All fields are required to place your purchase order.', 'danger')
        return redirect(url_for('marketplace.marketplace_view'))

    # VAL-02: Catch non-numeric product ID and quantity conversion errors gracefully
    try:
        pid = int(product_id)
    except (ValueError, TypeError):
        flash('Invalid product identifier.', 'danger')
        return redirect(url_for('marketplace.marketplace_view'))

    success, msg, order = MarketplaceService.place_order(
        buyer_id=buyer_id,
        product_id=pid,
        quantity=quantity_str,
        delivery_address=delivery_address,
        contact_phone=contact_phone,
        notes=notes
    )

    if success:
        flash(f"Order #{order.order_number} confirmed! Direct purchase request logged with farmer.", 'success')
        return redirect(url_for('orders.orders_view'))
    else:
        flash(msg, 'danger')
        return redirect(url_for('marketplace.product_detail', id=pid))

@orders_bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
def update_order_status(id):
    order = db.session.get(Order, id)
    if not order:
        abort(404)
    new_status = request.form.get('status')
    user_id = session['user_id']
    role = session.get('role')

    # RUN-02: Handle missing/deleted products safely without raising AttributeError
    if order.product:
        if order.product.user_id != user_id and role != 'ADMIN':
            abort(403)
    elif role != 'ADMIN':
        abort(403)

    allowed_statuses = ['Pending Payment', 'Processing', 'Dispatched', 'Delivered', 'Cancelled']
    if new_status in allowed_statuses:
        # LOG-01: Restore stock atomically when transitioning to Cancelled exactly once
        if new_status == 'Cancelled' and order.status != 'Cancelled':
            if order.product:
                order.product.quantity = round(order.product.quantity + order.quantity, 2)
                if order.product.availability_status == 'Sold Out' and order.product.quantity > 0:
                    order.product.availability_status = 'Available'

        order.status = new_status
        if new_status == 'Delivered':
            order.payment_status = 'Paid (Direct Cash / Demo Transfer)'
        db.session.commit()
        flash(f"Order #{order.order_number} status updated to '{new_status}'.", 'success')
    else:
        flash('Invalid order status.', 'danger')

    return redirect(url_for('orders.orders_view'))

@orders_bp.route('/orders/<int:id>/review', methods=['POST'])
@login_required
@role_required('BUYER')
def add_review(id):
    order = db.session.get(Order, id)
    if not order:
        abort(404)
    user_id = session['user_id']

    if order.buyer_id != user_id:
        abort(403)

    if order.status != 'Delivered':
        flash('Reviews can only be submitted after verified delivery.', 'warning')
        return redirect(url_for('orders.orders_view'))

    try:
        rating = max(1, min(5, int(request.form.get('rating', 5))))
    except (ValueError, TypeError):
        rating = 5
    comment = request.form.get('comment', '').strip()

    if not comment:
        flash('Please write a short review comment.', 'danger')
        return redirect(url_for('orders.orders_view'))

    # Check if review already exists
    existing = Review.query.filter_by(order_id=order.id).first()
    if existing:
        existing.rating = rating
        existing.comment = comment
    else:
        new_rev = Review(
            order_id=order.id,
            buyer_id=order.buyer_id,
            farmer_id=order.product.user_id,
            rating=max(1, min(5, rating)),
            comment=comment
        )
        db.session.add(new_rev)

    db.session.commit()
    flash('Thank you! Your feedback updates this farmer\'s verified trust score.', 'success')
    return redirect(url_for('orders.orders_view'))

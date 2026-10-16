from flask import Blueprint, render_template, session, redirect, url_for, flash, abort, request
from extensions import db
from models.user import User
from models.farm import Farm
from models.crop import Crop
from models.order import Order
from models.product import Product
from models.reservation import FutureHarvest, Reservation
from models.demand import BuyerDemand
from models.notification import Notification
from routes.auth import login_required, role_required
from datetime import datetime, date, timedelta
import uuid

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/buyer/dashboard')
@login_required
@role_required('BUYER')
def buyer_dashboard():
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    orders = Order.query.filter_by(buyer_id=user_id).order_by(Order.created_at.desc()).all()
    total_spent = sum(o.total_amount for o in orders if o.status != 'Cancelled')
    active_orders = [o for o in orders if o.status in ['Pending Payment', 'Processing', 'Dispatched']]
    delivered_orders = [o for o in orders if o.status == 'Delivered']
    
    # Recent marketplace products available for purchase
    featured_products = Product.query.filter(
        Product.availability_status == 'Available',
        Product.quantity > 0
    ).order_by(Product.created_at.desc()).limit(6).all()

    # Upcoming harvests open for advance procurement reservation
    upcoming_harvests = FutureHarvest.query.filter(
        FutureHarvest.status.in_(['Open for Reservation', 'Partially Reserved'])
    ).order_by(FutureHarvest.expected_harvest_date.asc()).limit(6).all()

    return render_template(
        'buyer_dashboard.html',
        user=user,
        orders=orders,
        total_spent=total_spent,
        active_orders=active_orders,
        delivered_orders=delivered_orders,
        featured_products=featured_products,
        upcoming_harvests=upcoming_harvests
    )

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    # If buyer, redirect to dedicated buyer dashboard
    if user.role == 'BUYER':
        return redirect(url_for('dashboard.buyer_dashboard'))
    if user.role == 'ADMIN':
        return redirect(url_for('admin.admin_view'))

    # Farmer data
    farms = Farm.query.filter_by(user_id=user.id).all()
    crops = Crop.query.filter_by(user_id=user.id).all()
    
    # Financials & Orders
    farmer_orders = Order.query.join(Order.product).filter(
        Order.product.has(user_id=user.id)
    ).all()
    
    total_revenue = sum(o.total_amount for o in farmer_orders if o.status in ['Delivered', 'Processing', 'Dispatched'])
    total_orders_count = len(farmer_orders)

    # Future harvests and reservations
    future_harvests = FutureHarvest.query.filter_by(farmer_id=user.id).all()
    total_reserved_kg = sum(fh.reserved_quantity for fh in future_harvests)
    
    # Notifications and alerts
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(5).all()

    # Active market demands in region
    market_demands = BuyerDemand.query.filter_by(status='Active').order_by(BuyerDemand.created_at.desc()).limit(4).all()

    # Today's Action Items ("What should I do today?")
    today_tasks = []
    # Check crops nearing harvest
    today = date.today()
    for crop in crops:
        days_to_harvest = (crop.expected_harvest_date - today).days
        if 0 <= days_to_harvest <= 7:
            today_tasks.append({
                'title': f"Prepare Harvest: {crop.crop_name}",
                'desc': f"Expected harvest date is in {days_to_harvest} day(s). Clean storage crates and review buyer demand.",
                'urgency': 'high',
                'action_url': url_for('crops.crops_view')
            })
        if crop.health_status in ['Moderate Risk', 'Action Required', 'Disease Detected']:
            today_tasks.append({
                'title': f"Inspect Crop Health: {crop.crop_name}",
                'desc': f"Health status is flagged as '{crop.health_status}'. Perform leaf check or scan a leaf image.",
                'urgency': 'high',
                'action_url': url_for('disease.crop_health_view')
            })

    # Default daily routine if no critical alerts
    if not today_tasks:
        today_tasks.append({
            'title': "Morning Irrigation & Drip Check",
            'desc': "Check soil moisture in root zone before ambient heat rises. Ensure drip line emitters are unclogged.",
            'urgency': 'normal',
            'action_url': url_for('farms.farms_view')
        })
        today_tasks.append({
            'title': "Scout for Sucking Pests",
            'desc': "Inspect lower foliage and sticky traps for early whitefly or aphid presence.",
            'urgency': 'normal',
            'action_url': url_for('chatbot.chatbot_view')
        })

    # Monthly revenue data for Chart.js
    monthly_revenue = {
        'labels': ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
        'revenues': [12000, 18500, 24000, 19500, 31000, float(total_revenue) if total_revenue > 0 else 6600]
    }

    # Crop health breakdown
    healthy_count = sum(1 for c in crops if c.health_status == 'Healthy')
    risk_count = sum(1 for c in crops if c.health_status != 'Healthy')

    return render_template(
        'dashboard.html',
        user=user,
        farms=farms,
        crops=crops,
        total_farms=len(farms),
        active_crops=len(crops),
        total_revenue=total_revenue,
        total_orders=total_orders_count,
        total_reserved_kg=total_reserved_kg,
        future_harvests=future_harvests,
        notifications=notifications,
        market_demands=market_demands,
        today_tasks=today_tasks,
        healthy_count=healthy_count,
        risk_count=risk_count,
        monthly_revenue=monthly_revenue
    )

@dashboard_bp.route('/profile/<int:user_id>')
def farmer_profile(user_id):
    user = User.query.get_or_404(user_id)
    trust_profile = user.get_trust_profile()
    farms = Farm.query.filter_by(user_id=user.id).all()
    products = [p for p in user.products if p.availability_status == 'Available']
    
    return render_template(
        'farmer_profile.html',
        farmer=user,
        trust=trust_profile,
        farms=farms,
        products=products
    )

from models.harvest import HarvestBatch
from models.verification_log import BatchVerificationLog
from services.verification_service import (
    VALID_STAGES,
    STAGE_CONFIG,
    trigger_farmer_re_review,
    generate_qr_data_uri
)
from werkzeug.utils import secure_filename
import os
from flask import current_app
from routes.auth import role_required

ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_DOC_EXT = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'doc', 'docx'}

def _is_valid_img(f):
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXT

def _is_valid_doc(f):
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXT

@dashboard_bp.route('/farmer/verifications')
@login_required
@role_required('FARMER')
def my_verifications():
    user = User.query.get_or_404(session['user_id'])
    filter_stage = request.args.get('stage', 'All').strip()
    
    all_batches = HarvestBatch.query.filter_by(user_id=user.id).order_by(HarvestBatch.created_at.desc()).all()
    if filter_stage != 'All' and filter_stage in VALID_STAGES:
        batches = [b for b in all_batches if b.verification_stage == filter_stage]
    else:
        batches = all_batches

    stage_counts = {s: sum(1 for b in all_batches if b.verification_stage == s) for s in VALID_STAGES}

    return render_template(
        'farmer_verifications.html',
        user=user,
        batches=batches,
        stage_counts=stage_counts,
        current_stage_filter=filter_stage,
        stage_config=STAGE_CONFIG,
        valid_stages=VALID_STAGES
    )

@dashboard_bp.route('/farmer/batches/<int:id>/submit-corrections', methods=['POST'])
@login_required
@role_required('FARMER')
def submit_corrections(id):
    batch = HarvestBatch.query.get_or_404(id)
    if batch.user_id != session['user_id']:
        abort(403)

    corrections_note = request.form.get('corrections_note', '').strip()
    if not corrections_note:
        flash('Please describe the corrections or clarifications you are submitting.', 'danger')
        return redirect(url_for('dashboard.my_verifications'))

    # Handle optional new supporting document
    if 'supporting_document' in request.files:
        doc_file = request.files['supporting_document']
        if doc_file and doc_file.filename != '' and _is_valid_doc(doc_file.filename):
            doc_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
            os.makedirs(doc_upload_dir, exist_ok=True)
            ext = doc_file.filename.rsplit('.', 1)[1].lower()
            doc_name = secure_filename(doc_file.filename)
            doc_filename = f"doc_{uuid.uuid4().hex[:10]}.{ext}"
            doc_file.save(os.path.join(doc_upload_dir, doc_filename))
            batch.document_url = f"/uploads/documents/{doc_filename}"
            batch.document_name = doc_name

    old_stage = batch.verification_stage
    batch.verification_stage = 'Submitted'
    batch.verification_status = 'Pending Re-review'
    batch.is_independently_verified = False

    # Log farmer corrections in audit timeline
    log = BatchVerificationLog(
        batch_id=batch.id,
        previous_stage=old_stage,
        new_stage='Submitted',
        action_by_id=session['user_id'],
        action_type='CORRECTION_SUBMITTED',
        comments=f"Farmer submitted corrections: {corrections_note}",
        created_at=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Corrections submitted for Batch #{batch.batch_code}! Status transitioned to 'Submitted' for admin re-review.", 'success')
    return redirect(url_for('dashboard.my_verifications'))

@dashboard_bp.route('/farmer/batches/<int:id>/edit', methods=['POST'])
@login_required
@role_required('FARMER')
def edit_batch_details(id):
    batch = HarvestBatch.query.get_or_404(id)
    if batch.user_id != session['user_id']:
        abort(403)

    crop_name = request.form.get('crop_name', '').strip()
    category = request.form.get('category', batch.category).strip()
    description = request.form.get('description', '').strip()
    quantity_str = request.form.get('quantity')
    unit = request.form.get('unit', batch.unit).strip()
    harvest_date_str = request.form.get('harvest_date')
    location = request.form.get('location', '').strip()
    price_str = request.form.get('asking_price')
    quality_grade = request.form.get('quality_grade', batch.quality_grade).strip()

    if not crop_name or not quantity_str or not harvest_date_str or not location:
        flash('Product name, quantity, harvest date, and location are required.', 'danger')
        return redirect(url_for('dashboard.my_verifications'))

    try:
        qty = float(quantity_str)
        h_date = datetime.strptime(harvest_date_str, '%Y-%m-%d').date()
        price = float(price_str) if price_str else batch.asking_price
        if qty <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(url_for('dashboard.my_verifications'))
    except (ValueError, TypeError):
        flash('Invalid numeric or date format.', 'danger')
        return redirect(url_for('dashboard.my_verifications'))

    # Update permitted specifications
    batch.crop_name = crop_name
    batch.category = category
    batch.description = description
    batch.quantity = qty
    batch.unit = unit
    batch.harvest_date = h_date
    batch.location = location
    batch.asking_price = price
    batch.quality_grade = quality_grade

    # Handle image upload if provided
    if 'product_image' in request.files:
        img_file = request.files['product_image']
        if img_file and img_file.filename != '' and _is_valid_img(img_file.filename):
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
            os.makedirs(upload_dir, exist_ok=True)
            ext = img_file.filename.rsplit('.', 1)[1].lower()
            filename = f"prod_{uuid.uuid4().hex[:10]}.{ext}"
            img_file.save(os.path.join(upload_dir, filename))
            batch.image_url = f"/uploads/products/{filename}"

    # Handle document upload if provided
    if 'supporting_document' in request.files:
        doc_file = request.files['supporting_document']
        if doc_file and doc_file.filename != '' and _is_valid_doc(doc_file.filename):
            doc_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
            os.makedirs(doc_upload_dir, exist_ok=True)
            ext = doc_file.filename.rsplit('.', 1)[1].lower()
            doc_name = secure_filename(doc_file.filename)
            doc_filename = f"doc_{uuid.uuid4().hex[:10]}.{ext}"
            doc_file.save(os.path.join(doc_upload_dir, doc_filename))
            batch.document_url = f"/uploads/documents/{doc_filename}"
            batch.document_name = doc_name

    # Synchronize linked Product if exists
    for prod in batch.products:
        prod.title = crop_name
        prod.category = category
        prod.description = description
        prod.quantity = qty
        prod.unit = unit
        prod.harvest_date = h_date
        prod.location = location
        if price:
            prod.price_per_unit = price
        if batch.image_url:
            prod.image_url = batch.image_url

    # Trigger re-review: material changes invalidate previous approval
    trigger_farmer_re_review(
        batch=batch,
        actor_id=session['user_id'],
        reason="Farmer updated batch specifications. Mandatory re-review required."
    )

    flash(f"Batch #{batch.batch_code} updated! As specifications were changed, verification status has been reset to 'Submitted' for admin re-evaluation.", 'success')
    return redirect(url_for('dashboard.my_verifications'))


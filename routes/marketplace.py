import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, abort
from extensions import db
from models.product import Product
from models.crop import Crop
from models.user import User
from models.demand import BuyerDemand
from services.marketplace_service import MarketplaceService
from routes.auth import login_required, role_required

marketplace_bp = Blueprint('marketplace', __name__)

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'webp'}

def is_valid_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXT

from models.harvest import HarvestBatch
from models.verification_log import BatchVerificationLog
from services.verification_service import generate_uhvc_code, generate_qr_data_uri, STAGE_CONFIG
from werkzeug.utils import secure_filename

ALLOWED_DOC_EXT = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'doc', 'docx'}

def is_valid_doc(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXT

@marketplace_bp.route('/marketplace')
def marketplace_view():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'All')
    location = request.args.get('location', '').strip()
    max_price = request.args.get('max_price', '').strip()

    products = MarketplaceService.search_products(
        query=query,
        category=category,
        location=location,
        max_price=max_price
    )
    
    categories = ['All', 'Vegetables', 'Grains', 'Fruits', 'Pulses', 'Spices']

    return render_template(
        'marketplace.html',
        products=products,
        categories=categories,
        current_category=category,
        search_query=query,
        search_location=location,
        search_max_price=max_price,
        stage_config=STAGE_CONFIG
    )

@marketplace_bp.route('/products/<int:id>')
def product_detail(id):
    product = db.session.get(Product, id)
    if not product:
        abort(404)
    farmer = product.farmer
    trust = farmer.get_trust_profile()
    
    # Generate live QR code for batch public traceability passport
    batch_code = product.uhvc_code or (product.batch.batch_code if product.batch else None)
    qr_data_uri = ""
    if batch_code:
        trace_url = url_for('traceability.batch_detail', batch_code=batch_code, _external=True)
        qr_data_uri = generate_qr_data_uri(trace_url)

    # Other products from the same farmer
    other_products = Product.query.filter(
        Product.user_id == farmer.id,
        Product.id != product.id,
        Product.availability_status == 'Available'
    ).limit(3).all()

    return render_template(
        'product_detail.html',
        product=product,
        farmer=farmer,
        trust=trust,
        other_products=other_products,
        qr_data_uri=qr_data_uri,
        batch_code=batch_code,
        stage_config=STAGE_CONFIG
    )

@marketplace_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@role_required('FARMER')
def create_product():
    user_id = session['user_id']
    farmer_crops = Crop.query.filter_by(user_id=user_id).all()
    farmer_batches = HarvestBatch.query.filter_by(user_id=user_id).order_by(HarvestBatch.created_at.desc()).all()

    demand_id = request.args.get('demand_id') or request.form.get('demand_id')
    demand = None
    if demand_id:
        try:
            demand = db.session.get(BuyerDemand, int(demand_id))
        except (ValueError, TypeError):
            demand = None

    if request.method == 'POST':
        # 1.D: If demand has an HVC code, validate only Batch ID and Quantity
        if demand and demand.hvc_code:
            batch_input = request.form.get('batch_id', '').strip()
            quantity_str = request.form.get('quantity', '').strip()

            if not batch_input or not quantity_str:
                flash('Both Batch ID and Quantity are required to fulfill this verified demand.', 'danger')
                return render_template('product_create.html', crops=farmer_crops, farmer_batches=farmer_batches, demand=demand)

            try:
                qty = float(quantity_str)
                if qty <= 0:
                    flash('Quantity must be greater than zero.', 'danger')
                    return render_template('product_create.html', crops=farmer_crops, farmer_batches=farmer_batches, demand=demand)
            except (ValueError, TypeError):
                flash('Invalid quantity format.', 'danger')
                return render_template('product_create.html', crops=farmer_crops, farmer_batches=farmer_batches, demand=demand)

            # Look up batch by id or batch_code owned by this farmer
            batch = None
            try:
                b_id = int(batch_input)
                batch = HarvestBatch.query.filter_by(id=b_id, user_id=user_id).first()
            except ValueError:
                pass
            if not batch:
                batch = HarvestBatch.query.filter_by(batch_code=batch_input, user_id=user_id).first()

            if not batch:
                batch_code_val = batch_input if batch_input.startswith("UHVC-") else f"UHVC-{datetime.now().year}-{batch_input.upper()}"
                batch = HarvestBatch(
                    batch_code=batch_code_val,
                    user_id=user_id,
                    crop_name=demand.crop_name,
                    category='Vegetables',
                    harvest_date=datetime.now().date(),
                    quantity=qty,
                    unit=demand.unit or 'kg',
                    asking_price=demand.target_price or 25.0,
                    quality_grade='Grade A',
                    verification_stage='Submitted',
                    verification_status='Registered',
                    is_independently_verified=False,
                    journey_stage='Harvested'
                )
                db.session.add(batch)
                db.session.flush()
            elif batch.quantity < qty:
                batch.quantity = qty

            # Create product listing from the verified batch to fulfill the demand
            unit_price = demand.target_price if demand.target_price else (batch.asking_price or 20.0)
            new_product = Product(
                user_id=user_id,
                crop_id=batch.crop_id,
                batch_id=batch.id,
                title=f"{demand.crop_name} (Batch #{batch.batch_code})",
                category=batch.category,
                quantity=qty,
                initial_quantity=qty,
                unit=batch.unit or demand.unit,
                price_per_unit=unit_price,
                location=batch.location or demand.location,
                harvest_date=batch.harvest_date,
                image_url=batch.image_url or 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80',
                quality_grade=batch.quality_grade,
                description=f"Direct lot fulfillment for demand #{demand.id} ({demand.crop_name}). Verified HVC: {batch.batch_code}.",
                availability_status='Available'
            )
            db.session.add(new_product)

            # Update demand fulfillment supply
            demand.available_supply = round((demand.available_supply or 0.0) + qty, 2)
            if demand.available_supply >= demand.required_quantity:
                demand.status = 'Fulfilled'

            db.session.commit()
            flash(f"Demand for '{demand.crop_name}' fulfilled successfully with Batch #{batch.batch_code} ({qty} {batch.unit})!", 'success')
            return redirect(url_for('general.demand_view'))

        # Existing form logic unchanged for demands without HVC code or standalone listings
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Vegetables')
        crop_id = request.form.get('crop_id')
        quantity_str = request.form.get('quantity', '0')
        unit = request.form.get('unit', 'kg')
        price_str = request.form.get('price_per_unit', '0')
        location = request.form.get('location', '').strip()
        harvest_date_str = request.form.get('harvest_date')
        quality_grade = request.form.get('quality_grade', 'Grade A')
        description = request.form.get('description', '').strip()

        if not title or not quantity_str or not price_str or not location or not harvest_date_str:
            flash('Please fill in all required product fields.', 'danger')
            return render_template('product_create.html', crops=farmer_crops, farmer_batches=farmer_batches, demand=demand)

        try:
            qty = float(quantity_str)
            price = float(price_str)
            h_date = datetime.strptime(harvest_date_str, '%Y-%m-%d').date()
            if qty <= 0 or price <= 0:
                flash('Quantity and price must be greater than zero.', 'danger')
                return render_template('product_create.html', crops=farmer_crops)
        except (ValueError, TypeError):
            flash('Invalid numeric or date format.', 'danger')
            return render_template('product_create.html', crops=farmer_crops)

        image_url = None
        # Handle optional product image upload
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename != '' and is_valid_image(file.filename):
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
                os.makedirs(upload_dir, exist_ok=True)
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"prod_{uuid.uuid4().hex[:10]}.{ext}"
                file.save(os.path.join(upload_dir, filename))
                image_url = f"/uploads/products/{filename}"

        if not image_url:
            # Default fallback images based on category
            cat_images = {
                'Vegetables': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80',
                'Grains': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80',
                'Fruits': 'https://images.unsplash.com/photo-1528825871115-3581a5387919?auto=format&fit=crop&w=600&q=80',
                'Pulses': 'https://images.unsplash.com/photo-1515543237350-b3eea1ec8082?auto=format&fit=crop&w=600&q=80',
                'Spices': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=600&q=80'
            }
            image_url = cat_images.get(category, cat_images['Vegetables'])

        # Handle optional supporting quality documents / certificates upload
        document_url = None
        document_name = None
        if 'supporting_document' in request.files:
            doc_file = request.files['supporting_document']
            if doc_file and doc_file.filename != '' and is_valid_doc(doc_file.filename):
                doc_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
                os.makedirs(doc_upload_dir, exist_ok=True)
                ext = doc_file.filename.rsplit('.', 1)[1].lower()
                doc_name = secure_filename(doc_file.filename)
                doc_filename = f"doc_{uuid.uuid4().hex[:10]}.{ext}"
                doc_file.save(os.path.join(doc_upload_dir, doc_filename))
                document_url = f"/uploads/documents/{doc_filename}"
                document_name = doc_name

        # SEC-04: Verify crop_id ownership if provided
        assigned_crop_id = None
        if crop_id:
            try:
                c_id = int(crop_id)
                crop = Crop.query.filter_by(id=c_id, user_id=user_id).first()
                if not crop:
                    flash('Selected crop does not exist or does not belong to you.', 'danger')
                    return render_template('product_create.html', crops=farmer_crops)
                assigned_crop_id = crop.id
            except (ValueError, TypeError):
                flash('Invalid crop ID format.', 'danger')
                return render_template('product_create.html', crops=farmer_crops)

        # Backend-enforced UHVC Generation
        uhvc_code = generate_uhvc_code()

        # Create associated HarvestBatch
        new_batch = HarvestBatch(
            batch_code=uhvc_code,
            user_id=user_id,
            crop_id=assigned_crop_id,
            crop_name=title.split('(')[0].strip(),
            category=category,
            description=description,
            harvest_date=h_date,
            quantity=qty,
            unit=unit,
            asking_price=price,
            location=location,
            image_url=image_url,
            document_url=document_url,
            document_name=document_name,
            quality_grade=quality_grade,
            verification_stage='Submitted',
            verification_status='Registered',
            is_independently_verified=False,
            journey_stage='Harvested'
        )
        db.session.add(new_batch)
        db.session.flush()

        # Record Initial Submission in Audit History
        log = BatchVerificationLog(
            batch_id=new_batch.id,
            previous_stage=None,
            new_stage='Submitted',
            action_by_id=user_id,
            action_type='INITIAL_SUBMISSION',
            comments='Harvest batch registered by farmer with initial specifications and evidence.',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log)

        # Create Marketplace Product listing linked to the batch
        new_product = Product(
            user_id=user_id,
            crop_id=assigned_crop_id,
            batch_id=new_batch.id,
            title=title,
            category=category,
            quantity=qty,
            initial_quantity=qty,
            unit=unit,
            price_per_unit=price,
            location=location,
            harvest_date=h_date,
            image_url=image_url,
            quality_grade=quality_grade,
            description=description,
            availability_status='Available'
        )
        db.session.add(new_product)

        if demand:
            demand.available_supply = round((demand.available_supply or 0.0) + qty, 2)
            if demand.available_supply >= demand.required_quantity:
                demand.status = 'Fulfilled'

        db.session.commit()

        flash(f"Produce listing '{new_product.title}' registered with UHVC #{uhvc_code}! Verification stage: Submitted (Under queue for quality audit).", 'success')
        return redirect(url_for('marketplace.marketplace_view'))

    return render_template('product_create.html', crops=farmer_crops, farmer_batches=farmer_batches, demand=demand)

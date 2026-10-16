import uuid
import os
import io
import qrcode
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file, abort
from extensions import db
from models.harvest import HarvestBatch
from models.farm import Farm
from models.crop import Crop
from routes.auth import login_required, role_required

traceability_bp = Blueprint('traceability', __name__)

@traceability_bp.route('/traceability')
def traceability_view():
    search_code = request.args.get('batch_code', '').strip().upper()
    found_batch = None
    if search_code:
        found_batch = HarvestBatch.query.filter_by(batch_code=search_code).first()
        if not found_batch:
            flash(f"No harvest batch found matching code '{search_code}'.", 'warning')

    # If farmer is logged in, show their registered batches
    farmer_batches = []
    farmer_farms = []
    farmer_crops = []
    if 'user_id' in session and session.get('role') in ['FARMER', 'ADMIN']:
        farmer_batches = HarvestBatch.query.filter_by(user_id=session['user_id']).order_by(HarvestBatch.created_at.desc()).all()
        farmer_farms = Farm.query.filter_by(user_id=session['user_id']).all()
        farmer_crops = Crop.query.filter_by(user_id=session['user_id']).all()

    return render_template(
        'traceability.html',
        search_code=search_code,
        found_batch=found_batch,
        farmer_batches=farmer_batches,
        farms=farmer_farms,
        crops=farmer_crops
    )

from models.verification_log import BatchVerificationLog
from services.verification_service import generate_uhvc_code, generate_qr_data_uri, STAGE_CONFIG
from werkzeug.utils import secure_filename
from flask import current_app, send_file
import os
import io

ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_DOC_EXT = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'doc', 'docx'}

def _is_valid_img(f):
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXT

def _is_valid_doc(f):
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXT

@traceability_bp.route('/batch/<batch_code>')
def batch_detail(batch_code):
    batch = HarvestBatch.query.filter_by(batch_code=batch_code.upper()).first_or_404()
    trace_url = url_for('traceability.batch_detail', batch_code=batch.batch_code, _external=True)
    qr_data_uri = generate_qr_data_uri(trace_url)
    return render_template('batch_detail.html', batch=batch, qr_data_uri=qr_data_uri, stage_config=STAGE_CONFIG)

@traceability_bp.route('/batch/<batch_code>/qr')
def batch_qr_image(batch_code):
    batch = HarvestBatch.query.filter_by(batch_code=batch_code.upper()).first_or_404()
    trace_url = url_for('traceability.batch_detail', batch_code=batch.batch_code, _external=True)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(trace_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E3A1E", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@traceability_bp.route('/batches/create', methods=['POST'])
@login_required
@role_required('FARMER')
def create_batch():
    user_id = session['user_id']
    crop_name = request.form.get('crop_name', '').strip()
    category = request.form.get('category', 'Vegetables').strip()
    description = request.form.get('description', '').strip()
    farm_id = request.form.get('farm_id')
    crop_id = request.form.get('crop_id')
    harvest_date_str = request.form.get('harvest_date')
    quantity_str = request.form.get('quantity')
    unit = request.form.get('unit', 'kg')
    location = request.form.get('location', '').strip()
    asking_price_str = request.form.get('asking_price', '0')
    quality_grade = request.form.get('quality_grade', 'Grade A')
    storage = request.form.get('storage_conditions', 'Clean Farm Store')
    notes = request.form.get('notes', '').strip()

    if not crop_name or not harvest_date_str or not quantity_str:
        flash('Crop name, harvest date, and quantity are required.', 'danger')
        return redirect(url_for('traceability.traceability_view'))

    try:
        h_date = datetime.strptime(harvest_date_str, '%Y-%m-%d').date()
        qty = float(quantity_str)
        asking_price = float(asking_price_str) if asking_price_str else 0.0
        if qty <= 0:
            flash('Batch quantity must be greater than zero.', 'danger')
            return redirect(url_for('traceability.traceability_view'))
    except (ValueError, TypeError):
        flash('Invalid date, quantity, or price format.', 'danger')
        return redirect(url_for('traceability.traceability_view'))

    # Handle image upload
    image_url = None
    if 'product_image' in request.files:
        img_file = request.files['product_image']
        if img_file and img_file.filename != '' and _is_valid_img(img_file.filename):
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
            os.makedirs(upload_dir, exist_ok=True)
            ext = img_file.filename.rsplit('.', 1)[1].lower()
            filename = f"batch_{uuid.uuid4().hex[:10]}.{ext}"
            img_file.save(os.path.join(upload_dir, filename))
            image_url = f"/uploads/products/{filename}"

    # Handle document upload
    document_url = None
    document_name = None
    if 'supporting_document' in request.files:
        doc_file = request.files['supporting_document']
        if doc_file and doc_file.filename != '' and _is_valid_doc(doc_file.filename):
            doc_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
            os.makedirs(doc_upload_dir, exist_ok=True)
            ext = doc_file.filename.rsplit('.', 1)[1].lower()
            doc_name = secure_filename(doc_file.filename)
            doc_filename = f"doc_{uuid.uuid4().hex[:10]}.{ext}"
            doc_file.save(os.path.join(doc_upload_dir, doc_filename))
            document_url = f"/uploads/documents/{doc_filename}"
            document_name = doc_name

    # SEC-04: Verify farm_id ownership if provided
    assigned_farm_id = None
    if farm_id:
        try:
            f_id = int(farm_id)
            farm = Farm.query.filter_by(id=f_id, user_id=user_id).first()
            if not farm:
                flash('Selected farm does not exist or does not belong to you.', 'danger')
                return redirect(url_for('traceability.traceability_view'))
            assigned_farm_id = farm.id
        except (ValueError, TypeError):
            flash('Invalid farm ID format.', 'danger')
            return redirect(url_for('traceability.traceability_view'))

    # SEC-04: Verify crop_id ownership if provided
    assigned_crop_id = None
    if crop_id:
        try:
            c_id = int(crop_id)
            crop = Crop.query.filter_by(id=c_id, user_id=user_id).first()
            if not crop:
                flash('Selected crop does not exist or does not belong to you.', 'danger')
                return redirect(url_for('traceability.traceability_view'))
            if assigned_farm_id and crop.farm_id and crop.farm_id != assigned_farm_id:
                flash('Selected crop does not belong to the selected farm.', 'danger')
                return redirect(url_for('traceability.traceability_view'))
            assigned_crop_id = crop.id
        except (ValueError, TypeError):
            flash('Invalid crop ID format.', 'danger')
            return redirect(url_for('traceability.traceability_view'))

    # Unique UHVC batch code generated strictly on the backend
    code = generate_uhvc_code()

    new_batch = HarvestBatch(
        batch_code=code,
        user_id=user_id,
        farm_id=assigned_farm_id,
        crop_id=assigned_crop_id,
        crop_name=crop_name,
        category=category,
        description=description,
        harvest_date=h_date,
        quantity=qty,
        unit=unit,
        location=location,
        asking_price=asking_price,
        image_url=image_url,
        document_url=document_url,
        document_name=document_name,
        verification_stage='Submitted',
        verification_status='Registered',
        is_independently_verified=False,
        quality_grade=quality_grade,
        quality_score=90,
        journey_stage='Harvested',
        storage_conditions=storage,
        notes=notes
    )
    db.session.add(new_batch)
    db.session.flush()

    # Record Initial Submission
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
    db.session.commit()

    flash(f"Harvest Batch #{new_batch.batch_code} registered! Verification Stage: Submitted (queued for admin quality review).", 'success')
    return redirect(url_for('traceability.traceability_view', batch_code=new_batch.batch_code))

@traceability_bp.route('/batches/<int:id>/update-stage', methods=['POST'])
@login_required
@role_required('ADMIN')
def update_batch_stage(id):
    batch = db.session.get(HarvestBatch, id)
    if not batch:
        abort(404)

    stage = request.form.get('journey_stage')
    allowed_stages = ['Harvested', 'Quality Check', 'Packaging', 'In Transit', 'Delivered']
    if stage in allowed_stages:
        prev_stage = batch.journey_stage
        batch.journey_stage = stage
        if stage == 'Packaging':
            batch.packaging_date = datetime.now(timezone.utc).date()
        elif stage == 'In Transit':
            batch.dispatch_date = datetime.now(timezone.utc).date()

        # LOG-03: Ensure lifecycle updates are consistently audited
        log = BatchVerificationLog(
            batch_id=batch.id,
            previous_stage=prev_stage,
            new_stage=stage,
            action_by_id=session.get('user_id'),
            action_type='JOURNEY_STAGE_UPDATE',
            comments=f"Lifecycle journey stage updated from '{prev_stage}' to '{stage}'.",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log)
        db.session.commit()
        flash(f"Batch #{batch.batch_code} journey timeline advanced to '{stage}'.", 'success')
    else:
        flash('Invalid journey stage.', 'danger')

    return redirect(url_for('traceability.traceability_view', batch_code=batch.batch_code))


from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from extensions import db
from models.user import User
from models.product import Product
from models.order import Order
from models.harvest import HarvestBatch
from models.verification_log import BatchVerificationLog
from services.verification_service import (
    record_stage_change,
    VALID_STAGES,
    STAGE_CONFIG,
    generate_qr_data_uri
)
from routes.auth import login_required, role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
@role_required('ADMIN')
def admin_view():
    filter_stage = request.args.get('stage', 'All').strip()
    
    users = User.query.order_by(User.created_at.desc()).all()
    products = Product.query.order_by(Product.created_at.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    all_batches = HarvestBatch.query.order_by(HarvestBatch.created_at.desc()).all()
    if filter_stage != 'All' and filter_stage in VALID_STAGES:
        batches = [b for b in all_batches if b.verification_stage == filter_stage]
    else:
        batches = all_batches

    stage_counts = {stage: sum(1 for b in all_batches if b.verification_stage == stage) for stage in VALID_STAGES}

    stats = {
        'total_users': len(users),
        'total_farmers': sum(1 for u in users if u.role == 'FARMER'),
        'total_buyers': sum(1 for u in users if u.role == 'BUYER'),
        'total_products': len(products),
        'total_orders': len(orders),
        'total_batches': len(all_batches),
        'verified_batches': stage_counts.get('Quality Verified', 0),
        'pending_batches': stage_counts.get('Submitted', 0) + stage_counts.get('Under Review', 0),
        'action_required_batches': stage_counts.get('Action Required', 0),
        'rejected_batches': stage_counts.get('Rejected', 0),
        'stage_counts': stage_counts
    }

    return render_template(
        'admin.html',
        stats=stats,
        users=users,
        products=products,
        orders=orders,
        batches=batches,
        current_stage_filter=filter_stage,
        stage_config=STAGE_CONFIG,
        valid_stages=VALID_STAGES
    )

@admin_bp.route('/admin/batches/<int:id>/review', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def review_batch(id):
    batch = db.session.get(HarvestBatch, id)
    if not batch:
        abort(404)
    
    if request.method == 'POST':
        new_stage = request.form.get('verification_stage', '').strip()
        review_reason = request.form.get('review_reason', '').strip()
        internal_notes = request.form.get('internal_notes', '').strip()
        quality_score_str = request.form.get('quality_score', '90').strip()
        quality_grade = request.form.get('quality_grade', batch.quality_grade).strip()
        verifier_name = request.form.get('verifier_name', '').strip()

        if new_stage not in VALID_STAGES:
            flash(f"Invalid verification stage. Must be one of: {', '.join(VALID_STAGES)}.", 'danger')
            return redirect(url_for('admin.review_batch', id=batch.id))

        if new_stage in ['Action Required', 'Rejected'] and not review_reason:
            flash('A review reason/feedback is required when requesting corrections or rejecting a batch.', 'danger')
            return redirect(url_for('admin.review_batch', id=batch.id))

        try:
            score = int(quality_score_str)
            if score < 0 or score > 100:
                score = 90
        except ValueError:
            score = 90

        admin_user = db.session.get(User, session['user_id'])
        admin_name = verifier_name if verifier_name else f"AgriTrust Certified Inspector ({admin_user.full_name or admin_user.username})"

        # Execute transition and immutable audit logging
        record_stage_change(
            batch=batch,
            new_stage=new_stage,
            actor_id=admin_user.id,
            action_type=f"ADMIN_{new_stage.upper().replace(' ', '_')}",
            comments=review_reason,
            internal_notes=internal_notes,
            quality_score=score,
            quality_grade=quality_grade,
            verifier_name=admin_name
        )

        flash(f"Batch #{batch.batch_code} verification updated to '{new_stage}'! Audit timestamp and administrative rationale recorded.", 'success')
        return redirect(url_for('admin.admin_view'))

    # GET: render dedicated inspection detail page
    trace_url = url_for('traceability.batch_detail', batch_code=batch.batch_code, _external=True)
    qr_data_uri = generate_qr_data_uri(trace_url)
    
    return render_template(
        'admin_batch_review.html',
        batch=batch,
        qr_data_uri=qr_data_uri,
        stage_config=STAGE_CONFIG,
        valid_stages=VALID_STAGES
    )

@admin_bp.route('/admin/users/<int:id>/role', methods=['POST'])
@login_required
@role_required('ADMIN')
def change_user_role(id):
    user = db.session.get(User, id)
    if not user:
        abort(404)
    new_role = request.form.get('role')
    if new_role in ['FARMER', 'BUYER', 'ADMIN']:
        # SEC-05: Prevent administrator self-demotion lockout and preserve active admin
        if user.role == 'ADMIN' and new_role != 'ADMIN':
            active_admin_count = User.query.filter_by(role='ADMIN').count()
            if active_admin_count <= 1:
                flash('Cannot demote administrator: At least one active administrator is required.', 'danger')
                return redirect(url_for('admin.admin_view'))
            if user.id == session.get('user_id'):
                flash('Cannot demote your own account: Administrators cannot self-demote.', 'warning')
                return redirect(url_for('admin.admin_view'))
        user.role = new_role
        db.session.commit()
        flash(f"User {user.username} role updated to {new_role}.", 'success')
    return redirect(url_for('admin.admin_view'))

@admin_bp.route('/admin/batches/<int:id>/verify', methods=['POST'])
@login_required
@role_required('ADMIN')
def verify_batch(id):
    batch = db.session.get(HarvestBatch, id)
    if not batch:
        abort(404)
    admin_user = db.session.get(User, session['user_id'])
    
    record_stage_change(
        batch=batch,
        new_stage='Quality Verified',
        actor_id=admin_user.id,
        action_type='ADMIN_QUALITY_VERIFIED',
        comments='Batch officially verified and audited via admin quick approval.',
        internal_notes='Quick approval granted from administrative control center.',
        quality_score=batch.quality_score or 90,
        quality_grade=batch.quality_grade or 'Grade A',
        verifier_name=f"AgriTrust Certified Quality Inspector ({admin_user.full_name or admin_user.username})"
    )
    
    flash(f"Batch #{batch.batch_code} officially Quality Verified and audited!", 'success')
    return redirect(url_for('admin.admin_view'))

@admin_bp.route('/admin/batches/<int:id>/lifecycle-stage', methods=['POST'])
@login_required
@role_required('ADMIN')
def update_lifecycle_stage(id):
    batch = db.session.get(HarvestBatch, id)
    if not batch:
        abort(404)
    new_stage = request.form.get('journey_stage', '').strip()
    allowed_stages = ['Harvested', 'Quality Check', 'Packaging', 'In Transit', 'Delivered']
    
    if new_stage not in allowed_stages:
        flash('Invalid lifecycle stage.', 'danger')
        return redirect(url_for('admin.admin_view') + '#harvest-lifecycle-management')
        
    old_stage = batch.journey_stage
    batch.journey_stage = new_stage
    if new_stage == 'Packaging' and not batch.packaging_date:
        batch.packaging_date = datetime.now(timezone.utc).date()
    elif new_stage == 'In Transit' and not batch.dispatch_date:
        batch.dispatch_date = datetime.now(timezone.utc).date()
        
    admin_user = db.session.get(User, session['user_id'])
    log = BatchVerificationLog(
        batch_id=batch.id,
        previous_stage=batch.verification_stage,
        new_stage=batch.verification_stage,
        action_by_id=admin_user.id,
        action_type='LIFECYCLE_STAGE_UPDATED',
        comments=f"Admin advanced post-harvest lifecycle stage from '{old_stage}' to '{new_stage}'.",
        internal_notes="Admin post-harvest lifecycle management update.",
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f"Batch #{batch.batch_code} lifecycle stage updated to '{new_stage}'!", 'success')
    return redirect(url_for('admin.admin_view') + '#harvest-lifecycle-management')

import uuid
import io
import base64
from datetime import datetime
from flask import url_for
from extensions import db
from models.harvest import HarvestBatch
from models.verification_log import BatchVerificationLog

VALID_STAGES = ['Submitted', 'Under Review', 'Action Required', 'Quality Verified', 'Rejected']

STAGE_CONFIG = {
    'Submitted': {
        'badge_class': 'badge-neutral',
        'color': '#475569',
        'bg': '#F1F5F9',
        'icon': '📝',
        'label': 'Submitted',
        'desc': 'Batch details registered and queued for verification.'
    },
    'Under Review': {
        'badge_class': 'badge-warning',
        'color': '#D97706',
        'bg': '#FEF3C7',
        'icon': '🔍',
        'label': 'Under Review',
        'desc': 'Admin inspector is actively evaluating specifications and evidence.'
    },
    'Action Required': {
        'badge_class': 'badge-danger',
        'color': '#DC2626',
        'bg': '#FEE2E2',
        'icon': '⚠️',
        'label': 'Action Required',
        'desc': 'Admin has requested corrections, clarifications, or updated evidence.'
    },
    'Quality Verified': {
        'badge_class': 'badge-success',
        'color': '#16A34A',
        'bg': '#DCFCE7',
        'icon': '🛡️',
        'label': 'Quality Verified',
        'desc': 'Passed independent quality assessment and origin verification.'
    },
    'Rejected': {
        'badge_class': 'badge-danger',
        'color': '#991B1B',
        'bg': '#FFE4E6',
        'icon': '❌',
        'label': 'Rejected',
        'desc': 'Verification declined with recorded administrative rationale.'
    }
}

def generate_uhvc_code():
    """
    Generates a cryptographically random, backend-enforced Unique Harvest Verification Code (UHVC).
    Checks database for absolute uniqueness.
    """
    year = datetime.utcnow().year
    for _ in range(20):
        code_suffix = uuid.uuid4().hex[:6].upper()
        code = f"UHVC-{year}-{code_suffix}"
        if not HarvestBatch.query.filter_by(batch_code=code).first():
            return code
    # Fallback to longer uuid if collision limit reached
    return f"UHVC-{year}-{uuid.uuid4().hex[:10].upper()}"

def record_stage_change(batch, new_stage, actor_id, action_type='STAGE_UPDATE', comments=None, internal_notes=None, quality_score=None, quality_grade=None, verifier_name=None):
    """
    Validates and executes a verification stage transition, logging full audit history.
    """
    if new_stage not in VALID_STAGES:
        raise ValueError(f"Invalid verification stage '{new_stage}'. Must be one of {VALID_STAGES}")

    old_stage = batch.verification_stage
    batch.verification_stage = new_stage
    batch.reviewed_by_id = actor_id
    batch.reviewed_at = datetime.utcnow()
    
    if comments:
        batch.admin_feedback = comments
        batch.review_reason = comments
    if internal_notes:
        batch.internal_notes = internal_notes
        
    if new_stage == 'Quality Verified':
        batch.verification_status = 'Verified'
        batch.is_independently_verified = True
        batch.verification_date = datetime.utcnow().date()
        if quality_score is not None:
            batch.quality_score = int(quality_score)
        if quality_grade:
            batch.quality_grade = quality_grade
        if verifier_name:
            batch.verifier_name = verifier_name
        else:
            batch.verifier_name = "AgriTrust Certified Quality Inspector"
    else:
        batch.is_independently_verified = False
        batch.verification_status = new_stage

    # Create immutable audit log entry
    log_entry = BatchVerificationLog(
        batch_id=batch.id,
        previous_stage=old_stage,
        new_stage=new_stage,
        action_by_id=actor_id,
        action_type=action_type,
        comments=comments,
        internal_notes=internal_notes,
        created_at=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry

def trigger_farmer_re_review(batch, actor_id, reason="Farmer modified batch specifications or evidence."):
    """
    When a farmer edits verified/under-review specifications, invalidates previous approval
    and resets stage to 'Submitted' for mandatory re-review.
    """
    old_stage = batch.verification_stage
    batch.verification_stage = 'Submitted'
    batch.verification_status = 'Pending Re-review'
    batch.is_independently_verified = False
    
    log_entry = BatchVerificationLog(
        batch_id=batch.id,
        previous_stage=old_stage,
        new_stage='Submitted',
        action_by_id=actor_id,
        action_type='RE_REVIEW_REQUIRED',
        comments=reason,
        internal_notes="Automatically triggered re-review due to farmer specification modification.",
        created_at=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry

def generate_qr_data_uri(target_url):
    """Generates a base64 PNG data URI for a QR code linking to target_url"""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E3A1E", back_color="#FFFFFF")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"Error generating QR code data URI: {e}")
        return ""

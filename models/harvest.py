from datetime import datetime
import uuid
from extensions import db

class HarvestBatch(db.Model):
    __tablename__ = 'harvest_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(50), unique=True, nullable=False, index=True, default=lambda: f"UHVC-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Farmer
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=True, index=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=True, index=True)
    crop_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(80), nullable=False, default='Vegetables')
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=True)
    harvest_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in kg or unit
    unit = db.Column(db.String(20), nullable=False, default='kg')
    asking_price = db.Column(db.Float, nullable=True, default=0.0)
    image_url = db.Column(db.String(255), nullable=True)
    document_url = db.Column(db.String(255), nullable=True)
    document_name = db.Column(db.String(150), nullable=True)
    
    # Verification and Quality
    # Stages: 'Submitted', 'Under Review', 'Action Required', 'Quality Verified', 'Rejected'
    verification_stage = db.Column(db.String(50), nullable=False, default='Submitted')
    verification_status = db.Column(db.String(50), nullable=False, default='Registered')  # Kept for backward compatibility
    is_independently_verified = db.Column(db.Boolean, default=False)
    verifier_name = db.Column(db.String(120), nullable=True)
    verification_date = db.Column(db.Date, nullable=True)
    quality_grade = db.Column(db.String(50), nullable=False, default='Grade A')
    quality_score = db.Column(db.Integer, nullable=False, default=90)  # out of 100
    
    # Admin Review Details
    admin_feedback = db.Column(db.Text, nullable=True)  # Shareable with farmer
    internal_notes = db.Column(db.Text, nullable=True)  # Internal admin review only
    review_reason = db.Column(db.Text, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Product Journey Timeline
    journey_stage = db.Column(db.String(50), nullable=False, default='Harvested')  
    # Farm -> Harvested -> Verification -> Quality Check -> Packaging -> In Transit -> Delivered
    
    storage_conditions = db.Column(db.String(150), nullable=True, default='Cool Dry Warehouse (18°C)')
    packaging_date = db.Column(db.Date, nullable=True)
    dispatch_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])

    @property
    def is_verified(self):
        return self.verification_stage == 'Quality Verified'

from datetime import datetime
from extensions import db

class BatchVerificationLog(db.Model):
    __tablename__ = 'batch_verification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('harvest_batches.id'), nullable=False, index=True)
    previous_stage = db.Column(db.String(50), nullable=True)
    new_stage = db.Column(db.String(50), nullable=False)
    action_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False)  # INITIAL_SUBMISSION, STAGE_UPDATE, CORRECTION_SUBMITTED, DETAILS_EDITED
    comments = db.Column(db.Text, nullable=True)  # Review reason or feedback shared with farmer
    internal_notes = db.Column(db.Text, nullable=True)  # Internal admin notes (private)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = db.relationship('HarvestBatch', backref=db.backref('verification_history', order_by='BatchVerificationLog.created_at.desc()', lazy=True, cascade='all, delete-orphan'))
    actor = db.relationship('User', foreign_keys=[action_by_id])

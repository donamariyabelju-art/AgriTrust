from datetime import datetime
from extensions import db

class CropHealthScan(db.Model):
    __tablename__ = 'crop_health_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    crop_name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    detected_disease = db.Column(db.String(150), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)  # percentage 0.0 to 100.0
    health_status = db.Column(db.String(50), nullable=False)  # Healthy, Early Stage, Critical
    symptoms = db.Column(db.Text, nullable=True)
    possible_causes = db.Column(db.Text, nullable=True)
    preventive_measures = db.Column(db.Text, nullable=True)
    recommended_steps = db.Column(db.Text, nullable=True)
    is_demo_mode = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    farmer = db.relationship('User', backref='health_scans')

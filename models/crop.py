from datetime import datetime
from extensions import db

class Crop(db.Model):
    __tablename__ = 'crops'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=True, index=True)
    crop_name = db.Column(db.String(100), nullable=False)
    planting_date = db.Column(db.Date, nullable=False)
    growth_stage = db.Column(db.String(80), nullable=False, default='Vegetative')  # Germination, Vegetative, Flowering, Fruiting, Maturation, Harvest Ready
    growth_percentage = db.Column(db.Integer, nullable=False, default=10)  # 0 to 100
    expected_harvest_date = db.Column(db.Date, nullable=False)
    expected_yield = db.Column(db.Float, nullable=False)  # in kg
    production_cost = db.Column(db.Float, nullable=False, default=0.0)  # in currency units
    expected_revenue = db.Column(db.Float, nullable=False, default=0.0)  # in currency units
    health_status = db.Column(db.String(50), nullable=False, default='Healthy')  # Healthy, Moderate Risk, Action Required, Disease Detected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    harvest_batches = db.relationship('HarvestBatch', backref='crop', lazy=True)
    products = db.relationship('Product', backref='crop', lazy=True)

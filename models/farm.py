from datetime import datetime
from extensions import db

class Farm(db.Model):
    __tablename__ = 'farms'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    land_area = db.Column(db.Float, nullable=False)  # in acres
    soil_type = db.Column(db.String(80), nullable=False)  # Alluvial, Black, Red, Clay, Sandy, Loamy
    irrigation_method = db.Column(db.String(100), nullable=False)  # Drip, Sprinkler, Flood, Rainfed, Canal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    crops = db.relationship('Crop', backref='farm', lazy=True, cascade='all, delete-orphan')
    harvest_batches = db.relationship('HarvestBatch', backref='farm', lazy=True)

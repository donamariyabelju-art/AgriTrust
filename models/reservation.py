from datetime import datetime
from extensions import db

class FutureHarvest(db.Model):
    """Farmer listed future harvest available for advance reservation"""
    __tablename__ = 'future_harvests'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    crop_name = db.Column(db.String(100), nullable=False)
    expected_harvest_date = db.Column(db.Date, nullable=False)
    expected_quantity = db.Column(db.Float, nullable=False)  # Total expected in kg
    reserved_quantity = db.Column(db.Float, nullable=False, default=0.0)
    target_price_per_kg = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Open for Reservation')  # Open for Reservation, Fully Reserved, Harvested, Cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    farmer = db.relationship('User', foreign_keys=[farmer_id], backref='future_harvests')
    reservations = db.relationship('Reservation', backref='future_harvest', lazy=True, cascade='all, delete-orphan')

    @property
    def remaining_quantity(self):
        return max(0.0, self.expected_quantity - self.reserved_quantity)


class Reservation(db.Model):
    """Buyer reservation placed on an upcoming harvest"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Buyer
    future_harvest_id = db.Column(db.Integer, db.ForeignKey('future_harvests.id'), nullable=True, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    crop_name = db.Column(db.String(100), nullable=False)
    reserved_quantity = db.Column(db.Float, nullable=False)  # in kg
    unit_price = db.Column(db.Float, nullable=False)
    total_estimated_amount = db.Column(db.Float, nullable=False)
    expected_harvest_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Confirmed')  # Confirmed, Harvest Ready, Fulfilled, Cancelled
    contact_phone = db.Column(db.String(20), nullable=True)
    delivery_address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    farmer_user = db.relationship('User', foreign_keys=[farmer_id])

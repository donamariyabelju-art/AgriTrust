from datetime import datetime
from extensions import db

class BuyerDemand(db.Model):
    __tablename__ = 'buyer_demands'
    
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    crop_name = db.Column(db.String(100), nullable=False)
    required_quantity = db.Column(db.Float, nullable=False)  # in kg
    available_supply = db.Column(db.Float, nullable=False, default=0.0)
    unit = db.Column(db.String(20), nullable=False, default='kg')
    location = db.Column(db.String(150), nullable=False)
    demand_level = db.Column(db.String(30), nullable=False, default='High')  # High, Urgent, Moderate
    target_price = db.Column(db.Float, nullable=True)  # offering price per kg
    required_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='Active')  # Active, Fulfilled, Closed
    hvc_code = db.Column(db.String(50), nullable=True)  # Optional demanded HVC/UHVC code
    is_sample_data = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    buyer = db.relationship('User', backref='demands')

from datetime import datetime
import uuid
from extensions import db

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, default=lambda: f"ORD-{uuid.uuid4().hex[:8].upper()}")
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending Payment')  # Pending Payment, Processing, Dispatched, Delivered, Cancelled
    payment_status = db.Column(db.String(80), nullable=False, default='Pending Payment (Pay on Delivery / Demo)')  # Explicit demo/pending status per prompt
    delivery_address = db.Column(db.Text, nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with review
    review = db.relationship('Review', backref='order', uselist=False)

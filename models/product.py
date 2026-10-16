from datetime import datetime
from extensions import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=True, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('harvest_batches.id'), nullable=True, index=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False, default='Vegetables')  # Vegetables, Grains, Fruits, Pulses, Spices
    quantity = db.Column(db.Float, nullable=False)  # remaining available quantity
    initial_quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False, default='kg')  # kg, quintal, crate
    price_per_unit = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    harvest_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    quality_grade = db.Column(db.String(50), nullable=False, default='Grade A')  # Grade A, Grade B, Certified Organic
    description = db.Column(db.Text, nullable=True)
    availability_status = db.Column(db.String(30), nullable=False, default='Available')  # Available, Reserved, Sold Out
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='product', lazy=True)
    batch = db.relationship('HarvestBatch', backref=db.backref('products', lazy=True))

    @property
    def uhvc_code(self):
        return self.batch.batch_code if self.batch else None

    @property
    def verification_stage(self):
        return self.batch.verification_stage if self.batch else 'Submitted'

    @property
    def is_quality_verified(self):
        return self.batch.verification_stage == 'Quality Verified' if self.batch else False

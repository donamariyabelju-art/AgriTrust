from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='FARMER')  # FARMER, BUYER, ADMIN
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    farms = db.relationship('Farm', backref='farmer', lazy=True, cascade='all, delete-orphan')
    crops = db.relationship('Crop', backref='farmer', lazy=True, cascade='all, delete-orphan')
    products = db.relationship('Product', backref='farmer', lazy=True, cascade='all, delete-orphan')
    harvest_batches = db.relationship('HarvestBatch', backref='farmer', lazy=True, cascade='all, delete-orphan', foreign_keys='HarvestBatch.user_id')
    orders = db.relationship('Order', backref='buyer', lazy=True, foreign_keys='Order.buyer_id')
    reservations = db.relationship('Reservation', backref='buyer', lazy=True, foreign_keys='Reservation.user_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_farmer(self):
        return self.role == 'FARMER'
        
    @property
    def is_buyer(self):
        return self.role == 'BUYER'
        
    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    def get_trust_profile(self):
        """Calculate farmer trust metrics based strictly on recorded database data"""
        from models.order import Order
        from models.harvest import HarvestBatch
        from models.review import Review
        
        # Completed orders for this farmer's products
        completed_orders_count = Order.query.join(Order.product).filter(
            Order.product.has(user_id=self.id),
            Order.status == 'Delivered'
        ).count()
        
        # Total orders
        total_orders_count = Order.query.join(Order.product).filter(
            Order.product.has(user_id=self.id)
        ).count()
        
        # Verified harvest batches
        verified_batches = HarvestBatch.query.filter_by(user_id=self.id, verification_status='Verified').count()
        total_batches = HarvestBatch.query.filter_by(user_id=self.id).count()
        
        # Reviews
        reviews = Review.query.filter_by(farmer_id=self.id).all()
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0.0
        
        delivery_rate = round((completed_orders_count / total_orders_count * 100), 1) if total_orders_count > 0 else 100.0
        
        return {
            'completed_orders': completed_orders_count,
            'total_orders': total_orders_count,
            'verified_batches': verified_batches,
            'total_batches': total_batches,
            'reviews_count': len(reviews),
            'avg_rating': avg_rating,
            'delivery_reliability': delivery_rate,
            'reviews': reviews
        }

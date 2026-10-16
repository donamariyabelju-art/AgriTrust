import os
from flask import Flask, render_template, send_from_directory
from config import Config
from extensions import db
from datetime import datetime, date

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'scans'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.farms import farms_bp
    from routes.crops import crops_bp
    from routes.recommendations import recommendations_bp
    from routes.disease import disease_bp
    from routes.chatbot import chatbot_bp
    from routes.weather import weather_bp
    from routes.marketplace import marketplace_bp
    from routes.reservations import reservations_bp
    from routes.orders import orders_bp
    from routes.analytics import analytics_bp
    from routes.traceability import traceability_bp
    from routes.general import general_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(farms_bp)
    app.register_blueprint(crops_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(disease_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(traceability_bp)
    app.register_blueprint(general_bp)
    app.register_blueprint(admin_bp)

    # Main Index route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Uploads file server
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Auto-initialize database tables, migrations, and initial seeds
    with app.app_context():
        try:
            db.create_all()
            _migrate_database()
            _auto_seed_initial_data()
            _backfill_existing_batches()
        except Exception as e:
            print(f"[AgriTrust Warning] Database initialization check: {e}")

    return app

def _auto_seed_initial_data():
    """Seeds default sample records if database is empty"""
    from models.user import User
    from models.farm import Farm
    from models.crop import Crop
    from models.product import Product
    from models.demand import BuyerDemand
    from models.reservation import FutureHarvest, Reservation
    from models.harvest import HarvestBatch
    from models.order import Order
    from models.review import Review
    from models.notification import Notification

    if User.query.first():
        return  # Data already exists

    # 1. Create Default Users
    farmer = User(
        username='farmer1',
        email='farmer@agritrust.com',
        role='FARMER',
        full_name='Ramesh Patel',
        phone='+91 98765 43210',
        location='Nashik, Maharashtra',
        bio='Organic vegetable and grain farmer with over 15 years experience in sustainable agriculture.'
    )
    farmer.set_password('Farmer@123')

    buyer = User(
        username='buyer1',
        email='buyer@agritrust.com',
        role='BUYER',
        full_name='FreshMart Wholesale Co.',
        phone='+91 91234 56789',
        location='Mumbai, Maharashtra',
        bio='Procuring directly from regional growers to deliver farm-fresh harvest to urban communities.'
    )
    buyer.set_password('Buyer@123')

    admin = User(
        username='admin',
        email='admin@agritrust.com',
        role='ADMIN',
        full_name='AgriTrust Platform Admin',
        phone='+91 99999 88888',
        location='Pune, Maharashtra',
        bio='System administrator maintaining trust standards, marketplace integrity and agronomy intelligence.'
    )
    admin.set_password('Admin@123')

    db.session.add_all([farmer, buyer, admin])
    db.session.commit()

    # 2. Create Farms
    farm1 = Farm(
        user_id=farmer.id,
        name='Green Valley Organic Estate',
        location='Dindori Road, Nashik',
        land_area=6.5,
        soil_type='Black Soil (Regur)',
        irrigation_method='Drip Irrigation'
    )
    farm2 = Farm(
        user_id=farmer.id,
        name='Godavari Riverside Agro Farm',
        location='Niphad, Nashik',
        land_area=4.2,
        soil_type='Alluvial Soil',
        irrigation_method='Sprinkler & Canal'
    )
    db.session.add_all([farm1, farm2])
    db.session.commit()

    # 3. Create Crops
    crop1 = Crop(
        user_id=farmer.id,
        farm_id=farm1.id,
        crop_name='Tomato (Roma Hybrid)',
        planting_date=date(2026, 8, 15),
        growth_stage='Fruiting',
        growth_percentage=72,
        expected_harvest_date=date(2026, 10, 28),
        expected_yield=4200.0,
        production_cost=18500.0,
        expected_revenue=63000.0,
        health_status='Healthy'
    )
    crop2 = Crop(
        user_id=farmer.id,
        farm_id=farm1.id,
        crop_name='Cucumber (English Crispy)',
        planting_date=date(2026, 9, 1),
        growth_stage='Flowering',
        growth_percentage=55,
        expected_harvest_date=date(2026, 11, 10),
        expected_yield=2800.0,
        production_cost=11200.0,
        expected_revenue=39200.0,
        health_status='Healthy'
    )
    crop3 = Crop(
        user_id=farmer.id,
        farm_id=farm2.id,
        crop_name='Basmati Rice (Pusa 1121)',
        planting_date=date(2026, 7, 10),
        growth_stage='Maturation',
        growth_percentage=88,
        expected_harvest_date=date(2026, 10, 20),
        expected_yield=6500.0,
        production_cost=32000.0,
        expected_revenue=143000.0,
        health_status='Healthy'
    )
    crop4 = Crop(
        user_id=farmer.id,
        farm_id=farm2.id,
        crop_name='Grand Naine Banana',
        planting_date=date(2026, 3, 20),
        growth_stage='Vegetative',
        growth_percentage=40,
        expected_harvest_date=date(2026, 12, 15),
        expected_yield=8500.0,
        production_cost=41000.0,
        expected_revenue=127500.0,
        health_status='Moderate Risk'
    )
    db.session.add_all([crop1, crop2, crop3, crop4])
    db.session.commit()

    # 4. Create Products
    prod1 = Product(
        user_id=farmer.id,
        crop_id=crop1.id,
        title='Farm-Fresh Vine Tomatoes (Grade A)',
        category='Vegetables',
        quantity=1200.0,
        initial_quantity=1500.0,
        unit='kg',
        price_per_unit=22.0,
        location='Nashik, Maharashtra',
        harvest_date=date(2026, 10, 8),
        image_url='https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80',
        quality_grade='Grade A',
        description='Naturally ripened, pesticide-tested red tomatoes harvested fresh from the vine.',
        availability_status='Available'
    )
    prod2 = Product(
        user_id=farmer.id,
        crop_id=crop2.id,
        title='Crisp Green English Cucumbers',
        category='Vegetables',
        quantity=850.0,
        initial_quantity=1000.0,
        unit='kg',
        price_per_unit=18.0,
        location='Nashik, Maharashtra',
        harvest_date=date(2026, 10, 9),
        image_url='https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?auto=format&fit=crop&w=600&q=80',
        quality_grade='Grade A',
        description='Crunchy, thin-skinned English cucumbers cultivated under drip irrigation.',
        availability_status='Available'
    )
    prod3 = Product(
        user_id=farmer.id,
        crop_id=crop3.id,
        title='Aromatic Pusa Basmati Paddy Grain',
        category='Grains',
        quantity=3500.0,
        initial_quantity=3500.0,
        unit='kg',
        price_per_unit=38.0,
        location='Niphad, Maharashtra',
        harvest_date=date(2026, 10, 5),
        image_url='https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80',
        quality_grade='Certified Organic',
        description='Long-grain aromatic basmati paddy harvested naturally with low moisture content.',
        availability_status='Available'
    )
    db.session.add_all([prod1, prod2, prod3])
    db.session.commit()

    # 5. Future Harvests for all supported crops
    fh1 = FutureHarvest(
        farmer_id=farmer.id,
        crop_name='Red Bell Peppers (Capsicum)',
        expected_harvest_date=date(2026, 11, 5),
        expected_quantity=2000.0,
        reserved_quantity=500.0,
        target_price_per_kg=42.0,
        location='Nashik, Maharashtra',
        status='Open for Reservation',
        notes='High demand greenhouse crop. Advance booking locks price and guarantees immediate dispatch.'
    )
    fh2 = FutureHarvest(
        farmer_id=farmer.id,
        crop_name='Farm-Fresh Vine Tomatoes (Grade A)',
        expected_harvest_date=date(2026, 11, 10),
        expected_quantity=3000.0,
        reserved_quantity=0.0,
        target_price_per_kg=22.0,
        location='Nashik, Maharashtra',
        status='Open for Reservation',
        notes='Grade A greenhouse vine tomatoes nearing harvest. Available for bulk advance procurement.'
    )
    fh3 = FutureHarvest(
        farmer_id=farmer.id,
        crop_name='Crisp Green English Cucumbers',
        expected_harvest_date=date(2026, 11, 12),
        expected_quantity=2500.0,
        reserved_quantity=0.0,
        target_price_per_kg=24.0,
        location='Pune, Maharashtra',
        status='Open for Reservation',
        notes='High-yield parthenocarpic English cucumbers under protected polyhouse cultivation.'
    )
    fh4 = FutureHarvest(
        farmer_id=farmer.id,
        crop_name='Aromatic Pusa Basmati Paddy Grain',
        expected_harvest_date=date(2026, 11, 20),
        expected_quantity=6000.0,
        reserved_quantity=0.0,
        target_price_per_kg=45.0,
        location='Karnal, Haryana',
        status='Open for Reservation',
        notes='Certified organic aromatic basmati harvest batch available for wholesale flour mills and retail chains.'
    )
    fh5 = FutureHarvest(
        farmer_id=farmer.id,
        crop_name='Fresh Robusta Bananas (Export Grade)',
        expected_harvest_date=date(2026, 11, 15),
        expected_quantity=4000.0,
        reserved_quantity=0.0,
        target_price_per_kg=18.0,
        location='Jalgaon, Maharashtra',
        status='Open for Reservation',
        notes='Uniform Cavendish Robusta bananas grown with precision drip irrigation.'
    )
    db.session.add_all([fh1, fh2, fh3, fh4, fh5])
    db.session.commit()

    # 6. Reservation
    res1 = Reservation(
        user_id=buyer.id,
        future_harvest_id=fh1.id,
        farmer_id=farmer.id,
        crop_name='Red Bell Peppers (Capsicum)',
        reserved_quantity=500.0,
        unit_price=42.0,
        total_estimated_amount=21000.0,
        expected_harvest_date=date(2026, 11, 5),
        status='Confirmed',
        contact_phone='+91 91234 56789',
        delivery_address='FreshMart Central Cold Hub, Vashi APMC, Navi Mumbai',
        notes='Advance reservation locked for November delivery batch.'
    )
    db.session.add(res1)

    # 7. Harvest Batch & Traceability
    batch1 = HarvestBatch(
        batch_code='BATCH-2026-TM981',
        user_id=farmer.id,
        farm_id=farm1.id,
        crop_id=crop1.id,
        crop_name='Tomato (Roma Hybrid)',
        category='Vegetables',
        description='Naturally ripened, pesticide-tested red tomatoes harvested fresh from the vine.',
        harvest_date=date(2026, 10, 8),
        quantity=1500.0,
        unit='kg',
        asking_price=22.0,
        location='Nashik, Maharashtra',
        verification_stage='Quality Verified',
        verification_status='Verified',
        is_independently_verified=True,
        verifier_name='Nashik Agri Quality Inspection Agency',
        quality_grade='Grade A',
        quality_score=94,
        reviewed_by_id=admin.id,
        reviewed_at=datetime.utcnow(),
        journey_stage='Packaging',
        storage_conditions='Cold storage (12°C, 85% RH)',
        packaging_date=date(2026, 10, 10),
        notes='Pesticide residue test passed with zero banned synthetic chemical residues.'
    )
    db.session.add(batch1)
    db.session.flush()

    batch2 = HarvestBatch(
        batch_code='UHVC-2026-CU882',
        user_id=farmer.id,
        farm_id=farm1.id,
        crop_id=crop2.id,
        crop_name='Cucumber (English Crispy)',
        category='Vegetables',
        description='Crunchy, thin-skinned English cucumbers cultivated under drip irrigation.',
        harvest_date=date(2026, 10, 9),
        quantity=1000.0,
        unit='kg',
        asking_price=18.0,
        location='Nashik, Maharashtra',
        verification_stage='Quality Verified',
        verification_status='Verified',
        is_independently_verified=True,
        verifier_name='AgriTrust Certified Quality Inspector',
        quality_grade='Grade A',
        quality_score=92,
        reviewed_by_id=admin.id,
        reviewed_at=datetime.utcnow(),
        journey_stage='Packaging',
        storage_conditions='Cool Dry Warehouse (16°C)',
        notes='Moisture content calibrated. Certified pesticide residue safe.'
    )
    db.session.add(batch2)
    db.session.flush()

    batch3 = HarvestBatch(
        batch_code='UHVC-2026-BS311',
        user_id=farmer.id,
        farm_id=farm2.id,
        crop_id=crop3.id,
        crop_name='Basmati Rice (Pusa 1121)',
        category='Grains',
        description='Long-grain aromatic basmati paddy harvested naturally with low moisture content.',
        harvest_date=date(2026, 10, 5),
        quantity=3500.0,
        unit='kg',
        asking_price=38.0,
        location='Niphad, Maharashtra',
        verification_stage='Quality Verified',
        verification_status='Verified',
        is_independently_verified=True,
        verifier_name='Organic Standards Board Auditor',
        quality_grade='Certified Organic',
        quality_score=96,
        reviewed_by_id=admin.id,
        reviewed_at=datetime.utcnow(),
        journey_stage='Packaging',
        storage_conditions='Aired Grain Silo',
        notes='100% Organic certified origin lot.'
    )
    db.session.add(batch3)
    db.session.flush()

    prod1.batch_id = batch1.id
    prod2.batch_id = batch2.id
    prod3.batch_id = batch3.id

    from models.verification_log import BatchVerificationLog
    for b in [batch1, batch2, batch3]:
        log = BatchVerificationLog(
            batch_id=b.id,
            previous_stage='Submitted',
            new_stage='Quality Verified',
            action_by_id=admin.id,
            action_type='ADMIN_QUALITY_VERIFIED',
            comments='Full chemical assay and origin audit passed successfully.',
            internal_notes='Approved during platform onboarding.',
            created_at=datetime.utcnow()
        )
        db.session.add(log)

    # 8. Buyer Demand
    dem1 = BuyerDemand(
        buyer_id=buyer.id,
        crop_name='Ripe Tomato (Processing Grade)',
        required_quantity=5000.0,
        available_supply=1200.0,
        unit='kg',
        location='Mumbai Wholesale Terminal',
        demand_level='High',
        target_price=21.0,
        required_date=date(2026, 10, 30),
        description='Bulk requirement for urban grocery store network. Direct farmer delivery preferred.',
        status='Active',
        is_sample_data=False
    )
    db.session.add(dem1)

    # 9. Order
    ord1 = Order(
        order_number='ORD-2026-E49A11',
        buyer_id=buyer.id,
        product_id=prod1.id,
        quantity=300.0,
        unit_price=22.0,
        total_amount=6600.0,
        status='Delivered',
        payment_status='Paid (Demo)',
        delivery_address='FreshMart Store #14, Bandra West, Mumbai',
        contact_phone='+91 91234 56789',
        notes='Order completed with verified direct delivery.'
    )
    db.session.add(ord1)
    db.session.commit()

    # 10. Review
    rev1 = Review(
        order_id=ord1.id,
        buyer_id=buyer.id,
        farmer_id=farmer.id,
        rating=5,
        comment='Exceptional produce freshness! The tomatoes arrived uniformly graded with zero transit damage. Direct farmer buying made pricing transparent.'
    )
    db.session.add(rev1)

    # 11. Notification
    notif1 = Notification(
        user_id=farmer.id,
        title='Farming Alert: Pest Scouting Window',
        message='Weather conditions favorable for early leaf spot in high-humidity zones. Inspect lower leaves today.',
        category='alert',
        is_read=False
    )
    db.session.add(notif1)
    db.session.commit()

def _migrate_database():
    """Migrates existing SQLite schema to include verification fields and tables without data loss"""
    from sqlalchemy import text
    try:
        # Check harvest_batches columns
        result = db.session.execute(text("PRAGMA table_info(harvest_batches)")).fetchall()
        existing_cols = {row[1] for row in result}
        
        batch_col_defs = [
            ("category", "VARCHAR(80) DEFAULT 'Vegetables'"),
            ("description", "TEXT"),
            ("location", "VARCHAR(150)"),
            ("asking_price", "FLOAT DEFAULT 0.0"),
            ("image_url", "VARCHAR(255)"),
            ("document_url", "VARCHAR(255)"),
            ("document_name", "VARCHAR(150)"),
            ("verification_stage", "VARCHAR(50) DEFAULT 'Submitted'"),
            ("admin_feedback", "TEXT"),
            ("internal_notes", "TEXT"),
            ("review_reason", "TEXT"),
            ("reviewed_by_id", "INT"),
            ("reviewed_at", "DATETIME"),
            ("updated_at", "DATETIME")
        ]
        
        for col_name, col_type in batch_col_defs:
            if col_name not in existing_cols:
                db.session.execute(text(f"ALTER TABLE harvest_batches ADD COLUMN {col_name} {col_type}"))
                
        # Check products columns
        prod_result = db.session.execute(text("PRAGMA table_info(products)")).fetchall()
        existing_prod_cols = {row[1] for row in prod_result}
        if "batch_id" not in existing_prod_cols:
            db.session.execute(text("ALTER TABLE products ADD COLUMN batch_id INT"))

        # Check buyer_demands columns
        dem_result = db.session.execute(text("PRAGMA table_info(buyer_demands)")).fetchall()
        existing_dem_cols = {row[1] for row in dem_result}
        if "hvc_code" not in existing_dem_cols:
            db.session.execute(text("ALTER TABLE buyer_demands ADD COLUMN hvc_code VARCHAR(50)"))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[AgriTrust Migration Notice] {e}")

def _backfill_existing_batches():
    """Ensure existing batches and products are linked and have UHVC & verification stages"""
    from models.harvest import HarvestBatch
    from models.product import Product
    from models.user import User
    from models.verification_log import BatchVerificationLog
    from services.verification_service import generate_uhvc_code
    try:
        admin_user = User.query.filter_by(role='ADMIN').first()
        admin_id = admin_user.id if admin_user else 3

        # Backfill batch 1 (TM981) if stage not set
        b1 = HarvestBatch.query.filter_by(batch_code='BATCH-2026-TM981').first()
        if b1:
            if not b1.verification_stage or b1.verification_stage == 'Submitted':
                b1.verification_stage = 'Quality Verified'
                b1.verification_status = 'Verified'
                b1.is_independently_verified = True
                b1.category = 'Vegetables'
                b1.asking_price = 22.0
                b1.reviewed_by_id = admin_id
                b1.reviewed_at = datetime.utcnow()
                db.session.commit()
            
            if not BatchVerificationLog.query.filter_by(batch_id=b1.id).first():
                log = BatchVerificationLog(
                    batch_id=b1.id,
                    previous_stage='Submitted',
                    new_stage='Quality Verified',
                    action_by_id=admin_id,
                    action_type='ADMIN_QUALITY_VERIFIED',
                    comments='Passed independent pesticide residue and agronomy quality audit with Grade A ranking.',
                    internal_notes='Field inspection verified zero synthetic chemical residues. Origin traceability approved.',
                    created_at=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()

        # Link products to batches if batch_id is None
        products = Product.query.filter_by(batch_id=None).all()
        for prod in products:
            if b1 and prod.crop_id == b1.crop_id:
                prod.batch_id = b1.id
            else:
                batch_code = generate_uhvc_code()
                new_b = HarvestBatch(
                    batch_code=batch_code,
                    user_id=prod.user_id,
                    crop_id=prod.crop_id,
                    crop_name=prod.title.split('(')[0].strip(),
                    category=prod.category,
                    description=prod.description,
                    harvest_date=prod.harvest_date,
                    quantity=prod.quantity,
                    unit=prod.unit,
                    asking_price=prod.price_per_unit,
                    location=prod.location,
                    image_url=prod.image_url,
                    quality_grade=prod.quality_grade,
                    verification_stage='Quality Verified',
                    verification_status='Verified',
                    is_independently_verified=True,
                    verifier_name='AgriTrust Certified Quality Inspector',
                    reviewed_by_id=admin_id,
                    reviewed_at=datetime.utcnow()
                )
                db.session.add(new_b)
                db.session.flush()
                prod.batch_id = new_b.id
                
                log = BatchVerificationLog(
                    batch_id=new_b.id,
                    previous_stage='Submitted',
                    new_stage='Quality Verified',
                    action_by_id=admin_id,
                    action_type='ADMIN_QUALITY_VERIFIED',
                    comments='Produce batch audited and approved for direct marketplace trading.',
                    created_at=datetime.utcnow()
                )
                db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[AgriTrust Backfill Notice] {e}")

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

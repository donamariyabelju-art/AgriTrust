import pytest
import io
from app import create_app
from config import Config
from extensions import db
from models.user import User
from models.harvest import HarvestBatch
from models.product import Product
from models.verification_log import BatchVerificationLog
from services.verification_service import generate_uhvc_code, VALID_STAGES
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_uhvc_automatic_generation(app):
    """Test that a new batch automatically receives a unique UHVC code on the backend"""
    with app.app_context():
        code1 = generate_uhvc_code()
        code2 = generate_uhvc_code()
        assert code1.startswith("UHVC-")
        assert code2.startswith("UHVC-")
        assert code1 != code2

def test_batch_code_database_uniqueness(app):
    """Test that duplicate batch codes are rejected by database uniqueness constraint"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        duplicate_code = "UHVC-2026-TESTDUP1"

        b1 = HarvestBatch(
            batch_code=duplicate_code,
            user_id=farmer.id,
            crop_name="Organic Wheat",
            harvest_date=date(2026, 10, 1),
            quantity=100.0,
            unit="kg",
            verification_stage="Submitted"
        )
        db.session.add(b1)
        db.session.commit()

        b2 = HarvestBatch(
            batch_code=duplicate_code,
            user_id=farmer.id,
            crop_name="Organic Wheat Duplicate",
            harvest_date=date(2026, 10, 2),
            quantity=200.0,
            unit="kg",
            verification_stage="Submitted"
        )
        db.session.add(b2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_farmer_batch_registration_generates_uhvc(client, app):
    """Test farmer registering a batch in marketplace generates UHVC and stage=Submitted"""
    # Login as farmer
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'}, follow_redirects=True)

    prod_data = {
        'title': 'Test Alphonso Mangoes',
        'category': 'Fruits',
        'quantity': '500',
        'unit': 'kg',
        'price_per_unit': '120.0',
        'location': 'Ratnagiri, Maharashtra',
        'harvest_date': '2026-10-15',
        'quality_grade': 'Grade A',
        'description': 'Export quality naturally ripened alphonso mangoes.'
    }
    res = client.post('/products/create', data=prod_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"registered with UHVC #UHVC-" in res.data

    with app.app_context():
        batch = HarvestBatch.query.filter_by(crop_name='Test Alphonso Mangoes').first()
        assert batch is not None
        assert batch.batch_code.startswith("UHVC-")
        assert batch.verification_stage == 'Submitted'
        assert batch.is_independently_verified is False
        assert len(batch.verification_history) >= 1
        assert batch.verification_history[0].new_stage == 'Submitted'

def test_farmer_cannot_approve_own_batch_or_change_stages(client, app):
    """Test farmer is strictly forbidden from directly changing verification stage or approving batch"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        batch = HarvestBatch.query.filter_by(user_id=farmer.id).first()
        batch_id = batch.id

    # 1. Without logging in as admin (logged in as farmer)
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'}, follow_redirects=True)
    
    # Attempt to post to admin review endpoint
    hack_res = client.post(f'/admin/batches/{batch_id}/review', data={
        'verification_stage': 'Quality Verified',
        'review_reason': 'Self approved'
    }, follow_redirects=True)
    
    # Must be forbidden or denied
    assert hack_res.status_code in [403, 302] or b"Access denied" in hack_res.data or b"Unauthorized" in hack_res.data
    
    with app.app_context():
        # Verify batch was NOT changed by the unauthorized farmer request
        b = HarvestBatch.query.get(batch_id)
        # Should not have been changed by farmer
        log = BatchVerificationLog.query.filter_by(batch_id=batch_id, comments='Self approved').first()
        assert log is None

def test_admin_quality_review_workflow_and_audit_history(client, app):
    """Test authenticated admin reviews batch, records decision, updates stage, and saves audit log"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        admin = User.query.filter_by(role='ADMIN').first()
        admin_id = admin.id
        
        # Create a fresh test batch in Submitted stage
        batch = HarvestBatch(
            batch_code=generate_uhvc_code(),
            user_id=farmer.id,
            crop_name="Audit Test Capsicum",
            category="Vegetables",
            harvest_date=date(2026, 10, 10),
            quantity=250.0,
            unit="kg",
            asking_price=45.0,
            location="Nashik Greenhouse #4",
            verification_stage="Submitted"
        )
        db.session.add(batch)
        db.session.commit()
        batch_id = batch.id

    # 1. Login as Admin
    client.get('/logout')
    login_res = client.post('/login', data={'login_input': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    assert login_res.status_code == 200

    # 2. View dedicated admin review page
    rev_get = client.get(f'/admin/batches/{batch_id}/review')
    assert rev_get.status_code == 200
    assert b"Audit Test Capsicum" in rev_get.data
    assert b"Record Quality Verification Decision" in rev_get.data

    # 3. Transition to 'Under Review'
    res_under_review = client.post(f'/admin/batches/{batch_id}/review', data={
        'verification_stage': 'Under Review',
        'review_reason': 'Assigned inspector to verify drip irrigation and residue certificates.',
        'internal_notes': 'Internal check started.'
    }, follow_redirects=True)
    assert res_under_review.status_code == 200

    with app.app_context():
        b = HarvestBatch.query.get(batch_id)
        assert b.verification_stage == 'Under Review'
        assert b.is_independently_verified is False
        assert len(b.verification_history) == 1
        assert b.verification_history[0].new_stage == 'Under Review'
        assert b.verification_history[0].action_by_id == admin_id

    # 4. Request corrections: 'Action Required'
    res_action_req = client.post(f'/admin/batches/{batch_id}/review', data={
        'verification_stage': 'Action Required',
        'review_reason': 'Please attach accredited soil pH analysis certificate.',
        'internal_notes': 'Awaiting revised soil report.'
    }, follow_redirects=True)
    assert res_action_req.status_code == 200

    with app.app_context():
        b = HarvestBatch.query.get(batch_id)
        assert b.verification_stage == 'Action Required'
        assert b.admin_feedback == 'Please attach accredited soil pH analysis certificate.'

    # 5. Finally Approve: 'Quality Verified'
    res_approved = client.post(f'/admin/batches/{batch_id}/review', data={
        'verification_stage': 'Quality Verified',
        'quality_score': '95',
        'quality_grade': 'Grade A',
        'verifier_name': 'Senior Ag Quality Auditor',
        'review_reason': 'Official pesticide tests passed with zero prohibited residues.',
        'internal_notes': 'Final approval granted.'
    }, follow_redirects=True)
    assert res_approved.status_code == 200

    with app.app_context():
        b = HarvestBatch.query.get(batch_id)
        assert b.verification_stage == 'Quality Verified'
        assert b.is_independently_verified is True
        assert b.quality_score == 95
        assert b.quality_grade == 'Grade A'
        assert b.verifier_name == 'Senior Ag Quality Auditor'
        assert b.reviewed_by_id == admin_id
        assert b.reviewed_at is not None

        # Verify audit history has all 3 stage transition logs with timestamps
        history = b.verification_history
        assert len(history) == 3
        stages = [h.new_stage for h in reversed(history)]
        assert stages == ['Under Review', 'Action Required', 'Quality Verified']

def test_farmer_submits_corrections(client, app):
    """Test farmer can view My Product Verification and submit corrections for Action Required"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        batch = HarvestBatch(
            batch_code=generate_uhvc_code(),
            user_id=farmer.id,
            crop_name="Correctable Spinach",
            category="Vegetables",
            harvest_date=date(2026, 10, 10),
            quantity=150.0,
            unit="kg",
            verification_stage="Action Required",
            admin_feedback="Please clarify harvest packaging protocol."
        )
        db.session.add(batch)
        db.session.commit()
        batch_id = batch.id

    # 1. Login as farmer and check My Product Verification page
    client.get('/logout')
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'}, follow_redirects=True)
    
    page = client.get('/farmer/verifications')
    assert page.status_code == 200
    assert b"My Product Verification" in page.data
    assert b"Correctable Spinach" in page.data
    assert b"Please clarify harvest packaging protocol." in page.data

    # 2. Submit corrections
    corr_res = client.post(f'/farmer/batches/{batch_id}/submit-corrections', data={
        'corrections_note': 'Packaging uses food-grade sanitized perforated crates as requested.'
    }, follow_redirects=True)
    assert corr_res.status_code == 200

    with app.app_context():
        b = HarvestBatch.query.get(batch_id)
        assert b.verification_stage == 'Submitted'
        assert b.is_independently_verified is False
        last_log = b.verification_history[0]
        assert last_log.action_type == 'CORRECTION_SUBMITTED'
        assert 'food-grade sanitized' in last_log.comments

def test_farmer_spec_edit_triggers_re_review(client, app):
    """Test that editing verified batch specifications resets stage to Submitted for re-review"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        admin = User.query.filter_by(role='ADMIN').first()
        
        batch = HarvestBatch(
            batch_code=generate_uhvc_code(),
            user_id=farmer.id,
            crop_name="Verified Organic Carrots",
            category="Vegetables",
            harvest_date=date(2026, 10, 10),
            quantity=500.0,
            unit="kg",
            asking_price=25.0,
            location="Nashik Farm #1",
            verification_stage="Quality Verified",
            verification_status="Verified",
            is_independently_verified=True,
            reviewed_by_id=admin.id
        )
        db.session.add(batch)
        db.session.commit()
        batch_id = batch.id

    client.get('/logout')
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'}, follow_redirects=True)

    # Farmer edits specifications
    edit_res = client.post(f'/farmer/batches/{batch_id}/edit', data={
        'crop_name': 'Verified Organic Carrots (Modified Lot)',
        'category': 'Vegetables',
        'quantity': '800.0',
        'unit': 'kg',
        'harvest_date': '2026-10-12',
        'location': 'Nashik Farm #2 (New Location)',
        'asking_price': '28.0',
        'quality_grade': 'Grade A',
        'description': 'Updated quantity and harvest plot'
    }, follow_redirects=True)
    assert edit_res.status_code == 200

    with app.app_context():
        b = HarvestBatch.query.get(batch_id)
        # Previous approval MUST be invalidated
        assert b.verification_stage == 'Submitted'
        assert b.is_independently_verified is False
        assert b.quantity == 800.0
        # Re-review log entry recorded
        assert any(h.action_type in ['RE_REVIEW_REQUIRED', 'DETAILS_EDITED'] for h in b.verification_history)

def test_purchasing_blocked_for_unverified_products(client, app):
    """Test that purchasing an unverified product is strictly prevented by the server"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        buyer = User.query.filter_by(role='BUYER').first()

        batch = HarvestBatch(
            batch_code=generate_uhvc_code(),
            user_id=farmer.id,
            crop_name="Unverified Cauliflower",
            harvest_date=date(2026, 10, 10),
            quantity=300.0,
            unit="kg",
            verification_stage="Submitted"
        )
        db.session.add(batch)
        db.session.flush()

        prod = Product(
            user_id=farmer.id,
            batch_id=batch.id,
            title="Unverified Cauliflower Lot",
            category="Vegetables",
            quantity=300.0,
            initial_quantity=300.0,
            unit="kg",
            price_per_unit=20.0,
            location="Nashik",
            harvest_date=date(2026, 10, 10),
            availability_status="Available"
        )
        db.session.add(prod)
        db.session.commit()
        prod_id = prod.id

    client.get('/logout')
    client.post('/login', data={'login_input': 'buyer1', 'password': 'Buyer@123'}, follow_redirects=True)

    # 1. Product detail page should show checkout locked notice
    p_page = client.get(f'/products/{prod_id}')
    assert p_page.status_code == 200
    assert b"Pending Quality Review" in p_page.data
    assert b"Purchasing Disabled" in p_page.data

    # 2. Attempting to place an order via POST must be blocked on the server
    order_data = {
        'product_id': str(prod_id),
        'quantity': '10',
        'delivery_address': 'Bandra Terminal, Mumbai',
        'contact_phone': '9876543210'
    }
    post_res = client.post('/orders/create', data=order_data, follow_redirects=True)
    assert b"requires official admin Quality Verification" in post_res.data or b"Cannot place order" in post_res.data

def test_public_traceability_and_qr_code(client, app):
    """Test public traceability page displays approved info without exposing private docs or internal notes, and QR works"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        admin = User.query.filter_by(role='ADMIN').first()
        code = generate_uhvc_code()

        batch = HarvestBatch(
            batch_code=code,
            user_id=farmer.id,
            crop_name="Export Pomegranates",
            category="Fruits",
            harvest_date=date(2026, 10, 10),
            quantity=1000.0,
            unit="kg",
            location="Dindori, Nashik",
            verification_stage="Quality Verified",
            verification_status="Verified",
            is_independently_verified=True,
            quality_score=97,
            quality_grade="Grade A",
            verifier_name="Nashik Export Quality Inspector",
            document_url="/uploads/documents/confidential_lab_assay.pdf",
            document_name="confidential_lab_assay.pdf",
            internal_notes="Confidential risk analysis score 9.9 - internal only.",
            notes="Zero synthetic pesticide residue detected in gas chromatography."
        )
        db.session.add(batch)
        db.session.commit()

    # Public user / buyer visits traceability page
    client.get('/logout')
    res = client.get(f'/batch/{code}')
    assert res.status_code == 200
    assert code.encode() in res.data
    assert b"Export Pomegranates" in res.data
    assert b"Quality Verified" in res.data
    assert b"97/100" in res.data
    assert b"Nashik Export Quality Inspector" in res.data
    
    # PRIVACY CHECKS: Confidential documents and internal admin notes must NOT be in public view
    assert b"confidential_lab_assay.pdf" not in res.data
    assert b"Confidential risk analysis score" not in res.data
    assert b"internal only" not in res.data

    # QR Code endpoint check
    qr_res = client.get(f'/batch/{code}/qr')
    assert qr_res.status_code == 200
    assert qr_res.mimetype == 'image/png'

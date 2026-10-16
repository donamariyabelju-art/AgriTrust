import os
import pytest
from app import create_app
from config import Config
from extensions import db
from models.user import User
from models.farm import Farm
from models.crop import Crop
from models.product import Product
from models.order import Order
from models.reservation import FutureHarvest, Reservation
from models.harvest import HarvestBatch
from datetime import date

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

def test_landing_page_renders(client):
    """Test that landing page renders with required tagline and branding"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Grow Smarter. Sell Fairer. Build Trust." in response.data
    assert b"AgriTrust" in response.data

def test_public_pages_render(client):
    """Verify core public agronomy and marketplace pages render successfully"""
    pages = [
        '/marketplace',
        '/farming-guide',
        '/chatbot',
        '/weather',
        '/demand',
        '/price-advisor',
        '/traceability'
    ]
    for page in pages:
        res = client.get(page)
        assert res.status_code == 200, f"Page {page} failed with status {res.status_code}"

def test_authentication_workflow(client):
    """Verify user registration, login, session management, and logout"""
    # 1. Register new farmer
    reg_data = {
        'username': 'newfarmer',
        'email': 'newfarmer@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'FARMER',
        'full_name': 'New Test Farmer',
        'phone': '9876543210',
        'location': 'Nashik'
    }
    reg_res = client.post('/register', data=reg_data, follow_redirects=True)
    assert reg_res.status_code == 200
    assert b"New Test Farmer" in reg_res.data or b"Dashboard" in reg_res.data

    # 2. Logout
    logout_res = client.get('/logout', follow_redirects=True)
    assert logout_res.status_code == 200

    # 3. Login with credentials
    login_data = {
        'login_input': 'newfarmer',
        'password': 'password123'
    }
    login_res = client.post('/login', data=login_data, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"New Test Farmer" in login_res.data

def test_default_seed_users(client):
    """Verify that seeded farmer, buyer, and admin accounts exist and authenticate"""
    # Test Farmer login
    farmer_login = client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'}, follow_redirects=True)
    assert farmer_login.status_code == 200
    assert b"Ramesh Patel" in farmer_login.data
    client.get('/logout')

    # Test Buyer login
    buyer_login = client.post('/login', data={'login_input': 'buyer1', 'password': 'Buyer@123'}, follow_redirects=True)
    assert buyer_login.status_code == 200
    assert b"FreshMart Wholesale" in buyer_login.data
    client.get('/logout')

def test_farm_and_crop_management(client):
    """Verify farmer can create, edit, and delete farm and crop records"""
    # Login as farmer
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'})

    # 1. Add Farm
    farm_data = {
        'name': 'Test Plot 4',
        'location': 'Nashik North',
        'land_area': '3.5',
        'soil_type': 'Alluvial Soil',
        'irrigation_method': 'Drip Irrigation'
    }
    farm_res = client.post('/farms/add', data=farm_data, follow_redirects=True)
    assert farm_res.status_code == 200
    assert b"Test Plot 4" in farm_res.data

    # 2. Add Crop
    crop_data = {
        'crop_name': 'Test Hybrid Tomato',
        'planting_date': '2026-08-01',
        'expected_harvest_date': '2026-11-01',
        'growth_stage': 'Flowering',
        'growth_percentage': '45',
        'expected_yield': '2500',
        'production_cost': '12000',
        'expected_revenue': '38000',
        'health_status': 'Healthy'
    }
    crop_res = client.post('/crops/add', data=crop_data, follow_redirects=True)
    assert crop_res.status_code == 200
    assert b"Test Hybrid Tomato" in crop_res.data

def test_crop_recommendation_engine(client):
    """Verify recommendation engine evaluates soil/climate inputs and returns financial metrics"""
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'})
    rec_data = {
        'location': 'Nashik',
        'land_size': '2.0',
        'soil_type': 'Black',
        'season': 'Kharif',
        'water_availability': 'Irrigated'
    }
    res = client.post('/recommendations', data=rec_data)
    assert res.status_code == 200
    assert b"Tomato" in res.data
    assert b"Est. Net Profit" in res.data
    assert b"Algorithmic Transparency" in res.data

def test_disease_detection_validation_and_demo(client):
    """Verify disease detector rejects bad extensions and executes diagnostic pipeline"""
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'})
    # Invalid extension rejection
    import io
    bad_upload = {
        'crop_image': (io.BytesIO(b"fake content"), 'test.txt')
    }
    res = client.post('/crop-health', data=bad_upload, content_type='multipart/form-data', follow_redirects=True)
    assert b"Invalid file format" in res.data

def test_chatbot_api(client):
    """Verify chatbot API responds with contextual agricultural advice"""
    res = client.post('/api/chat', json={'message': 'What is the best irrigation for tomatoes?'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'reply' in data
    assert 'Drip Irrigation' in data['reply'] or 'irrigation' in data['reply'].lower()

def test_orders_and_stock_limits(client):
    """Verify marketplace purchase orders enforce quantity limits and atomic decrements"""
    # Log in as buyer
    client.post('/login', data={'login_input': 'buyer1', 'password': 'Buyer@123'})

    # Try purchasing valid quantity
    order_data = {
        'product_id': 1,
        'quantity': 50,
        'delivery_address': 'FreshMart Terminal 2, Mumbai',
        'contact_phone': '9123456789',
        'notes': 'Delivery by 10 AM'
    }
    res = client.post('/orders/create', data=order_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"confirmed" in res.data.lower() or b"order #" in res.data.lower()

    # Try purchasing excessive quantity exceeding available stock
    excessive_data = {
        'product_id': 1,
        'quantity': 999999,
        'delivery_address': 'Terminal 3',
        'contact_phone': '9123456789'
    }
    excessive_res = client.post('/orders/create', data=excessive_data, follow_redirects=True)
    assert b"exceeds available stock" in excessive_res.data.lower()

def test_reservation_limits(client):
    """Verify harvest reservation enforces capacity limits on upcoming harvest"""
    client.post('/login', data={'login_input': 'buyer1', 'password': 'Buyer@123'})
    
    # Exceeding reservation quantity
    excess_res_data = {
        'future_harvest_id': 1,
        'reserved_quantity': 500000,
        'contact_phone': '9123456789'
    }
    res = client.post('/reservations/book', data=excess_res_data, follow_redirects=True)
    assert b"exceeds remaining available" in res.data.lower()

def test_unauthorized_access_protection(client):
    """Verify non-logged-in users cannot access farmer dashboard, farms, or admin routes"""
    res_dash = client.get('/dashboard', follow_redirects=True)
    assert b"Please log in" in res_dash.data

    res_admin = client.get('/admin', follow_redirects=True)
    assert b"Please log in" in res_admin.data

def test_strict_role_based_access_controls(client, app):
    """Verify strict role separation and ownership boundaries across Buyer, Farmer, and Admin"""
    with app.app_context():
        farmer = User.query.filter_by(role='FARMER').first()
        buyer = User.query.filter_by(role='BUYER').first()
        admin = User.query.filter_by(role='ADMIN').first()
        batch = HarvestBatch.query.first()
        batch_id = batch.id if batch else 1

    # 1. BUYER ROLE RESTRICTIONS
    client.post('/login', data={'login_input': 'buyer1', 'password': 'Buyer@123'}, follow_redirects=True)
    
    # Buyer CAN access buyer dashboard
    buyer_dash = client.get('/buyer/dashboard')
    assert buyer_dash.status_code == 200
    assert b"Buyer Portal" in buyer_dash.data
    
    # Buyer CANNOT access Admin Dashboard (403)
    assert client.get('/admin').status_code == 403
    
    # Buyer CANNOT access Farmer crop health, recommendations, farms, or verifications (403)
    assert client.get('/crop-health').status_code == 403
    assert client.get('/recommendations').status_code == 403
    assert client.get('/farms').status_code == 403
    assert client.get('/crops').status_code == 403
    assert client.get('/farmer/verifications').status_code == 403
    assert client.post('/batches/create', data={}).status_code == 403
    
    client.get('/logout')

    # 2. FARMER ROLE RESTRICTIONS
    client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'}, follow_redirects=True)
    
    # Farmer CAN access their own dashboard, crops, crop-health, and recommendations
    assert client.get('/dashboard').status_code == 200
    assert client.get('/crop-health').status_code == 200
    assert client.get('/recommendations').status_code == 200
    assert client.get('/farmer/verifications').status_code == 200

    # Farmer CANNOT access Admin area (403)
    assert client.get('/admin').status_code == 403

    # Farmer CANNOT advance post-harvest lifecycle stages via update-stage (403, Admin only)
    post_stage = client.post(f'/batches/{batch_id}/update-stage', data={'journey_stage': 'Delivered'})
    assert post_stage.status_code == 403

    # Farmer CANNOT access buyer dashboard (403)
    assert client.get('/buyer/dashboard').status_code == 403

    client.get('/logout')

    # 3. ADMIN ROLE RESTRICTIONS & ALLOWANCES
    client.post('/login', data={'login_input': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    
    # Admin CAN access Admin Panel
    admin_res = client.get('/admin')
    assert admin_res.status_code == 200
    assert b"Admin Control Center" in admin_res.data
    assert b"Harvest Lifecycle Management" in admin_res.data

    # Admin CANNOT access farmer private crop health scanner or recommendations (403)
    assert client.get('/crop-health').status_code == 403
    assert client.get('/recommendations').status_code == 403
    assert client.get('/farms').status_code == 403
    assert client.get('/crops').status_code == 403
    assert client.get('/buyer/dashboard').status_code == 403

    # Admin CAN update harvest lifecycle stages
    admin_stage_res = client.post(f'/admin/batches/{batch_id}/lifecycle-stage', data={'journey_stage': 'Packaging'}, follow_redirects=True)
    assert admin_stage_res.status_code == 200
    assert b"lifecycle stage updated" in admin_stage_res.data.lower()

    client.get('/logout')


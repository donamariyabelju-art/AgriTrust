import pytest
from app import create_app
from config import Config
from extensions import db
from models.user import User
from models.demand import BuyerDemand
from models.reservation import FutureHarvest
from models.harvest import HarvestBatch
from services.chatbot_service import get_chatbot_response
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

def test_traceability_lookup_box_removed(client):
    """1.A: Verify Path Verification Lookup box is removed while batch features remain intact"""
    res = client.get('/traceability')
    assert res.status_code == 200
    assert b"Public Batch Verification Lookup" not in res.data
    assert b"Path Verification Lookup" not in res.data
    # Batch registration and core traceability remain
    assert b"Harvest Verification &amp; Traceability" in res.data or b"Harvest Verification & Traceability" in res.data
    assert b"Register Harvest Batch" in res.data

def test_farming_guide_ready_action_box_removed(client):
    """1.B: Verify 'Ready to Put This Action' box is removed from Smart Farming Guide"""
    res = client.get('/farming-guide')
    assert res.status_code == 200
    assert b"Ready to Put This Guide into Action" not in res.data
    assert b"Ready to Put This Action" not in res.data
    assert b"Smart Farming Guide" in res.data
    assert b"Cultivation Handbook" in res.data

def test_ai_assistant_typed_questions(app):
    """1.C: Verify AI Assistant responds appropriately to typed user queries across core crops and topics"""
    with app.app_context():
        # Query 1: Tomato blight
        res1 = get_chatbot_response("My tomatoes have brown spots and leaf blight, how to cure?")
        ans1 = res1['reply']
        assert "blight" in ans1.lower() or "fungicide" in ans1.lower() or "copper" in ans1.lower()
        assert "Could you try rephrasing" not in ans1
        assert res1['topic'] == 'Disease Symptoms & Control'

        # Query 2: Basmati rice fertilization
        res2 = get_chatbot_response("What fertilizer should I apply for Basmati rice crop?")
        ans2 = res2['reply']
        assert "rice" in ans2.lower() or "nitrogen" in ans2.lower() or "fertilizer" in ans2.lower() or "npk" in ans2.lower()
        assert "Could you try rephrasing" not in ans2

        # Query 3: Cucumber powdery mildew / greenhouse management
        res3 = get_chatbot_response("How to grow English cucumbers and prevent powdery mildew?")
        ans3 = res3['reply']
        assert "cucumber" in ans3.lower() or "mildew" in ans3.lower() or "trellis" in ans3.lower()
        assert "Could you try rephrasing" not in ans3

        # Query 4: Banana crop care
        res4 = get_chatbot_response("Tell me about banana farming and bunch care")
        ans4 = res4['reply']
        assert "banana" in ans4.lower() or "potassium" in ans4.lower() or "bunch" in ans4.lower()
        assert "Could you try rephrasing" not in ans4

        # Query 5: Weather advisory
        res5 = get_chatbot_response("Will heavy rainfall damage my harvest this week?")
        ans5 = res5['reply']
        assert "weather" in ans5.lower() or "rain" in ans5.lower() or "drainage" in ans5.lower()
        assert "Could you try rephrasing" not in ans5

def test_demand_fulfillment_conditional_form(client):
    """1.D: Verify conditional demand form: with HVC shows only Batch ID and Quantity, without HVC shows standard form"""
    # Login as farmer
    login_res = client.post('/login', data={'login_input': 'farmer1', 'password': 'Farmer@123'}, follow_redirects=True)
    assert login_res.status_code == 200

    # Create demand WITH hvc_code
    dem_with_hvc = BuyerDemand(
        buyer_id=2,
        crop_name='Export Grade Tomatoes',
        required_quantity=1000.0,
        unit='kg',
        location='Mumbai Terminal',
        demand_level='High',
        required_date=date(2026, 12, 1),
        hvc_code='UHVC-2026-TM981'
    )
    # Create demand WITHOUT hvc_code
    dem_no_hvc = BuyerDemand(
        buyer_id=2,
        crop_name='Commercial Cucumbers',
        required_quantity=500.0,
        unit='kg',
        location='Pune APMC',
        demand_level='Moderate',
        required_date=date(2026, 12, 1),
        hvc_code=None
    )
    db.session.add_all([dem_with_hvc, dem_no_hvc])
    db.session.commit()

    # GET product_create with demand_id of dem_with_hvc
    res1 = client.get(f'/products/create?demand_id={dem_with_hvc.id}')
    assert res1.status_code == 200
    # Shows Batch ID and Quantity
    assert b"Batch ID *" in res1.data
    assert b"Quantity (kg) *" in res1.data
    assert b"Fulfill Demand" in res1.data
    # Does NOT show standard standalone produce listing fields
    assert b"Product Title *" not in res1.data
    assert b"Category *" not in res1.data
    assert b"Produce Photo" not in res1.data

    # POST fulfillment with HVC
    res_post = client.post('/products/create', data={
        'demand_id': str(dem_with_hvc.id),
        'batch_id': 'UHVC-2026-TM981',
        'quantity': '1000.0'
    }, follow_redirects=True)
    assert res_post.status_code == 200
    # Verify demand is fulfilled
    db.session.refresh(dem_with_hvc)
    assert dem_with_hvc.available_supply >= 1000.0
    assert dem_with_hvc.status == 'Fulfilled'

    # GET product_create with demand_id of dem_no_hvc (without HVC code)
    res2 = client.get(f'/products/create?demand_id={dem_no_hvc.id}')
    assert res2.status_code == 200
    # Shows standard form
    assert b"Product Title *" in res2.data
    assert b"Category *" in res2.data

def test_buyer_page_traceability_removed(client):
    """2.B: Verify Traceability is removed from Buyer view and buyer dashboard"""
    # Login as buyer
    login_res = client.post('/login', data={'login_input': 'buyer1', 'password': 'Buyer@123'}, follow_redirects=True)
    assert login_res.status_code == 200
    res = client.get('/buyer/dashboard')
    assert res.status_code == 200
    # Traceability column removed from orders table
    assert b"<th>Traceability UHVC</th>" not in res.data
    # Traceability link removed from Buyer navigation
    assert b'<li class="nav-item"><a href="/traceability">Traceability</a></li>' not in res.data

def test_upcoming_section_multiple_crops(client):
    """2.C: Verify Upcoming Section on Buyer Dashboard and reservations supports multiple crops beyond bell peppers"""
    login_res = client.post('/login', data={'login_input': 'buyer1', 'password': 'Buyer@123'}, follow_redirects=True)
    assert login_res.status_code == 200
    res_dash = client.get('/buyer/dashboard')
    assert res_dash.status_code == 200
    assert b"Upcoming Harvests Open for Advance Procurement" in res_dash.data

    # Check reservations page
    res_res = client.get('/reservations')
    assert res_res.status_code == 200
    # Multiple crops present
    assert b"Red Bell Peppers (Capsicum)" in res_res.data
    assert b"Tomatoes" in res_res.data or b"Vine Tomatoes" in res_res.data
    assert b"Cucumbers" in res_res.data
    assert b"Basmati" in res_res.data
    assert b"Bananas" in res_res.data

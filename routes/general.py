from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models.demand import BuyerDemand
from models.product import Product
from routes.auth import login_required, role_required

general_bp = Blueprint('general', __name__)

# Complete 11-step Beginner Farming Guides
FARMING_GUIDES = {
    'Tomato': {
        'botanical_name': 'Solanum lycopersicum',
        'season': 'Kharif, Rabi, and Summer',
        'optimal_temp': '21°C - 28°C',
        'soil': 'Well-drained sandy loam or clay loam with pH 6.0 - 7.0',
        'steps': [
            {'num': 1, 'title': 'Soil Preparation', 'desc': 'Plow field to 25 cm depth. Incorporate 8-10 tons/acre well-rotted FYM. Construct raised beds 15 cm high and 1m wide.'},
            {'num': 2, 'title': 'Seed Selection', 'desc': 'Select disease-resistant F1 hybrids (e.g., Roma, Arka Rakshak). Treat seeds with Trichoderma viride (4g/kg) to prevent damping off.'},
            {'num': 3, 'title': 'Planting & Spacing', 'desc': 'Transplant 25-30 day old sturdy seedlings with 60 cm row-to-row and 45 cm plant-to-plant spacing in late afternoon.'},
            {'num': 4, 'title': 'Irrigation', 'desc': 'Set up inline drip emitters. Irrigate immediately after transplanting, followed by daily or alternate-day drip cycles during flowering.'},
            {'num': 5, 'title': 'Fertilizer Management', 'desc': 'Apply basal NPK 50:50:50 kg/acre. Fertigate with 19:19:19 water-soluble grade during vegetative stage and 13:0:45 during fruiting.'},
            {'num': 6, 'title': 'Pest Management', 'desc': 'Erect yellow sticky traps for whiteflies. Spray neem oil (3 ml/L) bi-weekly. Apply pheromone traps for Helicoverpa fruit borers.'},
            {'num': 7, 'title': 'Disease Prevention', 'desc': 'Prune lower leaves touching soil. Spray copper oxychloride (2.5 g/L) if early blight target spots appear on lower foliage.'},
            {'num': 8, 'title': 'Crop Monitoring & Staking', 'desc': 'Stake plants with bamboo poles or trellis twine by day 30 to keep fruit clusters off damp soil and enhance sunlight exposure.'},
            {'num': 9, 'title': 'Harvesting', 'desc': 'Harvest at "breaker stage" (slight pink at blossom end) for distance transport, or full red ripe for direct local delivery.'},
            {'num': 10, 'title': 'Post-Harvest Management', 'desc': 'Sort by uniform size and color in plastic crates. Pre-cool in shaded packing shed at 12-15°C; do not store in airtight bags.'},
            {'num': 11, 'title': 'Selling Produce', 'desc': 'List batch directly on AgriTrust Direct Marketplace to connect with institutional buyers and bypass middlemen commissions.'}
        ]
    },
    'Rice': {
        'botanical_name': 'Oryza sativa',
        'season': 'Kharif (Monsoon)',
        'optimal_temp': '24°C - 35°C',
        'soil': 'Clayey or alluvial soil with water retention ability',
        'steps': [
            {'num': 1, 'title': 'Soil Preparation', 'desc': 'Dry plowing followed by 2-3 passes of wet puddling to form an impervious subterranean hardpan to retain ponded water.'},
            {'num': 2, 'title': 'Seed Selection', 'desc': 'Select certified seed (e.g., Pusa 1121, MTU 1010). Soak in salt water solution (10%) to discard hollow floating seeds.'},
            {'num': 3, 'title': 'Planting & Transplanting', 'desc': 'Transplant 20-25 day seedlings at 20 cm x 15 cm spacing, placing 2-3 seedlings per hill at shallow 2 cm depth.'},
            {'num': 4, 'title': 'Irrigation', 'desc': 'Maintain 2-3 cm standing water for the first 3 weeks, then alternate wetting and drying (AWD) until flowering, keeping ponded during grain fill.'},
            {'num': 5, 'title': 'Fertilizer Management', 'desc': 'Apply basal DAP and MOP. Top dress urea in 3 equal splits: 15 days after transplanting, tillering stage, and panicle initiation.'},
            {'num': 6, 'title': 'Pest Management', 'desc': 'Monitor for yellow stem borer and brown planthopper. Avoid excess early nitrogen which attracts sucking pests.'},
            {'num': 7, 'title': 'Disease Prevention', 'desc': 'Check for rice blast (diamond lesions) and bacterial leaf streak. Apply validamycin or pseudomonas fluorescens as preventive bio-agent.'},
            {'num': 8, 'title': 'Crop Monitoring', 'desc': 'Scout for uniform tillering and panicle emergence. Pull weeds manually or using conoweeder at 20 and 40 days.'},
            {'num': 9, 'title': 'Harvesting', 'desc': 'Harvest when 85-90% of panicle grains turn golden yellow. Drain field water 10 days before harvesting.'},
            {'num': 10, 'title': 'Post-Harvest Management', 'desc': 'Thresh and dry paddy on clean tarpaulins until grain moisture drops below 13-14% to prevent Aspergillus molding.'},
            {'num': 11, 'title': 'Selling Produce', 'desc': 'List grain lots on AgriTrust with audited batch verification to secure wholesale procurement contracts.'}
        ]
    },
    'Banana': {
        'botanical_name': 'Musa acuminata',
        'season': 'Year-round planting in humid subtropics/tropics',
        'optimal_temp': '26°C - 32°C',
        'soil': 'Deep, rich loamy soil with high organic carbon and pH 6.5 - 7.5',
        'steps': [
            {'num': 1, 'title': 'Soil Preparation', 'desc': 'Dig pits of 60cm x 60cm x 60cm. Fill with 10 kg FYM, 250g neem cake, and topsoil 2 weeks prior to planting.'},
            {'num': 2, 'title': 'Seed / Sucker Selection', 'desc': 'Use virus-indexed tissue-cultured plantlets (Grand Naine) or sword suckers weighing 1.5 to 2.0 kg with well-formed corms.'},
            {'num': 3, 'title': 'Planting & Spacing', 'desc': 'Plant at 1.8m x 1.8m spacing. Compact soil firmly around the root ball and form a slight mound to prevent water stagnation.'},
            {'num': 4, 'title': 'Irrigation', 'desc': 'Banana is water-intensive. Install drip rings providing 15-20 liters per plant per day, increasing to 25L during shooting.'},
            {'num': 5, 'title': 'Fertilizer Management', 'desc': 'Apply 200g N, 60g P, and 300g K per plant divided across monthly drip fertigation doses up to bunch flowering.'},
            {'num': 6, 'title': 'Pest Management', 'desc': 'Inspect pseudostem for banana weevil boreholes. Drench corm with neem extract or entomopathogenic nematodes.'},
            {'num': 7, 'title': 'Disease Prevention', 'desc': 'Prevent Panama wilt and Sigatoka leaf spot. Prune dried lower leaves. Disinfect machetes in bleach solution.'},
            {'num': 8, 'title': 'Crop Monitoring & Propping', 'desc': 'Remove unwanted side suckers (desuckering), leaving only 1 follower. Prop heavy bunches with double bamboo poles.'},
            {'num': 9, 'title': 'Harvesting', 'desc': 'Harvest when bunch fingers lose angular edges and turn rounded, approximately 95-105 days after bunch shooting.'},
            {'num': 10, 'title': 'Post-Harvest Management', 'desc': 'De-hand bunches carefully, wash latex in alum water tank, and pack in ventilated corrugated boxes.'},
            {'num': 11, 'title': 'Selling Produce', 'desc': 'Publish upcoming banana harvest on AgriTrust Harvest Reservation for direct contract buying.'}
        ]
    },
    'Cucumber': {
        'botanical_name': 'Cucumis sativus',
        'season': 'Zaid (Summer) and Kharif',
        'optimal_temp': '22°C - 30°C',
        'soil': 'Sandy loam to alluvial soil with excellent drainage',
        'steps': [
            {'num': 1, 'title': 'Soil Preparation', 'desc': 'Prepare raised beds 90 cm wide. Mix 5 tons/acre decomposed compost with 50 kg single superphosphate.'},
            {'num': 2, 'title': 'Seed Selection', 'desc': 'Select parthenocarpic gynoecious hybrids for greenhouse or vigorous open-field slicing varieties (e.g., Poinsett).'},
            {'num': 3, 'title': 'Planting & Sowing', 'desc': 'Direct seed 2 cm deep with 45 cm distance between plants on silver-black mulch sheets with drip tape underneath.'},
            {'num': 4, 'title': 'Irrigation', 'desc': 'Keep soil consistently moist. Inconsistent watering causes fruit bitterness and hollow heart defects.'},
            {'num': 5, 'title': 'Fertilizer Management', 'desc': 'Supply balanced 100:50:50 NPK split weekly through drip fertigation until final harvest picking.'},
            {'num': 6, 'title': 'Pest Management', 'desc': 'Guard against red pumpkin beetle and fruit flies. Hang methyl eugenol pheromone lure traps across borders.'},
            {'num': 7, 'title': 'Disease Prevention', 'desc': 'Spray sulfur dust or potassium bicarbonate at first sign of white powdery mildew powder on upper leaf surfaces.'},
            {'num': 8, 'title': 'Crop Trellising', 'desc': 'Train vines upward on nylon netting trellises to increase yield by 35% and keep fruits straight and unblemished.'},
            {'num': 9, 'title': 'Harvesting', 'desc': 'Harvest every 2 days early morning when cucumbers reach tender 15-20 cm length before seeds harden.'},
            {'num': 10, 'title': 'Post-Harvest Management', 'desc': 'Wipe fruits gently, sort by uniform girth, and store in cool shaded rooms at 10-12°C with high humidity.'},
            {'num': 11, 'title': 'Selling Produce', 'desc': 'List fresh harvests on AgriTrust Direct Marketplace for daily procurement by restaurants and vegetable markets.'}
        ]
    }
}

@general_bp.route('/farming-guide')
def farming_guide_view():
    selected_crop = request.args.get('crop', 'Tomato')
    if selected_crop not in FARMING_GUIDES:
        selected_crop = 'Tomato'
    guide = FARMING_GUIDES[selected_crop]
    crops_available = list(FARMING_GUIDES.keys())
    return render_template(
        'farming_guide.html',
        selected_crop=selected_crop,
        guide=guide,
        crops_available=crops_available
    )

@general_bp.route('/demand', methods=['GET', 'POST'])
def demand_view():
    crop_filter = request.args.get('crop', 'All')
    level_filter = request.args.get('level', 'All')
    location_filter = request.args.get('location', '').strip()

    q = BuyerDemand.query.filter_by(status='Active')
    if crop_filter and crop_filter != 'All':
        q = q.filter(BuyerDemand.crop_name.ilike(f"%{crop_filter}%"))
    if level_filter and level_filter != 'All':
        q = q.filter(BuyerDemand.demand_level == level_filter)
    if location_filter:
        q = q.filter(BuyerDemand.location.ilike(f"%{location_filter}%"))

    demands = q.order_by(BuyerDemand.created_at.desc()).all()

    return render_template(
        'demand.html',
        demands=demands,
        current_crop=crop_filter,
        current_level=level_filter,
        current_location=location_filter
    )

@general_bp.route('/demand/create', methods=['POST'])
@login_required
@role_required('BUYER', 'ADMIN')
def create_demand():
    buyer_id = session['user_id']
    crop_name = request.form.get('crop_name', '').strip()
    required_qty = request.form.get('required_quantity')
    unit = request.form.get('unit', 'kg')
    location = request.form.get('location', '').strip()
    demand_level = request.form.get('demand_level', 'High')
    target_price = request.form.get('target_price')
    req_date_str = request.form.get('required_date')
    desc = request.form.get('description', '').strip()
    hvc_code = request.form.get('hvc_code', '').strip().upper() or None

    if not crop_name or not required_qty or not location or not req_date_str:
        flash('Please fill in all required procurement fields.', 'danger')
        return redirect(url_for('general.demand_view'))

    try:
        qty = float(required_qty)
        r_date = datetime.strptime(req_date_str, '%Y-%m-%d').date()
        price = float(target_price) if target_price else None
    except (ValueError, TypeError):
        flash('Invalid numeric or date format.', 'danger')
        return redirect(url_for('general.demand_view'))

    new_demand = BuyerDemand(
        buyer_id=buyer_id,
        crop_name=crop_name,
        required_quantity=qty,
        available_supply=0.0,
        unit=unit,
        location=location,
        demand_level=demand_level,
        target_price=price,
        required_date=r_date,
        description=desc,
        hvc_code=hvc_code,
        status='Active',
        is_sample_data=False
    )
    db.session.add(new_demand)
    db.session.commit()

    flash(f"Buyer procurement demand for '{new_demand.crop_name}' published to Community Demand Board!", 'success')
    return redirect(url_for('general.demand_view'))

@general_bp.route('/price-advisor')
def price_advisor_view():
    # Benchmark reference market prices (clearly labeled as indicative reference standards)
    reference_data = [
        {'crop': 'Tomato (Roma)', 'category': 'Vegetables', 'min_price': 18.0, 'max_price': 25.0, 'avg_price': 22.0, 'trend': '+8%', 'demand': 'High'},
        {'crop': 'Cucumber (English)', 'category': 'Vegetables', 'min_price': 15.0, 'max_price': 22.0, 'avg_price': 18.5, 'trend': '+3%', 'demand': 'Moderate'},
        {'crop': 'Basmati Rice (Pusa)', 'category': 'Grains', 'min_price': 34.0, 'max_price': 42.0, 'avg_price': 38.0, 'trend': '+12%', 'demand': 'High'},
        {'crop': 'Banana (Grand Naine)', 'category': 'Fruits', 'min_price': 14.0, 'max_price': 20.0, 'avg_price': 17.0, 'trend': '-2%', 'demand': 'Steady'},
        {'crop': 'Soybean (Grade 1)', 'category': 'Pulses/Oilseeds', 'min_price': 42.0, 'max_price': 49.0, 'avg_price': 46.0, 'trend': '+5%', 'demand': 'High'},
        {'crop': 'Wheat (Sharbati)', 'category': 'Grains', 'min_price': 24.0, 'max_price': 28.0, 'avg_price': 26.0, 'trend': '0%', 'demand': 'Moderate'}
    ]

    return render_template('price_advisor.html', reference_data=reference_data)

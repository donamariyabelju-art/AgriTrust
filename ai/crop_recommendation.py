"""
Crop Recommendation Engine for AgriTrust
Evaluates soil characteristics, climatic season, water availability, and land size
to recommend optimal crops with economic yield and profit projections.
"""
import math

CROP_KNOWLEDGE_BASE = {
    'Tomato': {
        'suitable_soils': ['Loamy', 'Black', 'Red', 'Alluvial'],
        'seasons': ['Kharif', 'Rabi', 'Zaid', 'Summer', 'Winter'],
        'water_requirements': ['Moderate', 'Irrigated', 'High'],
        'duration_days': '90 - 110 days',
        'avg_yield_per_acre_kg': 12000,
        'avg_price_per_kg': 22.0,
        'cost_per_acre': 35000,
        'suitability_score_base': 88,
        'rationale': 'High market liquidity and steady consumer demand. Thrives exceptionally well in well-drained loamy to black soils with drip irrigation.',
        'guidance': 'Employ raised beds and drip lines to curtail fungal leaf rot. Prune indeterminate side shoots for uniform fruit grading.'
    },
    'Rice (Basmati)': {
        'suitable_soils': ['Clay', 'Alluvial', 'Black'],
        'seasons': ['Kharif', 'Monsoon'],
        'water_requirements': ['High', 'Irrigated'],
        'duration_days': '120 - 145 days',
        'avg_yield_per_acre_kg': 2200,
        'avg_price_per_kg': 38.0,
        'cost_per_acre': 28000,
        'suitability_score_base': 92,
        'rationale': 'Well suited for clayey and alluvial soils with heavy water retention during monsoon periods.',
        'guidance': 'Ensure uniform puddling during transplanting. Maintain 2-3 cm standing water until grain filling begins.'
    },
    'Banana (Grand Naine)': {
        'suitable_soils': ['Alluvial', 'Loamy', 'Black'],
        'seasons': ['Kharif', 'Rabi', 'Zaid', 'Summer', 'Monsoon'],
        'water_requirements': ['High', 'Irrigated'],
        'duration_days': '300 - 365 days',
        'avg_yield_per_acre_kg': 32000,
        'avg_price_per_kg': 18.0,
        'cost_per_acre': 95000,
        'suitability_score_base': 85,
        'rationale': 'High yielding commercial cash crop with strong year-round wholesale market and retail demand.',
        'guidance': 'Plant tissue-culture suckers with 1.8m x 1.8m spacing. Supply potassium through fertigation during bunch formation.'
    },
    'Cucumber': {
        'suitable_soils': ['Sandy', 'Loamy', 'Alluvial'],
        'seasons': ['Zaid', 'Summer', 'Kharif'],
        'water_requirements': ['Moderate', 'Irrigated'],
        'duration_days': '55 - 70 days',
        'avg_yield_per_acre_kg': 8000,
        'avg_price_per_kg': 20.0,
        'cost_per_acre': 22000,
        'suitability_score_base': 82,
        'rationale': 'Short cultivation cycle enabling quick turnover and fast revenue turnaround between staple rotations.',
        'guidance': 'Trellising on net trellises keeps fruits straight and reduces ground rot risk. Harvest early morning.'
    },
    'Wheat': {
        'suitable_soils': ['Loamy', 'Clay', 'Black', 'Alluvial'],
        'seasons': ['Rabi', 'Winter'],
        'water_requirements': ['Moderate', 'Irrigated'],
        'duration_days': '115 - 130 days',
        'avg_yield_per_acre_kg': 2000,
        'avg_price_per_kg': 26.0,
        'cost_per_acre': 18000,
        'suitability_score_base': 86,
        'rationale': 'Reliable winter staple grain with high bulk procurement options and low perishability.',
        'guidance': 'Schedule first irrigation at crown root initiation stage (20-25 days after sowing).'
    },
    'Soybean': {
        'suitable_soils': ['Black', 'Loamy', 'Clay'],
        'seasons': ['Kharif', 'Monsoon'],
        'water_requirements': ['Moderate', 'Low'],
        'duration_days': '90 - 105 days',
        'avg_yield_per_acre_kg': 1100,
        'avg_price_per_kg': 46.0,
        'cost_per_acre': 14000,
        'suitability_score_base': 80,
        'rationale': 'Nitrogen-fixing legume that rejuvenates soil health while yielding high-protein oilseed with solid mandi pricing.',
        'guidance': 'Treat seeds with Rhizobium culture prior to sowing to maximize root nodule formation.'
    },
    'Groundnut (Peanut)': {
        'suitable_soils': ['Sandy', 'Red', 'Loamy'],
        'seasons': ['Kharif', 'Zaid', 'Summer'],
        'water_requirements': ['Low', 'Moderate'],
        'duration_days': '105 - 120 days',
        'avg_yield_per_acre_kg': 1300,
        'avg_price_per_kg': 58.0,
        'cost_per_acre': 21000,
        'suitability_score_base': 78,
        'rationale': 'Excellent tolerance to lighter, friable soils where peg penetration is effortless.',
        'guidance': 'Apply gypsum at 50 days to strengthen pod shell thickness and kernel filling.'
    }
}

def recommend_crops(location, land_size_acres, soil_type, season, water_availability):
    """
    Transparent rule-based agronomy recommendation engine.
    Calculates suitability scores, yields, costs, and profit estimates.
    """
    try:
        land_size = float(land_size_acres) if land_size_acres else 1.0
        if math.isnan(land_size) or math.isinf(land_size) or land_size <= 0:
            land_size = 1.0
    except (ValueError, TypeError):
        land_size = 1.0
        
    soil_norm = soil_type.strip().title() if soil_type else 'Loamy'
    season_norm = season.strip().title() if season else 'Kharif'
    water_norm = water_availability.strip().title() if water_availability else 'Moderate'

    results = []

    for crop_name, data in CROP_KNOWLEDGE_BASE.items():
        score = data['suitability_score_base']
        
        # Soil match factor
        if any(s.lower() in soil_norm.lower() for s in data['suitable_soils']):
            score += 8
        else:
            score -= 15

        # Season match factor
        if any(s.lower() in season_norm.lower() for s in data['seasons']):
            score += 7
        else:
            score -= 12

        # Water match factor
        if water_norm in data['water_requirements']:
            score += 5
        elif water_norm == 'Low' and 'High' in data['water_requirements']:
            score -= 25
        elif water_norm == 'High' and 'Low' in data['water_requirements']:
            score -= 10
            
        score = max(35, min(98, score))
        
        # Economic calculations for farmer's land size
        est_yield = round(data['avg_yield_per_acre_kg'] * land_size, 1)
        est_cost = round(data['cost_per_acre'] * land_size, 2)
        est_revenue = round(est_yield * data['avg_price_per_kg'], 2)
        est_profit = round(est_revenue - est_cost, 2)
        roi_pct = round((est_profit / est_cost * 100), 1) if est_cost > 0 else 0.0

        results.append({
            'crop_name': crop_name,
            'suitability_score': score,
            'duration': data['duration_days'],
            'estimated_yield': est_yield,
            'unit': 'kg',
            'market_price_ref': data['avg_price_per_kg'],
            'production_cost': est_cost,
            'expected_revenue': est_revenue,
            'net_profit': est_profit,
            'roi_percentage': roi_pct,
            'explanation': data['rationale'],
            'agronomy_guidance': data['guidance'],
            'soil_fit': 'Optimal' if any(s.lower() in soil_norm.lower() for s in data['suitable_soils']) else 'Moderate',
            'water_fit': water_norm
        })

    # Sort descending by suitability score
    results.sort(key=lambda x: x['suitability_score'], reverse=True)
    return results

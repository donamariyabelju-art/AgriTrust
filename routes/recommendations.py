import math
from flask import Blueprint, render_template, request, flash
from services.recommendation_service import RecommendationService
from routes.auth import login_required, role_required

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommendations', methods=['GET', 'POST'])
@login_required
@role_required('FARMER')
def recommendations_view():
    recommendations = []
    form_data = {
        'location': 'Nashik, Maharashtra',
        'land_size': '2.5',
        'soil_type': 'Black',
        'season': 'Kharif',
        'water_availability': 'Irrigated'
    }

    if request.method == 'POST':
        form_data['location'] = request.form.get('location', '').strip() or 'Local Region'
        land_size_input = request.form.get('land_size', '').strip()
        form_data['land_size'] = land_size_input
        form_data['soil_type'] = request.form.get('soil_type', 'Loamy').strip()
        form_data['season'] = request.form.get('season', 'Kharif').strip()
        form_data['water_availability'] = request.form.get('water_availability', 'Moderate').strip()

        # VAL-01: Validate land-size input before numeric conversion
        valid_land_size = True
        parsed_land_size = None
        if not land_size_input:
            valid_land_size = False
        else:
            try:
                val = float(land_size_input)
                if math.isnan(val) or math.isinf(val) or val <= 0:
                    valid_land_size = False
                else:
                    parsed_land_size = val
            except (ValueError, TypeError):
                valid_land_size = False

        if not valid_land_size:
            flash('Please enter a valid positive numeric value for land size in acres.', 'danger')
            return render_template('recommendations.html', recommendations=[], form_data=form_data)

        recommendations = RecommendationService.get_crop_recommendations(
            location=form_data['location'],
            land_size_acres=parsed_land_size,
            soil_type=form_data['soil_type'],
            season=form_data['season'],
            water_availability=form_data['water_availability']
        )
    else:
        # Default initial recommendations
        recommendations = RecommendationService.get_crop_recommendations(
            location=form_data['location'],
            land_size_acres=float(form_data['land_size']),
            soil_type=form_data['soil_type'],
            season=form_data['season'],
            water_availability=form_data['water_availability']
        )

    return render_template('recommendations.html', recommendations=recommendations, form_data=form_data)

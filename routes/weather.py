import os
import requests
from flask import Blueprint, render_template, request, current_app

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/weather')
def weather_view():
    location = request.args.get('location', 'Nashik, Maharashtra').strip()
    api_key = current_app.config.get('WEATHER_API_KEY')
    
    is_live_data = False
    weather_data = {}
    advisories = []

    if api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                is_live_data = True
                weather_data = {
                    'location': f"{data.get('name')}, {data.get('sys', {}).get('country')}",
                    'temperature': round(data['main']['temp'], 1),
                    'feels_like': round(data['main']['feels_like'], 1),
                    'humidity': data['main']['humidity'],
                    'wind_speed': round(data['wind']['speed'] * 3.6, 1),  # m/s to km/h
                    'condition': data['weather'][0]['main'],
                    'description': data['weather'][0]['description'].capitalize(),
                    'rain_prob': 65 if 'Rain' in data['weather'][0]['main'] else 10,
                    'icon': data['weather'][0]['icon']
                }
        except Exception:
            is_live_data = False

    # Honest fallback demonstration data when API key is not configured
    if not is_live_data:
        weather_data = {
            'location': location if location else 'Nashik Agrometeorological Zone',
            'temperature': 28.5,
            'feels_like': 29.8,
            'humidity': 68,
            'wind_speed': 12.4,
            'condition': 'Partly Cloudy',
            'description': 'Scattered cloud cover with moderate humidity',
            'rain_prob': 25,
            'icon': '03d'
        }

    # Generate agronomic advisories based on meteorological metrics
    temp = weather_data['temperature']
    hum = weather_data['humidity']
    rain = weather_data['rain_prob']

    if rain > 50:
        advisories.append({
            'title': 'Rain Alert: Suspend Foliar Spraying',
            'severity': 'warning',
            'advice': 'High precipitation probability detected. Postpone foliar pesticide and fertilizer applications to prevent wash-off into surrounding water tables.'
        })
        advisories.append({
            'title': 'Drainage Precaution',
            'severity': 'info',
            'advice': 'Clear field drainage furrows to prevent standing water accumulation around shallow-rooted crops (tomatoes, peppers).'
        })
    elif hum > 70 and temp > 22:
        advisories.append({
            'title': 'Fungal Blight Risk Elevated',
            'severity': 'warning',
            'advice': 'Current warmth combined with relative humidity above 65% accelerates Alternaria early blight spore sporulation. Scout lower leaves.'
        })
    else:
        advisories.append({
            'title': 'Optimal Morning Irrigation Window',
            'severity': 'success',
            'advice': 'Favorable mild temperatures and moderate wind speed. Ideal timing for scheduled drip fertigation to maximize root uptake.'
        })

    advisories.append({
        'title': 'Harvest Timing Advisory',
        'severity': 'info',
        'advice': 'For mature tomato and cucumber crops, harvest between 6:00 AM and 9:30 AM while internal fruit pulp remains cool to extend transit shelf-life.'
    })

    return render_template(
        'weather.html',
        weather=weather_data,
        advisories=advisories,
        is_live_data=is_live_data,
        api_configured=bool(api_key)
    )

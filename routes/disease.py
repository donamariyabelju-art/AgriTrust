import os
import uuid
from flask import Blueprint, render_template, request, flash, session, current_app, redirect, url_for
from werkzeug.utils import secure_filename
from extensions import db
from models.scan import CropHealthScan
from services.disease_service import DiseaseService
from routes.auth import login_required, role_required

disease_bp = Blueprint('disease', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@disease_bp.route('/crop-health', methods=['GET', 'POST'])
@login_required
@role_required('FARMER')
def crop_health_view():
    scan_result = None
    uploaded_image_url = None
    recent_scans = []
    
    if 'user_id' in session:
        recent_scans = CropHealthScan.query.filter_by(user_id=session['user_id']).order_by(CropHealthScan.created_at.desc()).limit(6).all()

    if request.method == 'POST':
        # Check if file was provided
        if 'crop_image' not in request.files:
            flash('No image file selected.', 'danger')
            return redirect(request.url)

        file = request.files['crop_image']
        demo_mode = request.form.get('demo_mode') == '1'

        if file.filename == '':
            flash('Please choose an image file to upload.', 'warning')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP.', 'danger')
            return redirect(request.url)

        try:
            # Ensure scan upload directory exists
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'scans')
            os.makedirs(upload_dir, exist_ok=True)

            # Generate unique safe filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"scan_{uuid.uuid4().hex[:12]}.{ext}"
            saved_path = os.path.join(upload_dir, unique_filename)
            file.save(saved_path)

            # Relative URL for browser preview
            uploaded_image_url = f"/uploads/scans/{unique_filename}"

            # Process with OpenCV and Model
            result = DiseaseService.process_and_diagnose(saved_path, demo_mode=demo_mode)
            
            if not result.get('success'):
                flash(result.get('error', 'Image processing failed.'), 'danger')
                return render_template('crop_health.html', scan_result=None, uploaded_image_url=None, recent_scans=recent_scans)

            scan_result = result

            # If user is logged in, record in scan history
            if 'user_id' in session:
                scan_record = CropHealthScan(
                    user_id=session['user_id'],
                    crop_name=result.get('plant_name', 'General Crop'),
                    image_path=uploaded_image_url,
                    detected_disease=result.get('detected_disease', 'Unknown'),
                    confidence_score=result.get('confidence_score', 0.0),
                    health_status=result.get('health_status', 'Action Required'),
                    symptoms=result.get('symptoms'),
                    possible_causes=result.get('possible_causes'),
                    preventive_measures=result.get('preventive_measures'),
                    recommended_steps=result.get('recommended_steps'),
                    is_demo_mode=not result.get('model_configured', False)
                )
                db.session.add(scan_record)
                db.session.commit()
                recent_scans = CropHealthScan.query.filter_by(user_id=session['user_id']).order_by(CropHealthScan.created_at.desc()).limit(6).all()

        except Exception as e:
            flash(f"Error analyzing image: {str(e)}", 'danger')

    return render_template(
        'crop_health.html',
        scan_result=scan_result,
        uploaded_image_url=uploaded_image_url,
        recent_scans=recent_scans,
        model_configured=DiseaseService.is_model_configured()
    )

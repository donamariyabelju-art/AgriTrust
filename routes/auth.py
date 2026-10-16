from functools import wraps
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, abort
from extensions import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

def is_safe_redirect_url(target):
    if not target:
        return False
    # Reject protocol-relative URLs (//) and backslash redirects (/\\ or \\)
    if target.startswith('//') or target.startswith('/\\') or '\\' in target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme and target.startswith('/')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            user = db.session.get(User, session['user_id'])
            if not user or user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'FARMER').upper()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()

        # Validation
        if not username or not email or not password or not full_name:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        # SEC-01: Restrict public registration strictly to FARMER and BUYER
        if role not in ['FARMER', 'BUYER']:
            role = 'FARMER'

        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'danger')
            return render_template('register.html')

        new_user = User(
            username=username,
            email=email,
            role=role,
            full_name=full_name,
            phone=phone,
            location=location
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Automatically log in
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['role'] = new_user.role
        session['full_name'] = new_user.full_name

        flash(f'Welcome to AgriTrust, {new_user.full_name}! Your account has been registered successfully.', 'success')
        if new_user.role == 'BUYER':
            return redirect(url_for('marketplace.marketplace_view'))
        return redirect(url_for('dashboard.dashboard_view'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')

        if not login_input or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('login.html')

        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input.lower())
        ).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name

            flash(f'Welcome back, {user.full_name}!', 'success')
            next_url = request.args.get('next')
            # SEC-02: Prevent open redirect via protocol-relative URLs or backslashes
            if is_safe_redirect_url(next_url):
                return redirect(next_url)
            if user.role == 'BUYER':
                return redirect(url_for('marketplace.marketplace_view'))
            elif user.role == 'ADMIN':
                return redirect(url_for('admin.admin_view'))
            return redirect(url_for('dashboard.dashboard_view'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

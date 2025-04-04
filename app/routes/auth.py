from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from ..models.user import Creator
from .. import db
import time
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    # Allow viewing the registration page even when logged in
    # Only redirect after successful registration
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '').strip() or None  # Convert empty string to None
        phone_number = request.form.get('phone_number', '').strip() or None  # Convert empty string to None
        display_name = request.form.get('display_name', username)
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not (email or phone_number):
            error = 'Either email or phone number is required.'
            
        # Format phone number if provided
        if phone_number:
            phone_number = Creator.format_phone_number(phone_number)
            if not phone_number:
                error = 'Invalid phone number format. Use format: 254XXXXXXXXX or 07XXXXXXXX'
            
        if not error:
            if Creator.query.filter_by(username=username).first() is not None:
                error = f'User {username} is already registered.'
            elif email and Creator.query.filter_by(email=email).first() is not None:
                error = f'Email {email} is already registered.'
            elif phone_number and Creator.query.filter_by(phone_number=phone_number).first() is not None:
                error = f'Phone number {phone_number} is already registered.'

        if error is None:
            creator = Creator(
                username=username,
                email=email,  # Will be None if empty string
                phone_number=phone_number,  # Will be None if empty string
                display_name=display_name
            )
            creator.set_password(password)
            db.session.add(creator)
            try:
                db.session.commit()
                # Log the user in immediately after registration
                session.clear()
                session['creator_id'] = creator.id
                session.permanent = True
                return redirect(url_for('dashboard.index'))
            except Exception as e:
                logging.error(f"Registration failed: {str(e)}")
                db.session.rollback()
                error = 'Registration failed. Please try again.'
                flash(error, 'danger')
                return render_template('auth/register.html')

        flash(error, 'danger')  # Changed from 'error' to 'danger' for Bootstrap

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        login = request.form.get('username') or request.form.get('login')  # Handle both old and new form fields
        password = request.form['password']
        error = None
        
        if not login:
            error = 'Email, phone number or username is required.'
        elif not password:
            error = 'Password is required.'
        else:
            # Try to find user by username first (legacy support)
            creator = Creator.query.filter_by(username=login).first()
            
            # If not found, try email/phone lookup
            if not creator:
                creator = Creator.get_by_login(login)

            if creator is None:
                error = 'Invalid credentials.'
            elif not creator.check_password(password):
                error = 'Invalid credentials.'
            elif not creator.active:
                error = 'Account is inactive. Please contact support.'

        if error is None:
            session.clear()
            session['creator_id'] = creator.id
            session.permanent = True
            
            # Update last login time
            creator.update_last_login()
            
            return redirect(url_for('dashboard.index'))

        flash(error, 'danger')
    
    return render_template('auth/login.html')

@auth_bp.before_app_request
def load_logged_in_user():
    creator_id = session.get('creator_id')

    if creator_id is None:
        g.user = None
        g.creator = None
    else:
        creator = Creator.query.get(creator_id)
        if creator is None:
            g.user = None
            g.creator = None
            session.clear()
        else:
            g.user = creator  # For backward compatibility
            g.creator = creator

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    response = redirect(url_for('auth.login'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response 
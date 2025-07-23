from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, EmailCapture
from datetime import datetime
import uuid

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route('/')
def index():
    """Marketing landing page"""
    return render_template('marketing/index.html')

@marketing_bp.route('/dashboard')
def dashboard():
    """Redirect to admin dashboard"""
    return redirect(url_for('admin.dashboard'))

@marketing_bp.route('/docs')
def docs():
    """Documentation page"""
    return render_template('marketing/docs.html')

@marketing_bp.route('/capture_email', methods=['POST'])
def capture_email():
    """Capture email from landing page CTA"""
    email = request.form.get('email', '').strip()
    
    if not email:
        flash('Please provide an email address', 'error')
        return redirect(url_for('marketing.index'))
    
    # Check if email already exists
    existing = EmailCapture.query.filter_by(email=email).first()
    if existing:
        flash('You\'re already on our list! We\'ll notify you when we launch.', 'info')
        return redirect(url_for('marketing.index'))
    
    # Save new email
    capture = EmailCapture(
        email=email,
        source='landing_page'
    )
    db.session.add(capture)
    db.session.commit()
    
    flash('Thank you! We\'ll notify you when Clockchain launches.', 'success')
    return redirect(url_for('marketing.index'))

@marketing_bp.route('/demo')
def demo():
    """Redirect to clockchain demo"""
    return redirect(url_for('clockchain.clockchain_view'))
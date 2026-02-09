"""
Marketing routes for landing page and promotional content
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime, timezone
import logging
import os
import markdown

logger = logging.getLogger(__name__)

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route('/')
def index():
    """Marketing landing page"""
    logger.debug("Serving marketing landing page")
    return render_template('marketing/index.html')

@marketing_bp.route('/dashboard')
def dashboard():
    """Redirect to admin dashboard"""
    logger.debug("Redirecting from marketing dashboard to admin")
    return redirect(url_for('admin.dashboard'))

@marketing_bp.route('/docs')
def docs():
    """Documentation page"""
    logger.debug("Serving marketing docs page")
    return render_template('marketing/docs.html')

@marketing_bp.route('/capture_email', methods=['POST'])
def capture_email():
    """
    Capture email from landing page CTA
    Note: Database models removed in Phase 7 - this now logs emails only
    """
    email = request.form.get('email', '').strip()

    if not email:
        logger.warning("Email capture attempted with empty email")
        flash('Please provide an email address', 'error')
        return redirect(url_for('marketing.index'))

    # Log the email capture (database removed in Phase 7)
    logger.info(f"Email capture: {email} from landing_page at {datetime.now(timezone.utc).isoformat()}")

    flash('Thank you! We\'ll notify you when Clockchain launches.', 'success')
    return redirect(url_for('marketing.index'))

@marketing_bp.route('/dev')
def dev():
    """Developer notes and known issues"""
    logger.debug("Serving dev notes page")
    return render_template('marketing/dev.html')

@marketing_bp.route('/demo')
def demo():
    """Redirect to clockchain demo"""
    logger.debug("Redirecting from marketing demo to clockchain view")
    return redirect(url_for('clockchain.clockchain_view'))

@marketing_bp.route('/whitepaper')
def whitepaper():
    """Render WHITEPAPER.md as a styled HTML page"""
    logger.debug("Serving whitepaper page")
    whitepaper_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'WHITEPAPER.md')
    try:
        with open(whitepaper_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'toc', 'smarty'],
            output_format='html5'
        )
        return render_template('marketing/whitepaper.html', content=html_content)
    except FileNotFoundError:
        logger.error("WHITEPAPER.md not found")
        flash('Whitepaper not found.', 'error')
        return redirect(url_for('marketing.index'))

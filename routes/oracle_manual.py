"""Routes for manual X.com oracle submission"""
import logging
import json
import asyncio
from flask import Blueprint, render_template, request, jsonify, abort, session
# from models import PredictionMarket, OracleSubmission, Actor  # Phase 7: Models removed
# from services.oracle_xcom import XcomOracleService  # Phase 7: Database-dependent
from services.xcom_api_service import XComAPIService
from services.blockchain_base import BaseBlockchainService
from utils.crypto import CryptoUtils
# from app import db  # Phase 7: Database removed
from datetime import datetime
# from sqlalchemy import desc  # Phase 7: SQLAlchemy removed

logger = logging.getLogger(__name__)
oracle_manual_bp = Blueprint('oracle_manual', __name__)

@oracle_manual_bp.route('/oracle/manual/submit/<market_id>')
def manual_submission_form(market_id):
    """Show manual X.com submission form for a market"""
    try:
        market = PredictionMarket.query.get(market_id)
        if not market:
            abort(404)
            
        # Check if market is ready for oracle submission
        if market.status != 'expired':
            return render_template('oracle/error.html', 
                                 error="Market is not ready for oracle submission")
        
        # Get X.com API status
        xcom_service = XComAPIService()
        api_status = xcom_service.get_api_status()
        
        return render_template('oracle/manual_submit.html', 
                             market=market,
                             api_status=api_status)
    except Exception as e:
        logger.error(f"Error loading manual submission form: {e}")
        abort(500)

@oracle_manual_bp.route('/oracle/manual/preview', methods=['POST'])
async def preview_submission():
    """Preview X.com submission before finalizing"""
    try:
        data = request.get_json()
        market_id = data.get('market_id')
        tweet_url = data.get('tweet_url')
        tweet_text = data.get('tweet_text', '')
        tweet_timestamp = data.get('tweet_timestamp', '')
        method = data.get('method', 'manual')  # 'manual' or 'api'
        
        market = PredictionMarket.query.get(market_id)
        if not market:
            return jsonify({'error': 'Market not found'}), 404
            
        xcom_service = XComAPIService()
        
        # Extract tweet ID and username
        tweet_id = xcom_service.extract_tweet_id_from_url(tweet_url)
        username = xcom_service.extract_username_from_url(tweet_url)
        
        if not tweet_id:
            return jsonify({'error': 'Invalid X.com URL format'}), 400
            
        result = {'method': method}
        
        if method == 'api':
            # Try to fetch from API
            tweet_data = await xcom_service.fetch_tweet_by_id(tweet_id)
            if tweet_data:
                result['tweet_data'] = tweet_data
                result['verified'] = True
                result['text'] = tweet_data['text']
                result['timestamp'] = tweet_data['created_at']
                result['username'] = tweet_data['author_username']
            else:
                result['error'] = 'Could not fetch tweet from API'
                result['verified'] = False
        else:
            # Manual submission
            parsed_data = xcom_service.parse_manual_tweet_data(tweet_url, tweet_text, tweet_timestamp)
            result['tweet_data'] = parsed_data
            result['text'] = tweet_text
            result['timestamp'] = tweet_timestamp
            result['username'] = username
            result['verified'] = False  # Manual submissions are not API-verified
            
        # Calculate Levenshtein distances for all submissions
        from services.text_analysis import TextAnalysisService
        text_service = TextAnalysisService()
        
        submissions = market.submissions
        distances = []
        
        for submission in submissions:
            if submission.predicted_text and result.get('text'):
                distance = text_service.calculate_levenshtein_distance(
                    submission.predicted_text,
                    result['text']
                )
                distances.append({
                    'submission_id': str(submission.id),
                    'predicted_text': submission.predicted_text,
                    'distance': distance,
                    'is_null': submission.is_null_submission
                })
                
        result['distances'] = sorted(distances, key=lambda x: x['distance'])
        
        # Try to capture screenshot if possible
        try:
            screenshot = await xcom_service.capture_tweet_screenshot(tweet_url)
            if screenshot:
                result['screenshot'] = screenshot
        except Exception as e:
            logger.warning(f"Could not capture screenshot: {e}")
            result['screenshot'] = None
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error previewing submission: {e}")
        return jsonify({'error': str(e)}), 500

@oracle_manual_bp.route('/oracle/manual/submit', methods=['POST'])
def submit_manual_oracle():
    """Submit manual X.com oracle data"""
    try:
        data = request.get_json()
        
        # Extract submission data
        market_id = data.get('market_id')
        oracle_wallet = data.get('oracle_wallet')
        tweet_url = data.get('tweet_url')
        tweet_text = data.get('tweet_text')
        screenshot_base64 = data.get('screenshot', '')
        signature = data.get('signature')
        
        # Validate required fields
        if not all([market_id, oracle_wallet, tweet_url, tweet_text, signature]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Extract tweet ID
        xcom_service = XComAPIService()
        tweet_id = xcom_service.extract_tweet_id_from_url(tweet_url)
        
        if not tweet_id:
            return jsonify({'error': 'Invalid X.com URL'}), 400
            
        # Use oracle service to submit
        oracle_service = XcomOracleService()
        success = oracle_service.submit_oracle_statement(
            market_id=market_id,
            oracle_wallet=oracle_wallet,
            actual_text=tweet_text,
            tweet_id=tweet_id,
            screenshot_base64=screenshot_base64 or '',
            signature=signature
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Oracle submission successful'})
        else:
            return jsonify({'error': 'Failed to submit oracle data'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting manual oracle: {e}")
        return jsonify({'error': str(e)}), 500

@oracle_manual_bp.route('/oracle/markets/expired')
def expired_markets():
    """List markets ready for oracle submission"""
    try:
        # Get expired markets that need oracle submission
        markets = PredictionMarket.query.filter_by(
            status='expired'
        ).order_by(desc(PredictionMarket.end_time)).all()
        
        # Get X.com API status
        xcom_service = XComAPIService()
        api_status = xcom_service.get_api_status()
        
        # Process market data
        market_data = []
        for market in markets:
            # Count oracle submissions
            oracle_count = OracleSubmission.query.filter_by(
                market_id=market.id
            ).count()
            
            market_data.append({
                'market': market,
                'oracle_count': oracle_count,
                'needs_oracles': oracle_count < 3  # Need at least 3 oracles
            })
            
        return render_template('oracle/expired_markets.html',
                             market_data=market_data,
                             api_status=api_status)
                             
    except Exception as e:
        logger.error(f"Error loading expired markets: {e}")
        return render_template('oracle/expired_markets.html', 
                             market_data=[],
                             api_status={'api_configured': False})
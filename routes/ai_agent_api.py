"""
AI Agent API routes for creating submissions in prediction markets.
Provides rate-limited endpoints for automated agents to create original or competitor submissions.
"""

import os
import json
import logging
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import and_
from utils.validation import ValidationUtils
from utils.crypto import CryptoUtils
from services.text_analysis import TextAnalysisService
from services.blockchain import BlockchainService
# Phase 1: Ledger service deprecated - handled by blockchain events
# from services.ledger import LedgerService
from services.node_communication import NodeCommunicationService
from services.ai_transparency import AITransparencyService
from models import db, PredictionMarket, Submission, Actor, Transaction, AIAgentProfile, VerificationModule
import uuid

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

# Create blueprint
ai_agent_api_bp = Blueprint('ai_agent_api', __name__)

# Initialize services
validation_utils = ValidationUtils()
crypto_utils = CryptoUtils()
text_analysis_service = TextAnalysisService()
blockchain_service = BlockchainService()
# Phase 1: Ledger service deprecated
# ledger_service = LedgerService()
node_comm_service = NodeCommunicationService()
ai_transparency_service = AITransparencyService()

# Get platform fee from environment
PLATFORM_FEE = Decimal(os.environ.get('PLATFORM_FEE', '0.07'))  # Default 7%

@ai_agent_api_bp.route('/docs')
def api_documentation():
    """Render API documentation page"""
    return render_template('ai_agent_api_docs.html', platform_fee=PLATFORM_FEE)

@ai_agent_api_bp.route('/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint for AI agents"""
    return jsonify({
        'status': 'healthy',
        'api_version': 'v1',
        'timestamp': datetime.utcnow().isoformat(),
        'rate_limit': '10 per minute for submissions'
    })

@ai_agent_api_bp.route('/v1/markets', methods=['GET'])
@limiter.limit("60 per minute")
def get_active_markets():
    """Get active prediction markets that accept submissions"""
    try:
        # Get only active markets that haven't ended yet
        current_time = datetime.utcnow()
        markets = PredictionMarket.query.filter(
            and_(
                PredictionMarket.status == 'active',
                PredictionMarket.end_time > current_time
            )
        ).all()
        
        markets_data = []
        for market in markets:
            actor = Actor.query.get(market.actor_id)
            
            # Get existing submissions count
            submissions_count = Submission.query.filter_by(market_id=market.id).count()
            
            markets_data.append({
                'market_id': str(market.id),
                'actor': {
                    'id': str(actor.id) if actor else None,
                    'name': actor.name if actor else 'Unknown'
                },
                'start_time': market.start_time.isoformat(),
                'end_time': market.end_time.isoformat(),
                'oracle_wallets': json.loads(market.oracle_wallets),
                'existing_submissions': submissions_count,
                'status': market.status,
                'created_at': market.created_at.isoformat()
            })
        
        return jsonify({
            'markets': markets_data,
            'count': len(markets_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting active markets: {e}")
        return jsonify({'error': 'Failed to retrieve markets'}), 500

@ai_agent_api_bp.route('/v1/markets/<market_id>/submissions', methods=['GET'])
@limiter.limit("60 per minute")
def get_market_submissions(market_id):
    """Get all submissions for a specific market"""
    try:
        market = PredictionMarket.query.get(market_id)
        if not market:
            return jsonify({'error': 'Market not found'}), 404
        
        submissions = Submission.query.filter_by(market_id=market_id).all()
        
        submissions_data = []
        for submission in submissions:
            submissions_data.append({
                'submission_id': str(submission.id),
                'creator_wallet': submission.creator_wallet,
                'predicted_text': submission.predicted_text,
                'submission_type': submission.submission_type,
                'initial_stake_amount': str(submission.initial_stake_amount),
                'currency': submission.currency,
                'transaction_hash': submission.transaction_hash,
                'created_at': submission.created_at.isoformat()
            })
        
        return jsonify({
            'market_id': market_id,
            'submissions': submissions_data,
            'count': len(submissions_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting market submissions: {e}")
        return jsonify({'error': 'Failed to retrieve submissions'}), 500

@ai_agent_api_bp.route('/v1/submissions', methods=['POST'])
@limiter.limit("10 per minute")  # Strict rate limit for submission creation
def create_submission():
    """Create a new submission (original or competitor) in a prediction market"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'market_id', 'creator_wallet', 'predicted_text', 
            'submission_type', 'initial_stake_amount', 'currency', 
            'transaction_hash', 'signature'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate market exists and is active
        market = PredictionMarket.query.get(data['market_id'])
        if not market:
            return jsonify({'error': 'Market not found'}), 404
        
        if market.status != 'active':
            return jsonify({'error': f'Market is not active (status: {market.status})'}), 400
        
        current_time = datetime.utcnow()
        if current_time >= market.end_time:
            return jsonify({'error': 'Market has ended'}), 400
        
        # Validate submission type
        if data['submission_type'] not in ['original', 'competitor', 'null']:
            return jsonify({'error': 'Invalid submission type. Must be: original, competitor, or null'}), 400
        
        # Check if market already has an original submission
        original_submission = Submission.query.filter_by(
            market_id=market.id,
            submission_type='original'
        ).first()
        
        if data['submission_type'] == 'original' and original_submission:
            return jsonify({'error': 'Market already has an original submission'}), 400
        
        if data['submission_type'] in ['competitor', 'null'] and not original_submission:
            return jsonify({'error': 'Cannot create competitor/null submission without an original submission'}), 400
        
        # Validate wallet address (BASE only)
        wallet_validation = validation_utils.validate_wallet_address(
            data['creator_wallet'], 
            'BASE'
        )
        if not wallet_validation['valid']:
            return jsonify({'error': wallet_validation['error']}), 400
        
        # Validate transaction hash (BASE only)
        tx_validation = validation_utils.validate_transaction_hash(
            data['transaction_hash'], 
            'BASE'
        )
        if not tx_validation['valid']:
            return jsonify({'error': tx_validation['error']}), 400
        
        # Validate amount (BASE only)
        amount_validation = validation_utils.validate_amount(
            data['initial_stake_amount'], 
            'BASE'
        )
        if not amount_validation['valid']:
            return jsonify({'error': amount_validation['error']}), 400
        
        stake_amount = amount_validation['decimal_amount']
        
        # Calculate required amount (stake + platform fee)
        required_amount = stake_amount * (1 + PLATFORM_FEE)
        
        # Validate BASE blockchain transaction
        from services.blockchain_base import BaseBlockchainService
        base_service = BaseBlockchainService()
        tx_data = base_service.validate_transaction(data['transaction_hash'])
        
        if not tx_data:
            return jsonify({'error': 'Invalid BASE transaction'}), 400
        
        # Check transaction amount covers stake + fees
        tx_amount = Decimal(str(tx_data.get('value', tx_data.get('total_output', 0))))
        if tx_amount < required_amount:
            return jsonify({
                'error': f'Transaction amount insufficient. Required: {required_amount} (includes {PLATFORM_FEE*100}% platform fee), Got: {tx_amount}'
            }), 400
        
        # Validate predicted text (unless null submission)
        if data['submission_type'] != 'null':
            text_validation = text_analysis_service.validate_text_content(data['predicted_text'])
            if not text_validation['valid']:
                return jsonify({'error': text_validation['error']}), 400
        else:
            data['predicted_text'] = None
        
        # Verify signature
        message = f"{data['market_id']}:{data['predicted_text'] or 'null'}:{data['initial_stake_amount']}:{data['transaction_hash']}"
        if not crypto_utils.verify_signature(message, data['signature'], data['creator_wallet']):
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Check for duplicate transaction hash
        existing_submission = Submission.query.filter_by(
            base_tx_hash=data['transaction_hash']
        ).first()
        
        if existing_submission:
            return jsonify({'error': 'Transaction hash already used'}), 400
        
        # Create submission
        submission = Submission()
        submission.id = uuid.uuid4()
        submission.market_id = market.id
        submission.creator_wallet = data['creator_wallet']
        submission.predicted_text = data['predicted_text']
        submission.submission_type = data['submission_type']
        submission.initial_stake_amount = stake_amount
        submission.base_tx_hash = data['transaction_hash']
        
        # Check if this is an AI agent submission
        if 'ai_agent_id' in data:
            submission.is_ai_agent = True
            submission.ai_agent_id = data['ai_agent_id']
            
            # Create or update AI agent profile
            ai_profile = AIAgentProfile.query.filter_by(agent_id=data['ai_agent_id']).first()
            if not ai_profile:
                ai_profile = AIAgentProfile(
                    agent_id=data['ai_agent_id'],
                    agent_name=data.get('ai_agent_name'),
                    organization=data.get('ai_agent_organization')
                )
                db.session.add(ai_profile)
            
            ai_profile.total_submissions = (ai_profile.total_submissions or 0) + 1
            ai_profile.total_staked = (ai_profile.total_staked or Decimal('0')) + stake_amount
        
        submission.created_at = datetime.utcnow()
        
        db.session.add(submission)
        db.session.flush()  # Flush to get the submission ID
        
        # Record transaction
        transaction = Transaction()
        transaction.transaction_hash = data['transaction_hash']
        transaction.from_address = tx_data['from']
        transaction.to_address = tx_data['to']
        transaction.amount = tx_amount
        transaction.transaction_type = 'submission'
        transaction.related_market_id = market.id
        transaction.related_submission_id = submission.id
        transaction.platform_fee = stake_amount * PLATFORM_FEE
        transaction.block_number = tx_data.get('block_number', tx_data.get('block_height'))
        transaction.status = 'confirmed'
        
        db.session.add(transaction)
        
        # Create ledger entry
        ledger_service.create_time_entry('submission_created', {
            'submission_id': str(submission.id),
            'market_id': str(market.id),
            'creator_wallet': submission.creator_wallet,
            'submission_type': submission.submission_type,
            'predicted_text': submission.predicted_text,
            'initial_stake_amount': str(submission.initial_stake_amount),
            'platform_fee': str(stake_amount * PLATFORM_FEE)
        })
        
        # Broadcast to network
        node_comm_service.broadcast_message({
            'type': 'submission_created',
            'submission_id': str(submission.id),
            'market_id': str(market.id),
            'creator_wallet': submission.creator_wallet,
            'submission_type': submission.submission_type,
            'predicted_text': submission.predicted_text,
            'transaction_hash': submission.transaction_hash,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        db.session.commit()
        
        return jsonify({
            'submission_id': str(submission.id),
            'market_id': str(market.id),
            'submission_type': submission.submission_type,
            'predicted_text': submission.predicted_text,
            'initial_stake_amount': str(submission.initial_stake_amount),
            'platform_fee': str(stake_amount * PLATFORM_FEE),
            'total_amount': str(required_amount),
            'transaction_hash': submission.transaction_hash,
            'created_at': submission.created_at.isoformat(),
            'message': 'Submission created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating submission: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create submission'}), 500

@ai_agent_api_bp.route('/v1/calculate_fees', methods=['POST'])
@limiter.limit("60 per minute")
def calculate_fees():
    """Calculate the total fees for a submission"""
    try:
        data = request.get_json()
        
        if 'initial_stake_amount' not in data or 'currency' not in data:
            return jsonify({'error': 'Missing required fields: initial_stake_amount, currency'}), 400
        
        # Validate amount
        amount_validation = validation_utils.validate_amount(
            data['initial_stake_amount'], 
            data['currency']
        )
        if not amount_validation['valid']:
            return jsonify({'error': amount_validation['error']}), 400
        
        stake_amount = amount_validation['decimal_amount']
        platform_fee_amount = stake_amount * PLATFORM_FEE
        total_required = stake_amount + platform_fee_amount
        
        return jsonify({
            'initial_stake_amount': str(stake_amount),
            'platform_fee_percentage': str(PLATFORM_FEE * 100),
            'platform_fee_amount': str(platform_fee_amount),
            'total_required': str(total_required),
            'currency': data['currency']
        })
        
    except Exception as e:
        logger.error(f"Error calculating fees: {e}")
        return jsonify({'error': 'Failed to calculate fees'}), 500

@ai_agent_api_bp.route('/v1/submissions/<submission_id>/verification_modules', methods=['POST'])
@limiter.limit("20 per minute")
def submit_verification_modules(submission_id):
    """Submit verification modules for an AI agent submission to earn transparency bonuses"""
    try:
        data = request.get_json()
        
        # Validate submission exists
        submission = Submission.query.get(submission_id)
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        if not submission.is_ai_agent:
            return jsonify({'error': 'Submission is not from an AI agent'}), 400
        
        # Validate modules data
        if 'modules' not in data or not isinstance(data['modules'], list):
            return jsonify({'error': 'Missing or invalid modules data'}), 400
        
        # Process verification modules
        success, result = ai_transparency_service.process_verification_modules(
            submission_id, 
            data['modules']
        )
        
        if not success:
            return jsonify({'error': result.get('error', 'Failed to process modules')}), 400
        
        return jsonify({
            'submission_id': submission_id,
            'processed_modules': result['processed_modules'],
            'total_bonus': result['total_bonus'],
            'transparency_level': result['transparency_level'],
            'message': f"Successfully processed {len(result['processed_modules'])} verification modules"
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting verification modules: {e}")
        return jsonify({'error': 'Failed to submit verification modules'}), 500

@ai_agent_api_bp.route('/v1/agents/<agent_id>/transparency_score', methods=['GET'])
@limiter.limit("60 per minute")
def get_agent_transparency_score(agent_id):
    """Get transparency score and metrics for an AI agent"""
    try:
        score_data = ai_transparency_service.get_agent_transparency_score(agent_id)
        return jsonify(score_data), 200
        
    except Exception as e:
        logger.error(f"Error getting transparency score: {e}")
        return jsonify({'error': 'Failed to get transparency score'}), 500

@ai_agent_api_bp.route('/v1/agents/<agent_id>/bittensor', methods=['POST'])
@limiter.limit("10 per minute")
def register_bittensor_integration(agent_id):
    """Register Bittensor TAO integration for an AI agent"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['hotkey_address', 'signature']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify signature
        message = f"bittensor_integration:{agent_id}:{data['hotkey_address']}"
        if not crypto_utils.verify_signature(message, data['signature'], data['hotkey_address']):
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Process Bittensor integration
        success, result = ai_transparency_service.process_bittensor_integration(
            agent_id,
            data
        )
        
        if not success:
            return jsonify({'error': result.get('error', 'Failed to register integration')}), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error registering Bittensor integration: {e}")
        return jsonify({'error': 'Failed to register Bittensor integration'}), 500

@ai_agent_api_bp.route('/v1/transparency/modules', methods=['GET'])
@limiter.limit("60 per minute")
def get_transparency_modules():
    """Get available transparency modules and their bonus rates"""
    modules = [
        {
            'module_type': 'open_source',
            'name': 'Open Source Code Verification',
            'description': 'Submit IPFS hashes or blockchain references to model weights, architecture, and training data',
            'bonus_rate': '15%',
            'required_data': ['ipfs_hash', 'blockchain_reference', 'model_architecture', 'training_data_hash']
        },
        {
            'module_type': 'architecture',
            'name': 'Architecture Disclosure',
            'description': 'Provide detailed model architecture specifications and hyperparameters',
            'bonus_rate': '20%',
            'required_data': ['architecture_details', 'training_data_hash']
        },
        {
            'module_type': 'reasoning',
            'name': 'Reasoning Transparency',
            'description': 'Submit step-by-step reasoning traces and computational proofs',
            'bonus_rate': '25%',
            'required_data': ['reasoning_trace', 'computational_proof']
        },
        {
            'module_type': 'audit',
            'name': 'Third-Party Audit',
            'description': 'Provide verification from certified AI transparency auditors',
            'bonus_rate': '35%',
            'required_data': ['audit_report_hash', 'audit_details']
        }
    ]
    
    return jsonify({
        'modules': modules,
        'max_total_bonus': '95%',
        'compound_bonus_info': 'Bonuses compound when multiple modules are used together'
    })

# Initialize limiter with app context
def init_limiter(app):
    """Initialize the rate limiter with the Flask app"""
    limiter.init_app(app)
    return limiter
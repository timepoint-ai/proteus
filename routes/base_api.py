from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import json
from services.blockchain_base import BaseBlockchainService
from services.oracle_xcom import XcomOracleService
from services.payout_base import BasePayoutService
from models import PredictionMarket, Submission, Bet, Actor, Transaction
from app import db
import os

logger = logging.getLogger(__name__)

base_api_bp = Blueprint('base_api', __name__)

# Initialize services
blockchain_service = BaseBlockchainService()
oracle_service = XcomOracleService()
payout_service = BasePayoutService()

# Load contract deployment if available
deployment_file = 'deployment-sepolia.json' if os.environ.get('NETWORK') == 'testnet' else 'deployment-mainnet.json'
if os.path.exists(deployment_file):
    blockchain_service.load_contracts(deployment_file)

@base_api_bp.route('/markets/create', methods=['POST'])
def create_market():
    """Create a new prediction market on BASE blockchain"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['question', 'actor_handle', 'duration_hours', 
                          'initial_stake', 'creator_wallet', 'xcom_only']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Get or create actor
        actor = Actor.query.filter_by(name=data['actor_handle']).first()
        if not actor:
            # Create new actor
            actor = Actor(
                name=data['actor_handle'],
                description=f"X.com handle: @{data['actor_handle']}",
                status='approved'  # Auto-approve for BASE integration
            )
            db.session.add(actor)
            db.session.flush()
            
        # Calculate timestamps
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=int(data['duration_hours']))
        
        # Create market in database
        market = PredictionMarket(
            actor_id=actor.id,
            start_time=start_time,
            end_time=end_time,
            oracle_wallets=json.dumps(data.get('oracle_wallets', [])),
            xcom_only=data['xcom_only'],
            twitter_handle=data['actor_handle'],  # Use the provided handle
            status='active'
        )
        
        db.session.add(market)
        db.session.flush()  # Get ID without committing
        
        # Calculate fees
        initial_stake = Decimal(str(data['initial_stake']))
        platform_fee = blockchain_service.calculate_platform_fee(initial_stake)
        total_amount = initial_stake + platform_fee
        
        # Prepare blockchain transaction
        if blockchain_service.contracts['PredictionMarket']:
            # Use smart contract
            tx_data = blockchain_service.create_market(
                data['question'],
                int(data['duration_hours']) * 3600,  # Convert to seconds
                data['actor_handle'],  # Use the provided handle
                data['xcom_only'],
                initial_stake,
                data['creator_wallet']
            )
            
            response = {
                'market_id': str(market.id),
                'blockchain_tx': {
                    'to': blockchain_service.contracts['PredictionMarket'].address,
                    'value': str(total_amount),
                    'platform_fee': str(platform_fee),
                    'gas_estimate': tx_data['params']['gas'],
                    'data': 'Contract call to createMarket'
                },
                'message': 'Market created in database. Send transaction to complete.'
            }
        else:
            # Manual transaction (no contract deployed)
            response = {
                'market_id': str(market.id),
                'manual_tx': {
                    'platform_wallet': os.environ.get('PLATFORM_WALLET', '0x0000000000000000000000000000000000000000'),
                    'amount': str(total_amount),
                    'platform_fee': str(platform_fee),
                    'initial_stake': str(initial_stake)
                },
                'message': 'Market created. Manual transaction required (no contract deployed).'
            }
            
        # Create initial submission
        predicted_text = data.get('predicted_text', '')
        submission_type = 'null' if not predicted_text else 'original'
        
        submission = Submission(
            market_id=market.id,
            creator_wallet=data['creator_wallet'],
            predicted_text=predicted_text if predicted_text else None,
            initial_stake_amount=initial_stake,
            submission_type=submission_type,
            base_tx_hash='0x' + '0' * 64  # Placeholder until actual transaction
        )
        
        db.session.add(submission)
        market.total_volume = initial_stake
        
        db.session.commit()
        
        return jsonify(response), 201
        
    except Exception as e:
        logger.error(f"Error creating market: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        
@base_api_bp.route('/markets/<market_id>/oracle/submit', methods=['POST'])
def submit_oracle_data():
    """Submit oracle data with X.com verification"""
    try:
        data = request.get_json()
        market_id = market_id
        
        # Validate required fields
        required_fields = ['oracle_wallet', 'actual_text', 'tweet_id', 'signature']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Capture screenshot if tweet URL provided
        screenshot_base64 = ''
        if 'tweet_url' in data:
            screenshot_base64 = oracle_service.capture_xcom_screenshot(data['tweet_url'])
            if not screenshot_base64:
                return jsonify({'error': 'Failed to capture screenshot'}), 500
                
        # Submit oracle statement
        success = oracle_service.submit_oracle_statement(
            market_id,
            data['oracle_wallet'],
            data['actual_text'],
            data['tweet_id'],
            screenshot_base64,
            data['signature']
        )
        
        if success:
            return jsonify({
                'message': 'Oracle submission successful',
                'market_id': market_id
            }), 201
        else:
            return jsonify({'error': 'Failed to submit oracle data'}), 400
            
    except Exception as e:
        logger.error(f"Error submitting oracle data: {e}")
        return jsonify({'error': str(e)}), 500
        
@base_api_bp.route('/markets/<market_id>/payouts', methods=['GET'])
def get_market_payouts():
    """Calculate payouts for a resolved market"""
    try:
        market_id = market_id
        
        # Calculate payouts
        payout_info = payout_service.calculate_payouts(market_id)
        
        if 'error' in payout_info:
            return jsonify(payout_info), 400
            
        return jsonify(payout_info), 200
        
    except Exception as e:
        logger.error(f"Error calculating payouts: {e}")
        return jsonify({'error': str(e)}), 500
        
@base_api_bp.route('/transactions/estimate-gas', methods=['POST'])
def estimate_gas():
    """Estimate gas for a transaction"""
    try:
        data = request.get_json()
        tx_type = data.get('type', 'transfer')
        
        gas_prices = blockchain_service.estimate_gas_price()
        
        # Estimate gas based on transaction type
        gas_estimates = {
            'market_creation': 300000,
            'submission': 150000,
            'bet': 100000,
            'oracle_submit': 200000,
            'payout_claim': 100000,
            'transfer': 21000
        }
        
        gas_limit = gas_estimates.get(tx_type, 100000)
        
        return jsonify({
            'gas_limit': gas_limit,
            'gas_prices': {
                'slow': {
                    'gwei': blockchain_service.w3.from_wei(gas_prices['slow'], 'gwei'),
                    'total_cost_eth': blockchain_service.w3.from_wei(gas_limit * gas_prices['slow'], 'ether')
                },
                'standard': {
                    'gwei': blockchain_service.w3.from_wei(gas_prices['standard'], 'gwei'),
                    'total_cost_eth': blockchain_service.w3.from_wei(gas_limit * gas_prices['standard'], 'ether')
                },
                'fast': {
                    'gwei': blockchain_service.w3.from_wei(gas_prices['fast'], 'gwei'),
                    'total_cost_eth': blockchain_service.w3.from_wei(gas_limit * gas_prices['fast'], 'ether')
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error estimating gas: {e}")
        return jsonify({'error': str(e)}), 500
        
@base_api_bp.route('/network/status', methods=['GET'])
def network_status():
    """Get BASE network status"""
    try:
        # Get latest block
        latest_block = blockchain_service.w3.eth.get_block('latest')
        
        # Get gas prices
        gas_prices = blockchain_service.estimate_gas_price()
        
        # Get chain ID
        chain_id = blockchain_service.chain_id
        
        return jsonify({
            'network': 'BASE ' + ('Mainnet' if chain_id == 8453 else 'Sepolia Testnet'),
            'chain_id': chain_id,
            'connected': blockchain_service.w3.is_connected(),
            'latest_block': {
                'number': latest_block['number'],
                'timestamp': latest_block['timestamp'],
                'gas_limit': latest_block['gasLimit'],
                'gas_used': latest_block['gasUsed']
            },
            'gas_prices': {
                'slow': blockchain_service.w3.from_wei(gas_prices['slow'], 'gwei'),
                'standard': blockchain_service.w3.from_wei(gas_prices['standard'], 'gwei'),
                'fast': blockchain_service.w3.from_wei(gas_prices['fast'], 'gwei')
            },
            'contracts_loaded': {
                'PredictionMarket': blockchain_service.contracts['PredictionMarket'] is not None,
                'ClockchainOracle': blockchain_service.contracts['ClockchainOracle'] is not None,
                'NodeRegistry': blockchain_service.contracts['NodeRegistry'] is not None,
                'PayoutManager': blockchain_service.contracts['PayoutManager'] is not None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting network status: {e}")
        return jsonify({'error': str(e)}), 500
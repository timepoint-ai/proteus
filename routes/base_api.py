from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import json
from services.blockchain_base import BaseBlockchainService
# from services.oracle_xcom import XcomOracleService  # Phase 7: Database-dependent
# from services.payout_base import BasePayoutService  # Phase 7: Database-dependent
# from models import PredictionMarket, Submission, Bet, Actor, Transaction  # Phase 7: Models removed
# from app import db  # Phase 7: Database removed
import os

logger = logging.getLogger(__name__)

base_api_bp = Blueprint('base_api', __name__)

# Initialize services
blockchain_service = BaseBlockchainService()
# oracle_service = XcomOracleService()  # Phase 7: Database-dependent
# payout_service = BasePayoutService()  # Phase 7: Database-dependent

# Load contract deployment if available
deployment_file = 'deployment-sepolia.json' if os.environ.get('NETWORK') == 'testnet' else 'deployment-mainnet.json'
if os.path.exists(deployment_file):
    blockchain_service.load_contracts(deployment_file)

@base_api_bp.route('/markets/create', methods=['POST'])
def create_market():
    """Create a new prediction market on BASE blockchain - Phase 7 Chain-Only"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['question', 'actor_handle', 'duration_hours', 
                          'initial_stake', 'creator_wallet']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Phase 7: Direct blockchain interaction only
        # Return transaction parameters for frontend to execute
        initial_stake = Decimal(str(data['initial_stake']))
        duration_seconds = int(data['duration_hours']) * 3600
        
        # Prepare response with blockchain transaction details
        response = {
            'success': True,
            'message': 'Transaction parameters prepared. Execute on blockchain.',
            'transaction': {
                'contract_address': os.environ.get('ENHANCED_PREDICTION_MARKET_ADDRESS', '0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c'),
                'method': 'createMarket',
                'params': {
                    'question': data['question'],
                    'actorUsername': data['actor_handle'].replace('@', ''),  # Remove @ if present
                    'duration': duration_seconds,
                    'oracleWallets': data.get('oracle_wallets', [data['creator_wallet'], '0x0000000000000000000000000000000000000001', '0x0000000000000000000000000000000000000002']),
                    'metadata': json.dumps({
                        'created': datetime.utcnow().isoformat(),
                        'creator': data['creator_wallet'],
                        'predicted_text': data.get('predicted_text', '')
                    })
                },
                'value': '0',  # No ETH sent for market creation
                'initial_stake_info': {
                    'amount': str(initial_stake),
                    'note': 'Create initial submission after market creation'
                }
            },
            'instructions': [
                '1. Execute createMarket transaction with provided parameters',
                '2. Wait for confirmation and get market ID from event',
                '3. Create initial submission with predicted text and stake'
            ]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error preparing market creation: {e}")
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
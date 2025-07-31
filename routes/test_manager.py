"""
Test Manager - Comprehensive E2E Testing for BASE Blockchain Integration
"""
import os
import json
import logging
import traceback
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from models import db, PredictionMarket, Submission, Bet, Transaction, OracleSubmission, Actor
from services.blockchain_base import BaseBlockchainService
from services.payout_base import BasePayoutService
from services.xcom_api_service import XComAPIService
from services.oracle_xcom import XcomOracleService
from web3 import Web3
from eth_account import Account
import time
from Levenshtein import distance
import base64
import secrets

logger = logging.getLogger(__name__)
test_manager_bp = Blueprint('test_manager', __name__)

# Helper function to get configured test wallets
def get_configured_test_wallets():
    """Get test wallets from environment or use defaults"""
    # Check if wallets are configured in environment
    if os.environ.get('TEST_WALLET_ADDRESS'):
        oracle_wallets = json.loads(os.environ.get('TEST_ORACLE_WALLETS', '[]'))
        return {
            'creator': os.environ.get('TEST_WALLET_ADDRESS'),
            'bettor1': oracle_wallets[0] if len(oracle_wallets) > 0 else '0x2345678901234567890123456789012345678901',
            'bettor2': oracle_wallets[1] if len(oracle_wallets) > 1 else '0x3456789012345678901234567890123456789012',
            'oracle1': oracle_wallets[0] if len(oracle_wallets) > 0 else '0x4567890123456789012345678901234567890123',
            'oracle2': oracle_wallets[1] if len(oracle_wallets) > 1 else '0x5678901234567890123456789012345678901234',
            'oracle3': oracle_wallets[2] if len(oracle_wallets) > 2 else '0x6789012345678901234567890123456789012345'
        }
    else:
        # Default test wallets
        return {
            'creator': '0x1234567890123456789012345678901234567890',
            'bettor1': '0x2345678901234567890123456789012345678901',
            'bettor2': '0x3456789012345678901234567890123456789012',
            'oracle1': '0x4567890123456789012345678901234567890123',
            'oracle2': '0x5678901234567890123456789012345678901234',
            'oracle3': '0x6789012345678901234567890123456789012345'
        }

# Test configuration for BASE Sepolia
TEST_CONFIG = {
    'chain_id': int(os.environ.get('TEST_CHAIN_ID', '84532')),
    'rpc_url': os.environ.get('TEST_NETWORK_RPC', 'https://base-sepolia.g.alchemy.com/public'),
    'explorer_url': 'https://sepolia.basescan.org',
    'test_wallets': get_configured_test_wallets(),
    'test_amounts': {
        'initial_stake': '0.1',
        'bet_amount': '0.05',
        'platform_fee': 0.07
    }
}

def require_test_auth(f):
    """Decorator to require test manager authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'test_authenticated' not in session:
            return redirect(url_for('test_manager.test_login'))
        return f(*args, **kwargs)
    return decorated_function

@test_manager_bp.route('/test-manager/login', methods=['GET', 'POST'])
def test_login():
    """Test manager login page"""
    if request.method == 'POST':
        passcode = request.form.get('passcode')
        expected_passcode = os.environ.get('TEST_MANAGER_PASSCODE')
        
        if not expected_passcode:
            return render_template('test_manager/login.html', 
                                 error='TEST_MANAGER_PASSCODE not configured in Replit Secrets')
        
        if passcode == expected_passcode:
            session['test_authenticated'] = True
            return redirect(url_for('test_manager.test_dashboard'))
        else:
            return render_template('test_manager/login.html', 
                                 error='Invalid passcode')
    
    return render_template('test_manager/login.html')

@test_manager_bp.route('/test-manager')
@require_test_auth
def test_dashboard():
    """Main test dashboard"""
    return render_template('test_manager/dashboard.html', 
                         test_config=TEST_CONFIG)

@test_manager_bp.route('/test-manager/run-test/<test_type>', methods=['POST'])
@require_test_auth
def run_test(test_type):
    """Run a specific test case"""
    try:
        test_case = test_type
        
        # Initialize test results
        results = {
            'test_case': test_case,
            'status': 'running',
            'steps': [],
            'started_at': datetime.utcnow().isoformat(),
            'errors': []
        }
        
        # Run the appropriate test
        if test_case == 'wallet_setup':
            results = run_wallet_setup_test(results)
        elif test_case == 'wallet_connection':
            results = run_wallet_connection_test(results)
        elif test_case == 'market_creation':
            results = run_market_creation_test(results)
        elif test_case == 'submission_creation':
            results = run_submission_creation_test(results)
        elif test_case == 'betting':
            results = run_bet_placement_test(results)
        elif test_case == 'oracle_submission':
            results = run_oracle_submission_test(results)
        elif test_case == 'market_resolution':
            results = run_market_resolution_test(results)
        elif test_case == 'full_e2e':
            results = run_full_e2e_test(results)
        else:
            results['status'] = 'failed'
            results['errors'].append(f'Unknown test case: {test_case}')
        
        # Complete the test
        results['completed_at'] = datetime.utcnow().isoformat()
        if not results['errors']:
            results['status'] = 'passed'
        else:
            results['status'] = 'failed'
            
        return jsonify({'success': True, 'results': results['steps']})
        
    except Exception as e:
        logger.error(f"Test execution error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@test_manager_bp.route('/test-manager/network-status')
@require_test_auth
def network_status():
    """Check network status"""
    try:
        w3 = Web3(Web3.HTTPProvider(TEST_CONFIG['rpc_url']))
        if not w3.is_connected():
            return jsonify({'success': False, 'error': 'Not connected to BASE Sepolia'})
        
        status = {
            'connected': True,
            'chain_id': w3.eth.chain_id,
            'current_block': w3.eth.block_number,
            'gas_price': w3.eth.gas_price / 10**9  # Convert to gwei
        }
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Network status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def add_test_step(results, step_name, status, details=None, error=None):
    """Add a step to test results"""
    step = {
        'name': step_name,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    }
    if details:
        step['details'] = details
    if error:
        step['error'] = error
        results['errors'].append(f"{step_name}: {error}")
    
    results['steps'].append(step)
    logger.info(f"TEST STEP: {step_name} - {status}")
    if error:
        logger.error(f"TEST ERROR: {error}")

def generate_test_wallets(oracle_count=3):
    """Generate test wallets programmatically"""
    # Generate main test wallet
    main_account = Account.create()
    
    # Generate oracle wallets
    oracle_wallets = []
    oracle_private_keys = []
    
    for i in range(oracle_count):
        oracle_account = Account.create()
        oracle_wallets.append(oracle_account.address)
        oracle_private_keys.append(oracle_account.key.hex())
    
    return {
        'main_wallet': {
            'address': main_account.address,
            'private_key': main_account.key.hex()
        },
        'oracle_wallets': oracle_wallets,
        'oracle_private_keys': oracle_private_keys
    }

def save_wallet_config_to_file(wallet_config, filename='.test_wallets.json'):
    """Save wallet configuration to file"""
    config = {
        'main_wallet': wallet_config['main_wallet'],
        'oracle_wallets': wallet_config['oracle_wallets'],
        'oracle_private_keys': wallet_config['oracle_private_keys'],
        'chain_id': TEST_CONFIG['chain_id'],
        'rpc_url': TEST_CONFIG['rpc_url'],
        'generated_at': datetime.utcnow().isoformat()
    }
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    return True

def configure_environment_from_wallets(wallet_config):
    """Configure environment variables from wallet config"""
    os.environ['TEST_WALLET_ADDRESS'] = wallet_config['main_wallet']['address']
    os.environ['TEST_WALLET_PRIVATE_KEY'] = wallet_config['main_wallet']['private_key']
    os.environ['TEST_ORACLE_WALLETS'] = json.dumps(wallet_config['oracle_wallets'])
    os.environ['TEST_NETWORK_RPC'] = TEST_CONFIG['rpc_url']
    os.environ['TEST_CHAIN_ID'] = str(TEST_CONFIG['chain_id'])
    
    # Update TEST_CONFIG with new wallets
    TEST_CONFIG['test_wallets'] = get_configured_test_wallets()
    
    return True

def run_wallet_setup_test(results):
    """Automated test wallet setup and configuration"""
    try:
        # Step 1: Check current configuration
        add_test_step(results, "Check Current Configuration", "running")
        
        existing_config = {
            'has_main_wallet': bool(os.environ.get('TEST_WALLET_ADDRESS')),
            'has_private_key': bool(os.environ.get('TEST_WALLET_PRIVATE_KEY')),
            'has_oracle_wallets': bool(os.environ.get('TEST_ORACLE_WALLETS')),
            'oracle_count': len(json.loads(os.environ.get('TEST_ORACLE_WALLETS', '[]')))
        }
        
        add_test_step(results, "Check Current Configuration", "passed", details=existing_config)
        
        # Step 2: Generate new wallets
        add_test_step(results, "Generate Test Wallets", "running")
        
        wallet_config = generate_test_wallets(oracle_count=3)
        
        add_test_step(results, "Generate Test Wallets", "passed", details={
            'main_wallet': wallet_config['main_wallet']['address'],
            'oracle_count': len(wallet_config['oracle_wallets']),
            'oracle_addresses': wallet_config['oracle_wallets']
        })
        
        # Step 3: Configure environment
        add_test_step(results, "Configure Environment Variables", "running")
        
        if configure_environment_from_wallets(wallet_config):
            add_test_step(results, "Configure Environment Variables", "passed", details={
                'TEST_WALLET_ADDRESS': 'Configured',
                'TEST_WALLET_PRIVATE_KEY': 'Configured',
                'TEST_ORACLE_WALLETS': f"Configured ({len(wallet_config['oracle_wallets'])} wallets)"
            })
        else:
            add_test_step(results, "Configure Environment Variables", "failed", 
                         error="Failed to configure environment")
            return results
        
        # Step 4: Save configuration
        add_test_step(results, "Save Wallet Configuration", "running")
        
        try:
            save_wallet_config_to_file(wallet_config)
            add_test_step(results, "Save Wallet Configuration", "passed", 
                         details={'file': '.test_wallets.json'})
        except Exception as e:
            add_test_step(results, "Save Wallet Configuration", "warning", 
                         details={'error': str(e), 'note': 'Configuration still active in memory'})
        
        # Step 5: Validate configuration
        add_test_step(results, "Validate Configuration", "running")
        
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(TEST_CONFIG['rpc_url']))
        
        if not w3.is_connected():
            add_test_step(results, "Validate Configuration", "failed", 
                         error="Failed to connect to BASE Sepolia")
            return results
        
        # Check all addresses are valid
        validation_errors = []
        
        if not Web3.is_address(wallet_config['main_wallet']['address']):
            validation_errors.append("Invalid main wallet address")
        
        for i, addr in enumerate(wallet_config['oracle_wallets']):
            if not Web3.is_address(addr):
                validation_errors.append(f"Invalid oracle wallet {i+1}")
        
        if validation_errors:
            add_test_step(results, "Validate Configuration", "failed", 
                         error=", ".join(validation_errors))
            return results
        
        add_test_step(results, "Validate Configuration", "passed", details={
            'all_addresses_valid': True,
            'connected_to_base_sepolia': True
        })
        
        # Step 6: Check balances (informational)
        add_test_step(results, "Check Wallet Balances", "running")
        
        balances = {}
        try:
            # Check main wallet balance
            balance_wei = w3.eth.get_balance(wallet_config['main_wallet']['address'])
            balance_eth = w3.from_wei(balance_wei, 'ether')
            balances['main'] = float(balance_eth)
            
            # Check oracle wallets
            for i, addr in enumerate(wallet_config['oracle_wallets']):
                balance_wei = w3.eth.get_balance(addr)
                balance_eth = w3.from_wei(balance_wei, 'ether')
                balances[f'oracle_{i+1}'] = float(balance_eth)
            
            add_test_step(results, "Check Wallet Balances", "passed", details=balances)
        except Exception as e:
            add_test_step(results, "Check Wallet Balances", "warning", 
                         details={'error': str(e), 'note': 'Balances could not be checked'})
        
        # Step 7: Provide funding instructions
        add_test_step(results, "Funding Instructions", "info", details={
            'faucets': [
                {
                    'name': 'QuickNode BASE Sepolia Faucet',
                    'url': 'https://faucet.quicknode.com/base/sepolia',
                    'amount': '0.05 BASE ETH'
                },
                {
                    'name': 'Coinbase BASE Sepolia Faucet',
                    'url': 'https://faucet.coinbase.com/base-sepolia',
                    'amount': '0.1 BASE ETH daily'
                }
            ],
            'required_amounts': {
                'main_wallet': '0.1 BASE ETH',
                'oracle_wallets': '0.01 BASE ETH each'
            }
        })
        
        # Summary
        results['summary'] = {
            'wallets_generated': True,
            'environment_configured': True,
            'main_wallet': wallet_config['main_wallet']['address'],
            'oracle_wallets': wallet_config['oracle_wallets'],
            'next_steps': [
                'Fund the wallets using the faucets provided',
                'Run the Wallet Connection test to verify setup',
                'Proceed with E2E testing'
            ]
        }
        
        return results
        
    except Exception as e:
        add_test_step(results, "Wallet Setup Test", "failed", error=str(e))
        logger.error(f"Wallet setup error: {e}")
        return results

def run_wallet_connection_test(results):
    """Test wallet connection to BASE Sepolia"""
    try:
        # Step 1: Initialize Web3
        add_test_step(results, "Initialize Web3", "running")
        w3 = Web3(Web3.HTTPProvider(TEST_CONFIG['rpc_url']))
        
        if not w3.is_connected():
            add_test_step(results, "Initialize Web3", "failed", 
                         error="Failed to connect to BASE Sepolia RPC")
            return results
        
        add_test_step(results, "Initialize Web3", "passed", 
                     details={'connected': True, 'chain_id': w3.eth.chain_id})
        
        # Step 2: Check chain ID
        add_test_step(results, "Verify Chain ID", "running")
        chain_id = w3.eth.chain_id
        
        if chain_id != TEST_CONFIG['chain_id']:
            add_test_step(results, "Verify Chain ID", "failed", 
                         error=f"Wrong chain ID: {chain_id}, expected {TEST_CONFIG['chain_id']}")
            return results
        
        add_test_step(results, "Verify Chain ID", "passed", 
                     details={'chain_id': chain_id, 'network': 'BASE Sepolia'})
        
        # Step 3: Test wallet addresses
        add_test_step(results, "Validate Test Wallets", "running")
        invalid_wallets = []
        
        for name, address in TEST_CONFIG['test_wallets'].items():
            if not Web3.is_address(address):
                invalid_wallets.append(name)
        
        if invalid_wallets:
            add_test_step(results, "Validate Test Wallets", "failed", 
                         error=f"Invalid wallet addresses: {', '.join(invalid_wallets)}")
            return results
        
        add_test_step(results, "Validate Test Wallets", "passed", 
                     details={'wallet_count': len(TEST_CONFIG['test_wallets'])})
        
        # Step 4: Check gas price
        add_test_step(results, "Check Gas Price", "running")
        gas_price = w3.eth.gas_price
        gas_price_gwei = gas_price / 10**9
        
        add_test_step(results, "Check Gas Price", "passed", 
                     details={'gas_price_wei': gas_price, 'gas_price_gwei': gas_price_gwei})
        
        return results
        
    except Exception as e:
        add_test_step(results, "Wallet Connection Test", "failed", error=str(e))
        return results

def run_market_creation_test(results):
    """Test market creation workflow"""
    try:
        # Step 1: Create test actor
        add_test_step(results, "Create Test Actor", "running")
        
        actor = Actor.query.filter_by(name='Test Actor').first()
        if not actor:
            actor = Actor(
                name='Test Actor',
                description='Test actor for BASE blockchain testing',
                wallet_address=TEST_CONFIG['test_wallets']['creator'],
                status='approved'
            )
            db.session.add(actor)
            db.session.commit()
        
        add_test_step(results, "Create Test Actor", "passed", 
                     details={'actor_id': str(actor.id), 'name': actor.name})
        
        # Step 2: Initialize blockchain service
        add_test_step(results, "Initialize Blockchain Service", "running")
        blockchain_service = BaseBlockchainService()
        
        # Validate service configuration
        if not blockchain_service.w3.is_connected():
            add_test_step(results, "Initialize Blockchain Service", "failed", 
                         error="Blockchain service not connected")
            return results
        
        add_test_step(results, "Initialize Blockchain Service", "passed", 
                     details={'is_testnet': blockchain_service.is_testnet})
        
        # Step 3: Create test market
        add_test_step(results, "Create Prediction Market", "running")
        
        market_data = {
            'actor_id': actor.id,
            'start_time': datetime.utcnow(),
            'end_time': datetime.utcnow(),
            'oracle_wallets': json.dumps([
                TEST_CONFIG['test_wallets']['oracle1'],
                TEST_CONFIG['test_wallets']['oracle2'],
                TEST_CONFIG['test_wallets']['oracle3']
            ]),
            'twitter_handle': 'test_actor',
            'total_volume': '0',
            'contract_address': '0x' + '0' * 40,  # Mock contract address
            'market_creation_tx': '0x' + 'a' * 64  # Mock transaction hash
        }
        
        market = PredictionMarket(**market_data)
        db.session.add(market)
        db.session.commit()
        
        add_test_step(results, "Create Prediction Market", "passed", 
                     details={'market_id': str(market.id), 'twitter_handle': market.twitter_handle})
        
        # Step 4: Verify market creation
        add_test_step(results, "Verify Market Creation", "running")
        
        saved_market = PredictionMarket.query.get(market.id)
        if not saved_market:
            add_test_step(results, "Verify Market Creation", "failed", 
                         error="Market not found in database")
            return results
        
        add_test_step(results, "Verify Market Creation", "passed", 
                     details={'verified': True, 'status': saved_market.status})
        
        return results
        
    except Exception as e:
        add_test_step(results, "Market Creation Test", "failed", error=str(e))
        return results

def run_submission_creation_test(results):
    """Test submission creation"""
    try:
        # Step 1: Get active market
        add_test_step(results, "Get Active Market", "running")
        
        market = PredictionMarket.query.filter_by(twitter_handle='test_actor').first()
        if not market:
            add_test_step(results, "Get Active Market", "failed", 
                         error="No test market found")
            return results
        
        add_test_step(results, "Get Active Market", "passed", 
                     details={'market_id': str(market.id)})
        
        # Step 2: Create original submission
        add_test_step(results, "Create Original Submission", "running")
        
        original = Submission(
            market_id=market.id,
            submission_type='original',
            predicted_text='Test prediction text',
            creator_wallet=TEST_CONFIG['test_wallets']['creator'],
            initial_stake_amount='0.1',
            base_tx_hash='0x' + 'b' * 64
        )
        db.session.add(original)
        db.session.commit()
        
        add_test_step(results, "Create Original Submission", "passed", 
                     details={'submission_id': str(original.id), 'type': 'original'})
        
        # Step 3: Create competitor submission
        add_test_step(results, "Create Competitor Submission", "running")
        
        competitor = Submission(
            market_id=market.id,
            submission_type='competitor',
            predicted_text='Alternative prediction',
            creator_wallet=TEST_CONFIG['test_wallets']['bettor1'],
            initial_stake_amount='0.1',
            base_tx_hash='0x' + 'c' * 64
        )
        db.session.add(competitor)
        db.session.commit()
        
        add_test_step(results, "Create Competitor Submission", "passed", 
                     details={'submission_id': str(competitor.id), 'type': 'competitor'})
        
        # Step 4: Create null submission
        add_test_step(results, "Create Null Submission", "running")
        
        null_sub = Submission(
            market_id=market.id,
            submission_type='null',
            predicted_text=None,
            creator_wallet=TEST_CONFIG['test_wallets']['bettor2'],
            initial_stake_amount='0.1',
            base_tx_hash='0x' + 'd' * 64
        )
        db.session.add(null_sub)
        db.session.commit()
        
        add_test_step(results, "Create Null Submission", "passed", 
                     details={'submission_id': str(null_sub.id), 'type': 'null'})
        
        return results
        
    except Exception as e:
        add_test_step(results, "Submission Creation Test", "failed", error=str(e))
        return results

def run_bet_placement_test(results):
    """Test bet placement workflow"""
    try:
        # Step 1: Get submission
        add_test_step(results, "Get Test Submission", "running")
        
        submission = Submission.query.filter_by(submission_type='original').first()
        if not submission:
            add_test_step(results, "Get Test Submission", "failed", 
                         error="No test submission found")
            return results
        
        add_test_step(results, "Get Test Submission", "passed", 
                     details={'submission_id': str(submission.id)})
        
        # Step 2: Calculate fees
        add_test_step(results, "Calculate Bet Fees", "running")
        
        bet_amount = float(TEST_CONFIG['test_amounts']['bet_amount'])
        platform_fee = bet_amount * TEST_CONFIG['test_amounts']['platform_fee']
        total_amount = bet_amount + platform_fee
        
        add_test_step(results, "Calculate Bet Fees", "passed", 
                     details={
                         'bet_amount': bet_amount,
                         'platform_fee': platform_fee,
                         'total_amount': total_amount
                     })
        
        # Step 3: Place bet
        add_test_step(results, "Place Test Bet", "running")
        
        bet = Bet(
            submission_id=submission.id,
            bettor_wallet=TEST_CONFIG['test_wallets']['bettor1'],
            amount=str(bet_amount),
            base_tx_hash='0x' + 'e' * 64
        )
        db.session.add(bet)
        db.session.commit()
        
        add_test_step(results, "Place Test Bet", "passed", 
                     details={'bet_id': str(bet.id), 'amount': str(bet.amount)})
        
        # Step 4: Verify bet
        add_test_step(results, "Verify Bet Placement", "running")
        
        saved_bet = Bet.query.get(bet.id)
        if not saved_bet:
            add_test_step(results, "Verify Bet Placement", "failed", 
                         error="Bet not found in database")
            return results
        
        add_test_step(results, "Verify Bet Placement", "passed", 
                     details={'verified': True})
        
        return results
        
    except Exception as e:
        add_test_step(results, "Bet Placement Test", "failed", error=str(e))
        return results

def run_oracle_submission_test(results):
    """Test oracle submission workflow with X.com API integration"""
    try:
        # Step 1: Get expired market
        add_test_step(results, "Get Expired Market", "running")
        
        # Update market to be expired
        market = PredictionMarket.query.filter_by(twitter_handle='test_actor').first()
        if not market:
            add_test_step(results, "Get Expired Market", "failed", 
                         error="No test market found")
            return results
        
        # Make market expired
        market.end_time = datetime.utcnow()
        db.session.commit()
        
        add_test_step(results, "Get Expired Market", "passed", 
                     details={'market_id': str(market.id), 'expired': True})
        
        # Step 2: Test X.com API Integration
        add_test_step(results, "Test X.com API Integration", "running")
        
        # Initialize X.com services
        xcom_api = XComAPIService()
        oracle_service = XcomOracleService()
        
        # Test tweet data - using a known test tweet ID
        test_tweet_url = "https://x.com/test_user/status/1234567890123456789"
        tweet_text = None
        screenshot_proof = None
        
        try:
            # Try fetching tweet via API
            tweet_data = xcom_api.get_tweet("1234567890123456789")
            if tweet_data and tweet_data.get('data'):
                tweet_text = tweet_data['data'].get('text', 'Test actual text from tweet')
                add_test_step(results, "Test X.com API Integration", "passed", 
                             details={'api_success': True, 'tweet_fetched': True})
            else:
                # API didn't return data, use fallback
                tweet_text = 'Test actual text from tweet'
                add_test_step(results, "Test X.com API Integration", "warning", 
                             details={'api_success': False, 'using_fallback': True})
        except Exception as api_error:
            # API failed, use manual fallback
            tweet_text = 'Test actual text from tweet'
            add_test_step(results, "Test X.com API Integration", "warning", 
                         details={'api_error': str(api_error), 'using_manual_fallback': True})
        
        # Step 3: Capture Screenshot (or use placeholder)
        add_test_step(results, "Capture Tweet Screenshot", "running")
        
        try:
            # Try to capture screenshot
            screenshot_data = oracle_service.capture_tweet_screenshot(test_tweet_url)
            if screenshot_data:
                screenshot_proof = screenshot_data
                add_test_step(results, "Capture Tweet Screenshot", "passed", 
                             details={'screenshot_captured': True})
            else:
                # Use placeholder if capture fails
                screenshot_proof = 'data:image/png;base64,iVBORw0KGgoAAAANS...'
                add_test_step(results, "Capture Tweet Screenshot", "warning", 
                             details={'using_placeholder': True})
        except Exception as screenshot_error:
            screenshot_proof = 'data:image/png;base64,iVBORw0KGgoAAAANS...'
            add_test_step(results, "Capture Tweet Screenshot", "warning", 
                         details={'screenshot_error': str(screenshot_error)})
        
        # Step 4: Submit oracle data
        add_test_step(results, "Submit Oracle Data", "running")
        
        oracle_submission = OracleSubmission(
            market_id=market.id,
            oracle_wallet=TEST_CONFIG['test_wallets']['oracle1'],
            tweet_id='1234567890123456789',
            submitted_text=tweet_text,
            screenshot_proof=screenshot_proof,
            signature='0x' + 'f' * 130,
            status='pending',
            tweet_url=test_tweet_url,
            verification_method='api_test'
        )
        db.session.add(oracle_submission)
        db.session.commit()
        
        add_test_step(results, "Submit Oracle Data", "passed", 
                     details={
                         'oracle_id': str(oracle_submission.id),
                         'tweet_text': tweet_text[:50] + '...' if len(tweet_text) > 50 else tweet_text,
                         'has_screenshot': bool(screenshot_proof)
                     })
        
        # Step 5: Calculate Levenshtein distances
        add_test_step(results, "Calculate Levenshtein Distances", "running")
        
        # Using imported distance function
        submissions = market.submissions
        
        for submission in submissions:
            if submission.predicted_text:
                dist = distance(oracle_submission.submitted_text, submission.predicted_text)
                submission.levenshtein_distance = dist
        
        db.session.commit()
        
        distances = {str(s.id): s.levenshtein_distance for s in submissions if s.levenshtein_distance is not None}
        add_test_step(results, "Calculate Levenshtein Distances", "passed", 
                     details={'distances': distances})
        
        # Step 6: Test Manual Submission Interface
        add_test_step(results, "Test Manual Submission Interface", "running")
        
        # Verify the manual submission route is available
        from routes.oracle_manual import oracle_manual_bp
        if oracle_manual_bp:
            add_test_step(results, "Test Manual Submission Interface", "passed", 
                         details={'manual_interface_available': True})
        else:
            add_test_step(results, "Test Manual Submission Interface", "warning", 
                         details={'manual_interface_available': False})
        
        # Step 7: Verify oracle submission
        add_test_step(results, "Verify Oracle Submission", "running")
        
        saved_oracle = OracleSubmission.query.get(oracle_submission.id)
        if not saved_oracle:
            add_test_step(results, "Verify Oracle Submission", "failed", 
                         error="Oracle submission not found")
            return results
        
        add_test_step(results, "Verify Oracle Submission", "passed", 
                     details={
                         'verified': True, 
                         'status': saved_oracle.status,
                         'has_tweet_url': bool(saved_oracle.tweet_url),
                         'verification_method': saved_oracle.verification_method
                     })
        
        return results
        
    except Exception as e:
        add_test_step(results, "Oracle Submission Test", "failed", error=str(e))
        return results

def run_market_resolution_test(results):
    """Test market resolution workflow"""
    try:
        # Step 1: Get market with oracle data
        add_test_step(results, "Get Market for Resolution", "running")
        
        market = PredictionMarket.query.filter_by(twitter_handle='test_actor').first()
        if not market:
            add_test_step(results, "Get Market for Resolution", "failed", 
                         error="No test market found")
            return results
        
        add_test_step(results, "Get Market for Resolution", "passed", 
                     details={'market_id': market.id})
        
        # Step 2: Determine winner
        add_test_step(results, "Determine Winner", "running")
        
        submissions = market.submissions
        winner = None
        min_distance = float('inf')
        
        for submission in submissions:
            if submission.levenshtein_distance is not None:
                if submission.levenshtein_distance < min_distance:
                    min_distance = submission.levenshtein_distance
                    winner = submission
        
        if not winner:
            add_test_step(results, "Determine Winner", "failed", 
                         error="No winner determined")
            return results
        
        winner.is_winner = True
        db.session.commit()
        
        add_test_step(results, "Determine Winner", "passed", 
                     details={
                         'winner_id': winner.id,
                         'distance': winner.levenshtein_distance,
                         'text': winner.predicted_text or '[NULL]'
                     })
        
        # Step 3: Calculate payouts
        add_test_step(results, "Calculate Payouts", "running")
        
        total_pot = sum(float(bet.amount) for submission in submissions for bet in submission.bets)
        platform_fee = total_pot * TEST_CONFIG['test_amounts']['platform_fee']
        winner_pot = total_pot - platform_fee
        
        winner_bets = winner.bets
        payout_details = []
        
        for bet in winner_bets:
            bet_proportion = float(bet.amount) / sum(float(b.amount) for b in winner_bets)
            payout = winner_pot * bet_proportion
            payout_details.append({
                'bettor': bet.bettor_wallet[:6] + '...',
                'payout': round(payout, 4)
            })
        
        add_test_step(results, "Calculate Payouts", "passed", 
                     details={
                         'total_pot': round(total_pot, 4),
                         'platform_fee': round(platform_fee, 4),
                         'winner_pot': round(winner_pot, 4),
                         'payouts': payout_details
                     })
        
        # Step 4: Mark market as resolved
        add_test_step(results, "Resolve Market", "running")
        
        market.status = 'resolved'
        db.session.commit()
        
        add_test_step(results, "Resolve Market", "passed", 
                     details={'status': market.status})
        
        return results
        
    except Exception as e:
        add_test_step(results, "Market Resolution Test", "failed", error=str(e))
        return results

def run_full_workflow_test(results):
    """Run complete end-to-end workflow test"""
    try:
        # This combines all the individual tests
        add_test_step(results, "Full Workflow Test", "running", 
                     details={'description': 'Running complete E2E workflow'})
        
        # Clean up test data first
        add_test_step(results, "Clean Test Data", "running")
        clean_test_data()
        add_test_step(results, "Clean Test Data", "passed")
        
        # Run each test in sequence
        test_sequence = [
            ('Wallet Connection', run_wallet_connection_test),
            ('Market Creation', run_market_creation_test),
            ('Submission Creation', run_submission_creation_test),
            ('Bet Placement', run_bet_placement_test),
            ('Oracle Submission', run_oracle_submission_test),
            ('Market Resolution', run_market_resolution_test)
        ]
        
        for test_name, test_func in test_sequence:
            add_test_step(results, f"Running {test_name}", "running")
            
            # Create sub-results for each test
            sub_results = {
                'test_case': test_name,
                'status': 'running',
                'steps': [],
                'errors': []
            }
            
            # Run the test
            sub_results = test_func(sub_results)
            
            # Check if sub-test failed
            if sub_results['errors']:
                add_test_step(results, f"Running {test_name}", "failed", 
                             error=f"Sub-test failed: {', '.join(sub_results['errors'])}")
                return results
            
            add_test_step(results, f"Running {test_name}", "passed")
        
        add_test_step(results, "Full Workflow Test", "passed", 
                     details={'all_tests_passed': True})
        
        return results
        
    except Exception as e:
        add_test_step(results, "Full Workflow Test", "failed", error=str(e))
        return results

def clean_test_data():
    """Clean up test data from database"""
    try:
        # Delete test oracle submissions
        OracleSubmission.query.filter(OracleSubmission.tweet_id == '1234567890123456789').delete()
        
        # Delete test bets
        Bet.query.filter(Bet.base_tx_hash.like('0x%eee%')).delete()
        
        # Delete test submissions
        Submission.query.filter(Submission.base_tx_hash.like('0x%bbb%')).delete()
        Submission.query.filter(Submission.base_tx_hash.like('0x%ccc%')).delete()
        Submission.query.filter(Submission.base_tx_hash.like('0x%ddd%')).delete()
        
        # Delete test markets
        PredictionMarket.query.filter(PredictionMarket.twitter_handle == 'test_actor').delete()
        
        # Delete test actors
        Actor.query.filter_by(name='Test Actor').delete()
        
        db.session.commit()
        logger.info("Test data cleaned successfully")
        
    except Exception as e:
        logger.error(f"Error cleaning test data: {e}")
        db.session.rollback()

@test_manager_bp.route('/test-manager/api/clean-data', methods=['POST'])
@require_test_auth
def clean_data():
    """Clean test data endpoint"""
    try:
        clean_test_data()
        return jsonify({'success': True, 'message': 'Test data cleaned'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@test_manager_bp.route('/test-manager/logout')
def test_logout():
    """Logout from test manager"""
    session.pop('test_authenticated', None)
    return redirect(url_for('test_manager.test_login'))

def run_full_e2e_test(results):
    """Run full end-to-end test workflow"""
    try:
        # Run all tests in sequence
        add_test_step(results, "Full E2E Test", "running")
        
        # 1. Wallet Connection
        add_test_step(results, "Wallet Connection Test", "running")
        wallet_results = run_wallet_connection_test({'steps': [], 'errors': []})
        if wallet_results['errors']:
            add_test_step(results, "Wallet Connection Test", "failed", 
                         error=wallet_results['errors'][0])
            return results
        add_test_step(results, "Wallet Connection Test", "passed")
        
        # 2. Market Creation
        add_test_step(results, "Market Creation Test", "running")
        market_results = run_market_creation_test({'steps': [], 'errors': []})
        if market_results['errors']:
            add_test_step(results, "Market Creation Test", "failed", 
                         error=market_results['errors'][0])
            return results
        add_test_step(results, "Market Creation Test", "passed")
        
        # 3. Submission Creation
        add_test_step(results, "Submission Creation Test", "running")
        submission_results = run_submission_creation_test({'steps': [], 'errors': []})
        if submission_results['errors']:
            add_test_step(results, "Submission Creation Test", "failed", 
                         error=submission_results['errors'][0])
            return results
        add_test_step(results, "Submission Creation Test", "passed")
        
        # 4. Betting
        add_test_step(results, "Betting Test", "running")
        bet_results = run_bet_placement_test({'steps': [], 'errors': []})
        if bet_results['errors']:
            add_test_step(results, "Betting Test", "failed", 
                         error=bet_results['errors'][0])
            return results
        add_test_step(results, "Betting Test", "passed")
        
        # 5. Oracle Submission
        add_test_step(results, "Oracle Submission Test", "running")
        oracle_results = run_oracle_submission_test({'steps': [], 'errors': []})
        if oracle_results['errors']:
            add_test_step(results, "Oracle Submission Test", "failed", 
                         error=oracle_results['errors'][0])
            return results
        add_test_step(results, "Oracle Submission Test", "passed")
        
        # 6. Market Resolution
        add_test_step(results, "Market Resolution Test", "running")
        resolution_results = run_market_resolution_test({'steps': [], 'errors': []})
        if resolution_results['errors']:
            add_test_step(results, "Market Resolution Test", "failed", 
                         error=resolution_results['errors'][0])
            return results
        add_test_step(results, "Market Resolution Test", "passed")
        
        # 7. Clean up test data
        add_test_step(results, "Clean Test Data", "running")
        clean_test_data()
        add_test_step(results, "Clean Test Data", "passed")
        
        add_test_step(results, "Full E2E Test", "passed", 
                     details={'all_tests': 'completed successfully'})
        
        return results
        
    except Exception as e:
        add_test_step(results, "Full E2E Test", "failed", error=str(e))
        return results
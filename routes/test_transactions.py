"""
Test Transaction Generator for Clockchain
Allows admins to create and manage real test transactions through the entire lifecycle
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from models import *
from app import db
from datetime import datetime, timedelta
from decimal import Decimal
import json
import uuid
import logging
from services.blockchain import BlockchainService
from services.ledger import LedgerService
from services.oracle import OracleService
from services.time_sync import TimeSyncService
from utils.crypto import CryptoUtils
import os

logger = logging.getLogger(__name__)

test_transactions_bp = Blueprint('test_transactions', __name__)

# Initialize services
blockchain_service = BlockchainService()
ledger_service = LedgerService()
oracle_service = OracleService()
time_sync_service = TimeSyncService()
crypto_utils = CryptoUtils()

# Test scenarios
TEST_SCENARIOS = [
    {
        'id': 'elon_tweet_abc',
        'actor': 'Elon Musk',
        'description': 'Elon tweets "abc 123 xyz" within the next hour',
        'window_minutes': 10,
        'oracle_count': 3,
        'initial_stake': '0.001',
        'competitor_stakes': ['0.0008', '0.0012', '0.0009'],
        'bet_amounts': ['0.0002', '0.0003', '0.0001', '0.0004'],
        'predicted_texts': [
            'abc 123 xyz',
            'ABC 123 XYZ',
            'abc123xyz',
            'abc one two three xyz'
        ]
    },
    {
        'id': 'trump_truth_social',
        'actor': 'Donald Trump',
        'description': 'Trump posts about the economy on Truth Social',
        'window_minutes': 10,
        'oracle_count': 3,
        'initial_stake': '0.0015',
        'competitor_stakes': ['0.001', '0.002'],
        'bet_amounts': ['0.0005', '0.0003', '0.0007'],
        'predicted_texts': [
            'The economy is doing GREAT!',
            'Economy is the best it has ever been',
            'Stock market hits new record high'
        ]
    },
    {
        'id': 'taylor_swift_album',
        'actor': 'Taylor Swift',
        'description': 'Taylor announces new album release date',
        'window_minutes': 15,
        'oracle_count': 3,
        'initial_stake': '0.002',
        'competitor_stakes': ['0.0015', '0.0025', '0.0018'],
        'bet_amounts': ['0.0008', '0.0006', '0.0009', '0.0005'],
        'predicted_texts': [
            'New album coming April 2025!',
            'Album drops next month',
            'Surprise! New music tomorrow',
            'The next era begins soon'
        ]
    }
]

class TestTransactionManager:
    """Manages the lifecycle of test transactions"""
    
    def __init__(self):
        self.active_tests = {}  # scenario_id -> test_state
        
    def create_test_session(self, scenario_id, mock_mode=True):
        """Initialize a new test session"""
        scenario = next((s for s in TEST_SCENARIOS if s['id'] == scenario_id), None)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")
            
        session_id = str(uuid.uuid4())
        self.active_tests[session_id] = {
            'scenario': scenario,
            'mock_mode': mock_mode,
            'state': 'initialized',
            'created_at': datetime.utcnow(),
            'transactions': [],
            'market': None,
            'submissions': [],
            'bets': [],
            'oracle_results': [],
            'errors': []
        }
        
        return session_id
        
    def get_session(self, session_id):
        """Get test session details"""
        return self.active_tests.get(session_id)
        
    def update_session_state(self, session_id, new_state, data=None):
        """Update session state"""
        if session_id in self.active_tests:
            self.active_tests[session_id]['state'] = new_state
            if data:
                self.active_tests[session_id].update(data)
                
    def mock_transaction(self, tx_type, tx_data):
        """Simulate a transaction without blockchain interaction"""
        return {
            'hash': f"0x{''.join([str(uuid.uuid4()).replace('-', '') for _ in range(2)])}",
            'type': tx_type,
            'data': tx_data,
            'status': 'mocked',
            'gas_used': 21000,
            'timestamp': datetime.utcnow().isoformat()
        }

# Global manager instance
test_manager = TestTransactionManager()

@test_transactions_bp.route('/')
def dashboard():
    """Test transaction dashboard"""
    active_sessions = []
    for session_id, session in test_manager.active_tests.items():
        active_sessions.append({
            'id': session_id,
            'scenario': session['scenario'],
            'state': session['state'],
            'mock_mode': session['mock_mode'],
            'created_at': session['created_at'],
            'errors': len(session['errors'])
        })
    
    # Check for test wallet configuration
    has_test_wallets = all([
        os.environ.get('TEST_WALLET_ADDRESS'),
        os.environ.get('TEST_WALLET_PRIVATE_KEY'),
        os.environ.get('TEST_ORACLE_WALLETS')
    ])
    
    return render_template('test_transactions/dashboard.html',
                         scenarios=TEST_SCENARIOS,
                         active_sessions=active_sessions,
                         has_test_wallets=has_test_wallets)

@test_transactions_bp.route('/create_session', methods=['POST'])
def create_session():
    """Create a new test session"""
    try:
        scenario_id = request.form.get('scenario_id')
        mock_mode = request.form.get('mock_mode', 'true') == 'true'
        
        session_id = test_manager.create_test_session(scenario_id, mock_mode)
        
        flash(f'Test session created: {session_id[:8]}...', 'success')
        return redirect(url_for('test_transactions.session_detail', session_id=session_id))
        
    except Exception as e:
        logger.error(f"Error creating test session: {e}")
        flash(f'Error creating session: {str(e)}', 'error')
        return redirect(url_for('test_transactions.dashboard'))

@test_transactions_bp.route('/session/<session_id>')
def session_detail(session_id):
    """View test session details"""
    session = test_manager.get_session(session_id)
    if not session:
        flash('Session not found', 'error')
        return redirect(url_for('test_transactions.dashboard'))
    
    # Calculate time until market starts/ends
    if session['market']:
        now = datetime.utcnow()
        market = session['market']
        time_to_start = (market.start_time - now).total_seconds() if market.start_time > now else 0
        time_to_end = (market.end_time - now).total_seconds() if market.end_time > now else 0
    else:
        time_to_start = None
        time_to_end = None
    
    return render_template('test_transactions/session_detail.html',
                         session_id=session_id,
                         session=session,
                         time_to_start=time_to_start,
                         time_to_end=time_to_end)

@test_transactions_bp.route('/session/<session_id>/create_market', methods=['POST'])
def create_market(session_id):
    """Step 1: Create prediction market"""
    try:
        session = test_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
            
        if session['state'] != 'initialized':
            return jsonify({'error': f"Cannot create market in state: {session['state']}"}), 400
            
        scenario = session['scenario']
        
        # Get or create actor
        actor = Actor.query.filter_by(name=scenario['actor']).first()
        if not actor:
            actor = Actor()
            actor.name = scenario['actor']
            actor.description = f"Test actor for {scenario['actor']}"
            actor.wallet_address = os.environ.get('TEST_WALLET_ADDRESS', '0x' + '0' * 40)
            actor.status = 'approved'
            db.session.add(actor)
            db.session.commit()
        
        # Create market
        start_time = datetime.utcnow() + timedelta(minutes=1)
        end_time = start_time + timedelta(minutes=scenario['window_minutes'])
        
        # Get test oracle wallets
        oracle_wallets = json.loads(os.environ.get('TEST_ORACLE_WALLETS', '[]'))
        if not oracle_wallets:
            oracle_wallets = [f"0x{str(i) * 40}" for i in range(3)]
        
        market = PredictionMarket()
        market.actor_id = actor.id
        market.start_time = start_time
        market.end_time = end_time
        market.oracle_wallets = json.dumps(oracle_wallets[:scenario['oracle_count']])
        market.status = 'active'
        db.session.add(market)
        db.session.commit()
        
        # Create transaction record
        if session['mock_mode']:
            tx = test_manager.mock_transaction('market_creation', {
                'market_id': str(market.id),
                'actor': scenario['actor']
            })
        else:
            # Real blockchain transaction would go here
            tx = {'hash': '0x' + '0' * 64, 'status': 'pending'}
        
        session['transactions'].append(tx)
        session['market'] = market
        test_manager.update_session_state(session_id, 'market_created', {
            'market_id': str(market.id)
        })
        
        return jsonify({
            'success': True,
            'market_id': str(market.id),
            'transaction': tx
        })
        
    except Exception as e:
        logger.error(f"Error creating market: {e}")
        session['errors'].append(str(e))
        return jsonify({'error': str(e)}), 500

@test_transactions_bp.route('/session/<session_id>/create_submissions', methods=['POST'])
def create_submissions(session_id):
    """Step 2: Create initial and competitor submissions"""
    try:
        session = test_manager.get_session(session_id)
        if not session or session['state'] != 'market_created':
            return jsonify({'error': 'Invalid session state'}), 400
            
        scenario = session['scenario']
        market = PredictionMarket.query.get(session['market_id'])
        
        submissions = []
        
        # Create initial submission
        initial_submission = Submission()
        initial_submission.market_id = market.id
        initial_submission.creator_wallet = os.environ.get('TEST_WALLET_ADDRESS', '0x' + '1' * 40)
        initial_submission.predicted_text = scenario['predicted_texts'][0]
        initial_submission.submission_type = 'original'
        initial_submission.initial_stake_amount = Decimal(scenario['initial_stake'])
        initial_submission.currency = 'ETH'
        initial_submission.transaction_hash = '0x' + uuid.uuid4().hex if session['mock_mode'] else ''
        initial_submission.is_ai_agent = False
        db.session.add(initial_submission)
        submissions.append(initial_submission)
        
        # Create competitor submissions
        for i, (stake, text) in enumerate(zip(scenario['competitor_stakes'], scenario['predicted_texts'][1:])):
            competitor = Submission()
            competitor.market_id = market.id
            competitor.creator_wallet = f"0x{str(i+2) * 40}"
            competitor.predicted_text = text
            competitor.submission_type = 'competitor'
            competitor.initial_stake_amount = Decimal(stake)
            competitor.currency = 'ETH'
            competitor.transaction_hash = '0x' + uuid.uuid4().hex if session['mock_mode'] else ''
            competitor.is_ai_agent = i % 2 == 0  # Make some AI agents
            competitor.ai_agent_id = f"test_ai_agent_{i}" if i % 2 == 0 else None
            db.session.add(competitor)
            submissions.append(competitor)
        
        db.session.commit()
        
        # Record transactions
        for sub in submissions:
            if session['mock_mode']:
                tx = test_manager.mock_transaction('submission', {
                    'submission_id': str(sub.id),
                    'text': sub.predicted_text[:50] + '...',
                    'stake': str(sub.initial_stake_amount)
                })
            else:
                tx = {'hash': sub.transaction_hash, 'status': 'pending'}
            session['transactions'].append(tx)
        
        session['submissions'] = [str(s.id) for s in submissions]
        test_manager.update_session_state(session_id, 'submissions_created')
        
        return jsonify({
            'success': True,
            'submissions': len(submissions),
            'transactions': session['transactions'][-len(submissions):]
        })
        
    except Exception as e:
        logger.error(f"Error creating submissions: {e}")
        session['errors'].append(str(e))
        return jsonify({'error': str(e)}), 500

@test_transactions_bp.route('/session/<session_id>/create_bets', methods=['POST'])
def create_bets(session_id):
    """Step 3: Create bets on submissions"""
    try:
        session = test_manager.get_session(session_id)
        if not session or session['state'] != 'submissions_created':
            return jsonify({'error': 'Invalid session state'}), 400
            
        scenario = session['scenario']
        submissions = Submission.query.filter(
            Submission.id.in_([uuid.UUID(sid) for sid in session['submissions']])
        ).all()
        
        bets = []
        bet_wallets = [f"0x{str(i+10) * 40}" for i in range(len(scenario['bet_amounts']))]
        
        # Distribute bets across submissions
        for i, (amount, wallet) in enumerate(zip(scenario['bet_amounts'], bet_wallets)):
            submission = submissions[i % len(submissions)]
            bet = Bet()
            bet.submission_id = submission.id
            bet.bettor_wallet = wallet
            bet.amount = Decimal(amount)
            bet.currency = 'ETH'
            bet.transaction_hash = '0x' + uuid.uuid4().hex if session['mock_mode'] else ''
            db.session.add(bet)
            bets.append(bet)
        
        db.session.commit()
        
        # Record transactions
        for bet in bets:
            if session['mock_mode']:
                tx = test_manager.mock_transaction('bet', {
                    'bet_id': str(bet.id),
                    'amount': str(bet.amount),
                    'submission': str(bet.submission_id)
                })
            else:
                tx = {'hash': bet.transaction_hash, 'status': 'pending'}
            session['transactions'].append(tx)
        
        session['bets'] = [str(b.id) for b in bets]
        test_manager.update_session_state(session_id, 'bets_created')
        
        return jsonify({
            'success': True,
            'bets': len(bets),
            'total_bet_amount': str(sum(b.amount for b in bets))
        })
        
    except Exception as e:
        logger.error(f"Error creating bets: {e}")
        session['errors'].append(str(e))
        return jsonify({'error': str(e)}), 500

@test_transactions_bp.route('/session/<session_id>/wait_for_market_end', methods=['POST'])
def wait_for_market_end(session_id):
    """Step 4: Wait for market to end (or simulate time passing)"""
    try:
        session = test_manager.get_session(session_id)
        if not session or session['state'] != 'bets_created':
            return jsonify({'error': 'Invalid session state'}), 400
            
        market = PredictionMarket.query.get(session['market_id'])
        
        # In test mode, we can fast-forward the market
        if request.form.get('fast_forward') == 'true':
            market.end_time = datetime.utcnow() - timedelta(minutes=1)
            market.status = 'expired'
            db.session.commit()
            
        # Check if market has ended
        if datetime.utcnow() > market.end_time:
            test_manager.update_session_state(session_id, 'market_ended')
            return jsonify({
                'success': True,
                'market_ended': True
            })
        else:
            time_remaining = (market.end_time - datetime.utcnow()).total_seconds()
            return jsonify({
                'success': True,
                'market_ended': False,
                'time_remaining': time_remaining
            })
            
    except Exception as e:
        logger.error(f"Error checking market status: {e}")
        return jsonify({'error': str(e)}), 500

@test_transactions_bp.route('/session/<session_id>/submit_oracle_results', methods=['POST'])
def submit_oracle_results(session_id):
    """Step 5: Submit oracle results"""
    try:
        session = test_manager.get_session(session_id)
        if not session or session['state'] != 'market_ended':
            return jsonify({'error': 'Invalid session state'}), 400
            
        market = PredictionMarket.query.get(session['market_id'])
        oracle_wallets = json.loads(market.oracle_wallets)
        
        # Simulate oracle consensus on the winning text
        winning_text = session['scenario']['predicted_texts'][0]  # First text wins
        
        oracle_submissions = []
        for oracle_wallet in oracle_wallets:
            oracle_sub = OracleSubmission()
            oracle_sub.market_id = market.id
            oracle_sub.oracle_wallet = oracle_wallet
            oracle_sub.submitted_text = winning_text
            oracle_sub.is_consensus = True
            db.session.add(oracle_sub)
            oracle_submissions.append(oracle_sub)
        
        # Update market status
        market.status = 'validating'
        market.resolution_text = winning_text
        
        db.session.commit()
        
        # Record oracle transactions
        for oracle_sub in oracle_submissions:
            if session['mock_mode']:
                tx = test_manager.mock_transaction('oracle_submission', {
                    'oracle': oracle_sub.oracle_wallet[:10] + '...',
                    'text': winning_text[:30] + '...'
                })
            else:
                tx = {'hash': '0x' + uuid.uuid4().hex, 'status': 'pending'}
            session['transactions'].append(tx)
        
        session['oracle_results'] = [str(o.id) for o in oracle_submissions]
        test_manager.update_session_state(session_id, 'oracles_submitted')
        
        return jsonify({
            'success': True,
            'oracle_count': len(oracle_submissions),
            'consensus_text': winning_text
        })
        
    except Exception as e:
        logger.error(f"Error submitting oracle results: {e}")
        session['errors'].append(str(e))
        return jsonify({'error': str(e)}), 500

@test_transactions_bp.route('/session/<session_id>/resolve_market', methods=['POST'])
def resolve_market(session_id):
    """Step 6: Resolve market and distribute rewards"""
    try:
        session = test_manager.get_session(session_id)
        if not session or session['state'] != 'oracles_submitted':
            return jsonify({'error': 'Invalid session state'}), 400
            
        market = PredictionMarket.query.get(session['market_id'])
        submissions = Submission.query.filter_by(market_id=market.id).all()
        
        # Calculate Levenshtein distances
        from Levenshtein import distance
        for submission in submissions:
            submission.levenshtein_distance = distance(submission.predicted_text, market.resolution_text)
        
        # Find winner (lowest distance)
        winner = min(submissions, key=lambda s: s.levenshtein_distance)
        winner.is_winner = True
        market.winning_submission_id = winner.id
        market.status = 'resolved'
        market.resolution_time = datetime.utcnow()
        
        # Calculate rewards
        total_pool = sum(s.initial_stake_amount for s in submissions)
        total_bets = sum(b.amount for s in submissions for b in s.bets)
        
        # Create payout transactions
        payouts = []
        
        # Winner gets their stake back plus pool
        winner_payout = winner.initial_stake_amount + (total_pool - winner.initial_stake_amount) * Decimal('0.9')
        payouts.append({
            'to': winner.creator_wallet,
            'amount': winner_payout,
            'type': 'winner_payout'
        })
        
        # Bet payouts
        for bet in winner.bets:
            bet_payout = bet.amount * Decimal('1.8')  # 80% return
            payouts.append({
                'to': bet.bettor_wallet,
                'amount': bet_payout,
                'type': 'bet_payout'
            })
        
        db.session.commit()
        
        # Record payout transactions
        for payout in payouts:
            if session['mock_mode']:
                tx = test_manager.mock_transaction('payout', payout)
            else:
                tx = {'hash': '0x' + uuid.uuid4().hex, 'status': 'pending'}
            session['transactions'].append(tx)
        
        test_manager.update_session_state(session_id, 'resolved', {
            'winner_id': str(winner.id),
            'total_payouts': str(sum(p['amount'] for p in payouts))
        })
        
        return jsonify({
            'success': True,
            'winner': {
                'id': str(winner.id),
                'text': winner.predicted_text,
                'distance': winner.levenshtein_distance
            },
            'payouts': len(payouts),
            'total_amount': str(sum(p['amount'] for p in payouts))
        })
        
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        session['errors'].append(str(e))
        return jsonify({'error': str(e)}), 500

@test_transactions_bp.route('/session/<session_id>/reconcile', methods=['POST'])
def reconcile_ledger(session_id):
    """Step 7: Reconcile on ledger"""
    try:
        session = test_manager.get_session(session_id)
        if not session or session['state'] != 'resolved':
            return jsonify({'error': 'Invalid session state'}), 400
            
        # Perform ledger reconciliation
        if not session['mock_mode']:
            # Real ledger reconciliation would happen here
            # TODO: Implement ledger_service.reconcile_market_resolution(session['market_id'])
            logger.info(f"Ledger reconciliation for market {session['market_id']} would happen here")
        
        # Create final transaction record
        if session['mock_mode']:
            tx = test_manager.mock_transaction('reconciliation', {
                'market_id': session['market_id'],
                'entries': len(session['transactions'])
            })
        else:
            tx = {'hash': '0x' + uuid.uuid4().hex, 'status': 'confirmed'}
        
        session['transactions'].append(tx)
        test_manager.update_session_state(session_id, 'completed')
        
        return jsonify({
            'success': True,
            'reconciled': True,
            'total_transactions': len(session['transactions'])
        })
        
    except Exception as e:
        logger.error(f"Error reconciling ledger: {e}")
        session['errors'].append(str(e))
        return jsonify({'error': str(e)}), 500

@test_transactions_bp.route('/configure_wallets')
def configure_wallets():
    """Configure test wallets"""
    return render_template('test_transactions/configure_wallets.html')
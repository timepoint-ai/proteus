"""
Test Data Generation with Proper Status Workflow
Following the STATUS_WORKFLOW.md specification
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import *
from app import db
from datetime import datetime, timedelta
import random
import uuid
from decimal import Decimal
# Phase 1: Bet resolution service deprecated - handled by DecentralizedOracle contract
# from services.bet_resolution import MarketResolutionService
import logging

logger = logging.getLogger(__name__)
test_data_v2_bp = Blueprint('test_data_v2', __name__)
# Phase 1: Resolution service deprecated
# resolution_service = MarketResolutionService()

@test_data_v2_bp.route('/')
def index():
    """Display test data generation options"""
    return '''
    <html>
    <head><title>Test Data V2</title></head>
    <body>
        <h1>Generate Test Data with Proper Status Workflow</h1>
        <form method="POST" action="/test_data_v2/generate_proper_workflow">
            <button type="submit">Generate Test Data</button>
        </form>
    </body>
    </html>
    '''

@test_data_v2_bp.route('/generate_proper_workflow', methods=['GET', 'POST'])
def generate_proper_workflow():
    """Generate test data following proper status workflow"""
    try:
        # Clear existing data
        db.session.query(Transaction).delete()
        db.session.query(Bet).delete()
        db.session.query(OracleSubmission).delete()
        db.session.query(Submission).delete()
        db.session.query(PredictionMarket).delete()
        db.session.query(Actor).delete()
        db.session.query(NodeOperator).delete()
        db.session.commit()
        
        # Create node operators
        nodes = []
        for i in range(3):
            node = NodeOperator()
            node.operator_id = f"node_{i+1}"
            node.public_key = f"public_key_{uuid.uuid4().hex[:16]}"
            node.node_address = f"http://node{i+1}.clockchain.network"
            node.status = 'active'
            db.session.add(node)
            nodes.append(node)
        
        # Create actors
        actors = []
        actor_names = ["Elon Musk", "Taylor Swift", "Joe Biden", "Oprah Winfrey", "Bill Gates"]
        for name in actor_names:
            actor = Actor()
            actor.name = name
            actor.description = f"Public figure - {name}"
            actor.wallet_address = f"0x{uuid.uuid4().hex[:40]}"
            actor.status = 'approved'
            actor.approval_votes = random.randint(10, 20)
            db.session.add(actor)
            actors.append(actor)
        
        db.session.commit()
        
        # Create bets with different statuses
        current_time = datetime.utcnow()
        
        # 1. ACTIVE BETS (3)
        for i in range(3):
            bet = Bet()
            bet.creator_wallet = f"0x{uuid.uuid4().hex[:40]}"
            bet.actor_id = random.choice(actors).id
            bet.predicted_text = f"I believe that blockchain technology will {random.choice(['transform', 'revolutionize', 'change'])} the {random.choice(['financial', 'healthcare', 'education'])} industry"
            bet.start_time = current_time - timedelta(hours=random.randint(1, 10))
            bet.end_time = current_time + timedelta(hours=random.randint(12, 48))
            bet.oracle_wallets = '["' + '","'.join([f"0x{uuid.uuid4().hex[:40]}" for _ in range(3)]) + '"]'
            bet.initial_stake_amount = Decimal(str(random.uniform(0.1, 2.0)))
            bet.currency = random.choice(['ETH', 'BTC'])
            bet.transaction_hash = f"0x{uuid.uuid4().hex[:64]}"
            bet.status = 'active'
            db.session.add(bet)
            db.session.flush()  # Flush to get the bet ID
            
            # Add initial stake transaction
            init_tx = Transaction()
            init_tx.transaction_hash = bet.transaction_hash
            init_tx.from_address = bet.creator_wallet
            init_tx.to_address = "platform_pool"
            init_tx.amount = bet.initial_stake_amount
            init_tx.currency = bet.currency
            init_tx.transaction_type = 'stake'
            init_tx.related_bet_id = bet.id
            init_tx.status = 'confirmed'
            db.session.add(init_tx)
            
            # Add some confirmed stakes
            for j in range(random.randint(2, 5)):
                stake = Stake()
                stake.bet_id = bet.id
                stake.staker_wallet = f"0x{uuid.uuid4().hex[:40]}"
                stake.amount = Decimal(str(random.uniform(0.05, 0.5)))
                stake.currency = bet.currency
                stake.transaction_hash = f"0x{uuid.uuid4().hex[:64]}"
                stake.position = random.choice(['for', 'against'])
                stake.status = 'confirmed'
                db.session.add(stake)
                
                # Add stake transaction
                stake_tx = Transaction()
                stake_tx.transaction_hash = stake.transaction_hash
                stake_tx.from_address = stake.staker_wallet
                stake_tx.to_address = "platform_pool"
                stake_tx.amount = stake.amount
                stake_tx.currency = stake.currency
                stake_tx.transaction_type = 'stake'
                stake_tx.related_bet_id = bet.id
                stake_tx.status = 'confirmed'
                db.session.add(stake_tx)
        
        # 2. EXPIRED BETS (2) - Awaiting oracle
        for i in range(2):
            bet = Bet()
            bet.creator_wallet = f"0x{uuid.uuid4().hex[:40]}"
            bet.actor_id = random.choice(actors).id
            bet.predicted_text = f"We will see {random.choice(['significant', 'major', 'unprecedented'])} changes in {random.choice(['AI regulation', 'climate policy', 'space exploration'])}"
            bet.start_time = current_time - timedelta(hours=48)
            bet.end_time = current_time - timedelta(hours=random.randint(1, 6))
            bet.oracle_wallets = '["' + '","'.join([f"0x{uuid.uuid4().hex[:40]}" for _ in range(3)]) + '"]'
            bet.initial_stake_amount = Decimal(str(random.uniform(0.5, 3.0)))
            bet.currency = 'ETH'
            bet.transaction_hash = f"0x{uuid.uuid4().hex[:64]}"
            bet.status = 'expired'
            db.session.add(bet)
            db.session.flush()  # Flush to get the bet ID
            
            # Add stakes - all confirmed
            for j in range(random.randint(3, 7)):
                stake = Stake()
                stake.bet_id = bet.id
                stake.staker_wallet = f"0x{uuid.uuid4().hex[:40]}"
                stake.amount = Decimal(str(random.uniform(0.1, 0.8)))
                stake.currency = bet.currency
                stake.transaction_hash = f"0x{uuid.uuid4().hex[:64]}"
                stake.position = 'for' if j < 4 else 'against'
                stake.status = 'confirmed'
                db.session.add(stake)
                
                # Transaction for stake
                stake_tx = Transaction()
                stake_tx.transaction_hash = stake.transaction_hash
                stake_tx.from_address = stake.staker_wallet
                stake_tx.to_address = "platform_pool"
                stake_tx.amount = stake.amount
                stake_tx.currency = stake.currency
                stake_tx.transaction_type = 'stake'
                stake_tx.related_bet_id = bet.id
                stake_tx.status = 'confirmed'
                db.session.add(stake_tx)
        
        # 3. VALIDATING BETS (1) - Oracle submitted, awaiting consensus
        bet = Bet()
        bet.creator_wallet = f"0x{uuid.uuid4().hex[:40]}"
        bet.actor_id = actors[0].id  # Elon Musk
        bet.predicted_text = "AI will fundamentally change how we interact with technology"
        bet.start_time = current_time - timedelta(hours=72)
        bet.end_time = current_time - timedelta(hours=24)
        oracle_wallets = [f"0x{uuid.uuid4().hex[:40]}" for _ in range(3)]
        bet.oracle_wallets = '["' + '","'.join(oracle_wallets) + '"]'
        bet.initial_stake_amount = Decimal('1.5')
        bet.currency = 'ETH'
        bet.transaction_hash = f"0x{uuid.uuid4().hex[:64]}"
        bet.status = 'validating'
        db.session.add(bet)
        db.session.flush()  # Flush to get the bet ID
        
        # Add oracle submission
        oracle_sub = OracleSubmission()
        oracle_sub.bet_id = bet.id
        oracle_sub.oracle_wallet = oracle_wallets[0]
        oracle_sub.submitted_text = "AI will completely transform how we interact with technology and each other"
        oracle_sub.signature = f"sig_{uuid.uuid4().hex[:32]}"
        oracle_sub.votes_for = 2
        oracle_sub.votes_against = 0
        oracle_sub.status = 'pending'
        oracle_sub.created_at = current_time - timedelta(hours=20)
        db.session.add(oracle_sub)
        
        # 4. RESOLVED BETS (3) - Fully resolved with payouts
        for i in range(3):
            bet = Bet()
            bet.creator_wallet = f"0x{uuid.uuid4().hex[:40]}"
            bet.actor_id = random.choice(actors).id
            bet.predicted_text = f"The future of {random.choice(['finance', 'healthcare', 'education'])} is {random.choice(['decentralized', 'digital', 'automated'])}"
            bet.start_time = current_time - timedelta(days=random.randint(5, 10))
            bet.end_time = current_time - timedelta(days=random.randint(2, 4))
            bet.oracle_wallets = '["' + '","'.join([f"0x{uuid.uuid4().hex[:40]}" for _ in range(3)]) + '"]'
            bet.initial_stake_amount = Decimal(str(random.uniform(0.5, 2.0)))
            bet.currency = random.choice(['ETH', 'BTC'])
            bet.transaction_hash = f"0x{uuid.uuid4().hex[:64]}"
            bet.status = 'resolved'
            bet.resolution_text = bet.predicted_text + " and it's happening now"
            bet.levenshtein_distance = random.randint(5, 15)
            bet.resolution_time = current_time - timedelta(days=1)
            db.session.add(bet)
            db.session.flush()  # Flush to get the bet ID
            
            # Add stakes - mix of won and lost
            total_pool = Decimal('0')
            winning_stakes = []
            losing_stakes = []
            
            for j in range(random.randint(5, 10)):
                stake = Stake()
                stake.bet_id = bet.id
                stake.staker_wallet = f"0x{uuid.uuid4().hex[:40]}"
                stake.amount = Decimal(str(random.uniform(0.1, 1.0)))
                stake.currency = bet.currency
                stake.transaction_hash = f"0x{uuid.uuid4().hex[:64]}"
                stake.position = 'for' if j < 6 else 'against'
                
                # For resolved bets, stakes are either won or lost
                if stake.position == 'for':
                    stake.status = 'won'
                    winning_stakes.append(stake)
                else:
                    stake.status = 'lost'
                    losing_stakes.append(stake)
                
                total_pool += stake.amount
                db.session.add(stake)
                
                # Add confirmed stake transaction
                stake_tx = Transaction()
                stake_tx.transaction_hash = stake.transaction_hash
                stake_tx.from_address = stake.staker_wallet
                stake_tx.to_address = "platform_pool"
                stake_tx.amount = stake.amount
                stake_tx.currency = stake.currency
                stake_tx.transaction_type = 'stake'
                stake_tx.related_bet_id = bet.id
                stake_tx.status = 'confirmed'
                db.session.add(stake_tx)
            
            # Calculate and create payouts for winners
            platform_fee = total_pool * Decimal('0.05')
            distributable_pool = total_pool - platform_fee
            
            if winning_stakes:
                total_winning_amount = sum(s.amount for s in winning_stakes)
                
                for stake in winning_stakes:
                    stake_proportion = stake.amount / total_winning_amount
                    payout_amount = stake.amount + (distributable_pool * stake_proportion)
                    stake.payout_amount = payout_amount
                    
                    # Create payout transaction
                    payout_tx = Transaction()
                    payout_tx.transaction_hash = f"payout_{uuid.uuid4().hex[:16]}"
                    payout_tx.from_address = "platform_pool"
                    payout_tx.to_address = stake.staker_wallet
                    payout_tx.amount = payout_amount
                    payout_tx.currency = stake.currency
                    payout_tx.transaction_type = 'payout'
                    payout_tx.related_bet_id = bet.id
                    payout_tx.status = 'confirmed'
                    payout_tx.created_at = bet.resolution_time + timedelta(hours=1)
                    db.session.add(payout_tx)
                    
                    stake.payout_transaction_hash = payout_tx.transaction_hash
            
            # Create platform fee transaction
            fee_tx = Transaction()
            fee_tx.transaction_hash = f"fee_{uuid.uuid4().hex[:16]}"
            fee_tx.from_address = "platform_pool"
            fee_tx.to_address = "platform_treasury"
            fee_tx.amount = platform_fee
            fee_tx.currency = bet.currency
            fee_tx.transaction_type = 'fee'
            fee_tx.related_bet_id = bet.id
            fee_tx.platform_fee = platform_fee
            fee_tx.status = 'confirmed'
            fee_tx.created_at = bet.resolution_time + timedelta(hours=1)
            db.session.add(fee_tx)
            
            # Add consensus oracle submission
            oracle_sub = OracleSubmission()
            oracle_sub.bet_id = bet.id
            oracle_sub.oracle_wallet = oracle_wallets[0]
            oracle_sub.submitted_text = bet.resolution_text
            oracle_sub.signature = f"sig_{uuid.uuid4().hex[:32]}"
            oracle_sub.votes_for = 3
            oracle_sub.votes_against = 0
            oracle_sub.status = 'consensus'
            oracle_sub.is_consensus = True
            oracle_sub.created_at = bet.resolution_time - timedelta(hours=2)
            db.session.add(oracle_sub)
        
        db.session.commit()
        
        # Get counts for confirmation
        bet_counts = {
            'active': Bet.query.filter_by(status='active').count(),
            'expired': Bet.query.filter_by(status='expired').count(),
            'validating': Bet.query.filter_by(status='validating').count(),
            'resolved': Bet.query.filter_by(status='resolved').count()
        }
        
        stake_counts = {
            'confirmed': Stake.query.filter_by(status='confirmed').count(),
            'won': Stake.query.filter_by(status='won').count(),
            'lost': Stake.query.filter_by(status='lost').count()
        }
        
        tx_counts = {
            'stake': Transaction.query.filter_by(transaction_type='stake').count(),
            'payout': Transaction.query.filter_by(transaction_type='payout').count(),
            'fee': Transaction.query.filter_by(transaction_type='fee').count(),
            'confirmed': Transaction.query.filter_by(status='confirmed').count()
        }
        
        flash(f'''Test data generated successfully with proper workflow!
        
        Bets: {bet_counts['active']} active, {bet_counts['expired']} expired, 
              {bet_counts['validating']} validating, {bet_counts['resolved']} resolved
        
        Stakes: {stake_counts['confirmed']} confirmed, {stake_counts['won']} won, {stake_counts['lost']} lost
        
        Transactions: {tx_counts['stake']} stakes, {tx_counts['payout']} payouts, 
                     {tx_counts['fee']} fees (all {tx_counts['confirmed']} confirmed)
        ''', 'success')
        
        return redirect(url_for('test_data_v2.index'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating test data: {e}")
        flash(f'Error generating test data: {str(e)}', 'error')
        return redirect(url_for('test_data_v2.index'))
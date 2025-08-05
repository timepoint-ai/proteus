"""
Route to generate realistic test data with proper status flows
"""
from flask import Blueprint, redirect, url_for, flash
from app import db
from models import (
    Actor, PredictionMarket, Submission, Bet, Transaction, 
    OracleSubmission, NodeOperator
)
# Phase 1: Bet resolution service deprecated - handled by DecentralizedOracle contract
# from services.bet_resolution import MarketResolutionService
from services.text_analysis import TextAnalysisService
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
import json
import uuid
import logging

logger = logging.getLogger(__name__)

generate_data_bp = Blueprint('generate_data', __name__, url_prefix='/generate')

# Sample data
SAMPLE_ACTORS = [
    ("Elon Musk", "CEO of Tesla and SpaceX, tech entrepreneur"),
    ("Taylor Swift", "Global pop star and songwriter"),
    ("Donald Trump", "Former US President and businessman"),
    ("Oprah Winfrey", "Media mogul and talk show host"),
    ("Bill Gates", "Microsoft founder and philanthropist"),
    ("Joe Biden", "Current US President"),
    ("LeBron James", "NBA superstar"),
    ("Kim Kardashian", "Reality TV star and entrepreneur")
]

SAMPLE_PREDICTIONS = [
    "AI will revolutionize everything in the next 5 years.",
    "The economy is doing great, best it's ever been.",
    "Climate change is the biggest threat to humanity.",
    "We need to invest more in renewable energy.",
    "Cryptocurrency is the future of finance.",
    "Education needs a complete overhaul.",
    "Healthcare should be a basic human right.",
    "Space exploration will define the next century.",
    "Social media is destroying society.",
    "Electric vehicles will dominate by 2030."
]

def generate_wallet_address():
    """Generate a realistic wallet address"""
    return f"0x{''.join(random.choices(string.hexdigits.lower(), k=40))}"

def generate_transaction_hash():
    """Generate a realistic transaction hash"""
    return f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}"

def create_transaction(tx_type, from_addr, to_addr, amount, currency, status='confirmed', 
                      related_market_id=None, related_submission_id=None, related_bet_id=None):
    """Create a transaction record"""
    tx = Transaction(
        transaction_hash=generate_transaction_hash(),
        from_address=from_addr,
        to_address=to_addr,
        amount=amount,
        currency=currency,
        transaction_type=tx_type,
        status=status,
        related_market_id=related_market_id,
        related_submission_id=related_submission_id,
        related_bet_id=related_bet_id,
        block_number=random.randint(1000000, 9999999) if status == 'confirmed' else None
    )
    db.session.add(tx)
    return tx

@generate_data_bp.route('/realistic')
def generate_realistic():
    """Generate realistic test data with proper status flows"""
    try:
        # Clear existing data in proper order to avoid foreign key constraints
        logger.info("Clearing existing data...")
        
        # Import VerificationModule to delete it first
        from models import VerificationModule
        
        # Delete in reverse order of dependencies
        db.session.query(Transaction).delete()
        db.session.query(VerificationModule).delete()  # Delete verification modules before submissions
        db.session.query(Bet).delete()
        db.session.query(OracleSubmission).delete()
        db.session.query(Submission).delete()
        db.session.query(PredictionMarket).delete()
        db.session.query(Actor).delete()
        db.session.query(NodeOperator).filter(NodeOperator.operator_id != 'default-node-001').delete()
        db.session.commit()
        
        # Create actors
        logger.info("Creating actors...")
        actors = []
        for name, description in SAMPLE_ACTORS:
            actor = Actor(
                name=name,
                description=description,
                wallet_address=generate_wallet_address(),
                status='approved',
                approval_votes=random.randint(15, 30),
                rejection_votes=random.randint(0, 3)
            )
            actors.append(actor)
            db.session.add(actor)
        db.session.commit()
        
        # Create node operators for oracles
        logger.info("Creating node operators...")
        nodes = []
        for i in range(5):
            node = NodeOperator(
                operator_id=f"oracle-node-{i+1}",
                status='active',
                public_key=f"pk_oracle_{i+1}_{uuid.uuid4().hex[:16]}",
                node_address=generate_wallet_address(),
                last_seen=datetime.utcnow()
            )
            nodes.append(node)
            db.session.add(node)
        db.session.commit()
        
        # Services
        resolution_service = MarketResolutionService()
        text_service = TextAnalysisService()
        
        current_time = datetime.utcnow()
        
        # 1. Create ACTIVE markets (3)
        logger.info("Creating active markets...")
        for i in range(3):
            actor = random.choice(actors)
            start_time = current_time - timedelta(hours=random.randint(1, 12))
            end_time = current_time + timedelta(hours=random.randint(24, 72))
            
            market = PredictionMarket(
                actor_id=actor.id,
                start_time=start_time,
                end_time=end_time,
                oracle_wallets=json.dumps([node.node_address for node in random.sample(nodes, 3)]),
                status='active'
            )
            db.session.add(market)
            db.session.flush()
            
            # Create submissions
            predictions = random.sample(SAMPLE_PREDICTIONS, 3)
            for j, (pred_text, sub_type) in enumerate(zip(predictions, ['original', 'competitor', 'competitor'])):
                creator_wallet = generate_wallet_address()
                stake_amount = Decimal(str(random.uniform(0.5, 2.0)))
                
                submission = Submission(
                    market_id=market.id,
                    creator_wallet=creator_wallet,
                    predicted_text=pred_text,
                    submission_type=sub_type,
                    initial_stake_amount=stake_amount,
                    currency='ETH',
                    transaction_hash=generate_transaction_hash()
                )
                db.session.add(submission)
                db.session.flush()
                
                # Create initial stake transaction
                create_transaction(
                    'stake',
                    creator_wallet,
                    'platform_pool',
                    stake_amount,
                    'ETH',
                    'confirmed',
                    related_market_id=market.id,
                    related_submission_id=submission.id
                )
                
                # Add some bets
                for k in range(random.randint(2, 5)):
                    bettor_wallet = generate_wallet_address()
                    bet_amount = Decimal(str(random.uniform(0.1, 0.5)))
                    
                    bet = Bet(
                        submission_id=submission.id,
                        bettor_wallet=bettor_wallet,
                        amount=bet_amount,
                        currency='ETH',
                        transaction_hash=generate_transaction_hash(),
                        status='confirmed'
                    )
                    db.session.add(bet)
                    db.session.flush()
                    
                    # Create bet transaction
                    create_transaction(
                        'stake',
                        bettor_wallet,
                        'platform_pool',
                        bet_amount,
                        'ETH',
                        'confirmed',
                        related_market_id=market.id,
                        related_submission_id=submission.id,
                        related_bet_id=bet.id
                    )
        
        # 2. Create EXPIRED markets awaiting oracle (2)
        logger.info("Creating expired markets...")
        for i in range(2):
            actor = random.choice(actors)
            start_time = current_time - timedelta(hours=random.randint(48, 72))
            end_time = current_time - timedelta(hours=random.randint(2, 24))
            
            market = PredictionMarket(
                actor_id=actor.id,
                start_time=start_time,
                end_time=end_time,
                oracle_wallets=json.dumps([node.node_address for node in random.sample(nodes, 3)]),
                status='expired'
            )
            db.session.add(market)
            db.session.flush()
            
            # Create submissions with bets
            predictions = random.sample(SAMPLE_PREDICTIONS, 2)
            for j, (pred_text, sub_type) in enumerate(zip(predictions, ['original', 'competitor'])):
                creator_wallet = generate_wallet_address()
                stake_amount = Decimal(str(random.uniform(0.8, 1.5)))
                
                submission = Submission(
                    market_id=market.id,
                    creator_wallet=creator_wallet,
                    predicted_text=pred_text,
                    submission_type=sub_type,
                    initial_stake_amount=stake_amount,
                    currency='ETH',
                    transaction_hash=generate_transaction_hash()
                )
                db.session.add(submission)
                db.session.flush()
                
                # Create initial stake transaction
                create_transaction(
                    'stake',
                    creator_wallet,
                    'platform_pool',
                    stake_amount,
                    'ETH',
                    'confirmed',
                    related_market_id=market.id,
                    related_submission_id=submission.id
                )
                
                # Add bets
                for k in range(random.randint(3, 6)):
                    bettor_wallet = generate_wallet_address()
                    bet_amount = Decimal(str(random.uniform(0.2, 0.8)))
                    
                    bet = Bet(
                        submission_id=submission.id,
                        bettor_wallet=bettor_wallet,
                        amount=bet_amount,
                        currency='ETH',
                        transaction_hash=generate_transaction_hash(),
                        status='confirmed'
                    )
                    db.session.add(bet)
                    db.session.flush()
                    
                    # Create bet transaction
                    create_transaction(
                        'stake',
                        bettor_wallet,
                        'platform_pool',
                        bet_amount,
                        'ETH',
                        'confirmed',
                        related_market_id=market.id,
                        related_submission_id=submission.id,
                        related_bet_id=bet.id
                    )
        
        # 3. Create VALIDATING market (1)
        logger.info("Creating validating market...")
        actor = random.choice(actors)
        start_time = current_time - timedelta(hours=96)
        end_time = current_time - timedelta(hours=48)
        
        market = PredictionMarket(
            actor_id=actor.id,
            start_time=start_time,
            end_time=end_time,
            oracle_wallets=json.dumps([node.node_address for node in random.sample(nodes, 3)]),
            status='validating'
        )
        db.session.add(market)
        db.session.flush()
        
        # Create submissions
        predictions = random.sample(SAMPLE_PREDICTIONS, 3)
        submissions = []
        for j, (pred_text, sub_type) in enumerate(zip(predictions, ['original', 'competitor', 'null'])):
            creator_wallet = generate_wallet_address()
            stake_amount = Decimal(str(random.uniform(1.0, 2.5)))
            
            submission = Submission(
                market_id=market.id,
                creator_wallet=creator_wallet,
                predicted_text=pred_text if sub_type != 'null' else None,
                submission_type=sub_type,
                initial_stake_amount=stake_amount,
                currency='ETH',
                transaction_hash=generate_transaction_hash()
            )
            submissions.append(submission)
            db.session.add(submission)
            db.session.flush()
            
            # Create initial stake transaction
            create_transaction(
                'stake',
                creator_wallet,
                'platform_pool',
                stake_amount,
                'ETH',
                'confirmed',
                related_market_id=market.id,
                related_submission_id=submission.id
            )
            
            # Add bets
            for k in range(random.randint(4, 8)):
                bettor_wallet = generate_wallet_address()
                bet_amount = Decimal(str(random.uniform(0.3, 1.0)))
                
                bet = Bet(
                    submission_id=submission.id,
                    bettor_wallet=bettor_wallet,
                    amount=bet_amount,
                    currency='ETH',
                    transaction_hash=generate_transaction_hash(),
                    status='confirmed'
                )
                db.session.add(bet)
                db.session.flush()
                
                # Create bet transaction
                create_transaction(
                    'stake',
                    bettor_wallet,
                    'platform_pool',
                    bet_amount,
                    'ETH',
                    'confirmed',
                    related_market_id=market.id,
                    related_submission_id=submission.id,
                    related_bet_id=bet.id
                )
        
        # Create oracle submission
        oracle_text = random.choice(SAMPLE_PREDICTIONS)
        oracle_submission = OracleSubmission(
            market_id=market.id,
            oracle_wallet=json.loads(market.oracle_wallets)[0],
            submitted_text=oracle_text,
            signature=f"sig_{uuid.uuid4().hex[:128]}",
            votes_for=2,
            votes_against=0,
            status='pending',
            is_consensus=False
        )
        db.session.add(oracle_submission)
        
        # 4. Create RESOLVED markets (3)
        logger.info("Creating resolved markets...")
        for i in range(3):
            actor = random.choice(actors)
            start_time = current_time - timedelta(days=random.randint(5, 10))
            end_time = current_time - timedelta(days=random.randint(2, 4))
            
            market = PredictionMarket(
                actor_id=actor.id,
                start_time=start_time,
                end_time=end_time,
                oracle_wallets=json.dumps([node.node_address for node in random.sample(nodes, 3)]),
                status='validating'  # Will be resolved after oracle submission
            )
            db.session.add(market)
            db.session.flush()
            
            # Create submissions
            predictions = random.sample(SAMPLE_PREDICTIONS, 3)
            submissions = []
            for j, (pred_text, sub_type) in enumerate(zip(predictions, ['original', 'competitor', 'competitor'])):
                creator_wallet = generate_wallet_address()
                stake_amount = Decimal(str(random.uniform(0.5, 2.0)))
                
                submission = Submission(
                    market_id=market.id,
                    creator_wallet=creator_wallet,
                    predicted_text=pred_text,
                    submission_type=sub_type,
                    initial_stake_amount=stake_amount,
                    currency='ETH',
                    transaction_hash=generate_transaction_hash()
                )
                submissions.append(submission)
                db.session.add(submission)
                db.session.flush()
                
                # Create initial stake transaction
                create_transaction(
                    'stake',
                    creator_wallet,
                    'platform_pool',
                    stake_amount,
                    'ETH',
                    'confirmed',
                    related_market_id=market.id,
                    related_submission_id=submission.id
                )
                
                # Add bets with mostly confirmed status
                for k in range(random.randint(5, 10)):
                    bettor_wallet = generate_wallet_address()
                    bet_amount = Decimal(str(random.uniform(0.1, 0.5)))
                    
                    # Most bets are confirmed, some pending
                    bet_status = 'confirmed' if random.random() > 0.1 else 'pending'
                    tx_status = bet_status
                    
                    bet = Bet(
                        submission_id=submission.id,
                        bettor_wallet=bettor_wallet,
                        amount=bet_amount,
                        currency='ETH',
                        transaction_hash=generate_transaction_hash(),
                        status=bet_status
                    )
                    db.session.add(bet)
                    db.session.flush()
                    
                    # Create bet transaction
                    create_transaction(
                        'stake',
                        bettor_wallet,
                        'platform_pool',
                        bet_amount,
                        'ETH',
                        tx_status,
                        related_market_id=market.id,
                        related_submission_id=submission.id,
                        related_bet_id=bet.id
                    )
            
            # Create oracle submission with consensus
            oracle_text = random.choice([s.predicted_text for s in submissions if s.predicted_text])
            oracle_submission = OracleSubmission(
                market_id=market.id,
                oracle_wallet=json.loads(market.oracle_wallets)[0],
                submitted_text=oracle_text,
                signature=f"sig_{uuid.uuid4().hex[:128]}",
                votes_for=3,
                votes_against=0,
                status='consensus',
                is_consensus=True
            )
            db.session.add(oracle_submission)
            db.session.flush()
            
            # Resolve the market
            logger.info(f"Resolving market {market.id}...")
            if resolution_service.resolve_market(str(market.id)):
                logger.info(f"Market {market.id} resolved successfully")
            else:
                logger.warning(f"Failed to resolve market {market.id}")
        
        db.session.commit()
        
        # Get statistics
        stats = {
            'actors': Actor.query.count(),
            'markets': {
                'active': PredictionMarket.query.filter_by(status='active').count(),
                'expired': PredictionMarket.query.filter_by(status='expired').count(),
                'validating': PredictionMarket.query.filter_by(status='validating').count(),
                'resolved': PredictionMarket.query.filter_by(status='resolved').count()
            },
            'submissions': Submission.query.count(),
            'bets': {
                'total': Bet.query.count(),
                'confirmed': Bet.query.filter_by(status='confirmed').count(),
                'won': Bet.query.filter_by(status='won').count(),
                'lost': Bet.query.filter_by(status='lost').count()
            },
            'transactions': {
                'total': Transaction.query.count(),
                'confirmed': Transaction.query.filter_by(status='confirmed').count(),
                'pending': Transaction.query.filter_by(status='pending').count()
            }
        }
        
        flash(f"""Test Data Generated Successfully!
        
        Actors: {stats['actors']}
        Markets: {stats['markets']['active']} active, {stats['markets']['expired']} expired, 
                {stats['markets']['validating']} validating, {stats['markets']['resolved']} resolved
        Submissions: {stats['submissions']}
        Bets: {stats['bets']['total']} total ({stats['bets']['confirmed']} confirmed, 
              {stats['bets']['won']} won, {stats['bets']['lost']} lost)
        Transactions: {stats['transactions']['total']} total 
                     ({stats['transactions']['confirmed']} confirmed, {stats['transactions']['pending']} pending)
        """, 'success')
        
        return redirect(url_for('admin.markets_view'))
        
    except Exception as e:
        logger.error(f"Error generating test data: {e}")
        db.session.rollback()
        flash(f'Error generating test data: {str(e)}', 'error')
        return redirect(url_for('admin.markets_view'))
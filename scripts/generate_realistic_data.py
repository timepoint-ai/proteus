"""
Generate realistic test data with proper status flows and real database calculations
Updated for X.com usernames and BASE blockchain
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    Actor, PredictionMarket, Submission, Bet, Transaction, 
    OracleSubmission, NodeOperator, SyntheticTimeEntry
)
from services.bet_resolution import MarketResolutionService
from services.text_analysis import TextAnalysisService
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data - Using X.com usernames (same as create_test_actors.py)
SAMPLE_ACTORS = [
    ("elonmusk", "Elon Musk", "CEO of Tesla and SpaceX, tech entrepreneur"),
    ("taylorswift13", "Taylor Swift", "Global pop star and songwriter"),
    ("BillGates", "Bill Gates", "Microsoft founder and philanthropist"),
    ("Oprah", "Oprah Winfrey", "Media mogul and talk show host"),
    ("GordonRamsay", "Gordon Ramsay", "Chef, TV personality"),
    ("MrBeast", "MrBeast", "YouTuber, Philanthropist"),
    ("cristiano", "Cristiano Ronaldo", "Professional footballer"),
    ("jimmyfallon", "Jimmy Fallon", "Host of The Tonight Show")
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

def create_transaction(tx_type, from_addr, to_addr, amount, status='confirmed', 
                      related_market_id=None, related_submission_id=None, related_bet_id=None):
    """Create a transaction record"""
    tx = Transaction(
        transaction_hash=generate_transaction_hash(),
        from_address=from_addr,
        to_address=to_addr,
        amount=amount,
        transaction_type=tx_type,
        status=status,
        related_market_id=related_market_id,
        related_submission_id=related_submission_id,
        related_bet_id=related_bet_id,
        block_number=random.randint(1000000, 9999999) if status == 'confirmed' else None,
        gas_used=random.randint(21000, 100000),
        gas_price=Decimal('0.001')  # BASE gas price
    )
    db.session.add(tx)
    return tx

def generate_realistic_data():
    """Generate realistic test data with proper status flows"""
    with app.app_context():
        try:
            # Clear existing data (except actors)
            logger.info("Clearing existing data (preserving actors)...")
            db.session.query(Transaction).delete()
            db.session.query(OracleSubmission).delete()
            db.session.query(Bet).delete()
            db.session.query(Submission).delete()
            db.session.query(PredictionMarket).delete()
            # Don't delete actors, we'll use existing ones
            db.session.query(NodeOperator).filter(NodeOperator.operator_id != 'default-node-001').delete()
            db.session.commit()
            
            # Get existing test actors or create them if needed
            logger.info("Getting test actors...")
            actors = Actor.query.filter_by(is_test_account=True).all()
            
            if not actors:
                logger.info("No test actors found, creating them...")
                for x_username, display_name, bio in SAMPLE_ACTORS:
                    actor = Actor(
                        x_username=x_username,
                        display_name=display_name,
                        bio=bio,
                        verified=True,
                        follower_count=random.randint(1000000, 100000000),
                        is_test_account=True,
                        status='active',
                        last_sync=datetime.utcnow()
                    )
                    actors.append(actor)
                    db.session.add(actor)
                db.session.commit()
            else:
                logger.info(f"Found {len(actors)} existing test actors")
            
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
                    stake_amount = Decimal(str(random.uniform(0.005, 0.02)))  # BASE amounts
                    
                    submission = Submission(
                        market_id=market.id,
                        creator_wallet=creator_wallet,
                        predicted_text=pred_text,
                        submission_type=sub_type,
                        initial_stake_amount=stake_amount,
                        base_tx_hash=generate_transaction_hash()
                    )
                    db.session.add(submission)
                    db.session.flush()
                    
                    # Create initial stake transaction
                    create_transaction(
                        'stake',
                        creator_wallet,
                        'platform_pool',
                        stake_amount,
                        'confirmed',
                        related_market_id=market.id,
                        related_submission_id=submission.id
                    )
                    
                    # Add some bets
                    for k in range(random.randint(2, 5)):
                        bettor_wallet = generate_wallet_address()
                        bet_amount = Decimal(str(random.uniform(0.001, 0.005)))  # BASE amounts
                        
                        bet = Bet(
                            submission_id=submission.id,
                            bettor_wallet=bettor_wallet,
                            amount=bet_amount,
                            base_tx_hash=generate_transaction_hash(),
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
                    stake_amount = Decimal(str(random.uniform(0.008, 0.015)))  # BASE amounts
                    
                    submission = Submission(
                        market_id=market.id,
                        creator_wallet=creator_wallet,
                        predicted_text=pred_text,
                        submission_type=sub_type,
                        initial_stake_amount=stake_amount,
                        base_tx_hash=generate_transaction_hash()
                    )
                    db.session.add(submission)
                    db.session.flush()
                    
                    # Create initial stake transaction
                    create_transaction(
                        'stake',
                        creator_wallet,
                        'platform_pool',
                        stake_amount,
                        'confirmed',
                        related_market_id=market.id,
                        related_submission_id=submission.id
                    )
                    
                    # Add bets
                    for k in range(random.randint(3, 6)):
                        bettor_wallet = generate_wallet_address()
                        bet_amount = Decimal(str(random.uniform(0.002, 0.008)))  # BASE amounts
                        
                        bet = Bet(
                            submission_id=submission.id,
                            bettor_wallet=bettor_wallet,
                            amount=bet_amount,
                            base_tx_hash=generate_transaction_hash(),
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
                            'confirmed',
                            related_market_id=market.id,
                            related_submission_id=submission.id,
                            related_bet_id=bet.id
                        )
            
            # 3. Create VALIDATING markets with oracle submissions (2)
            logger.info("Creating validating markets...")
            for i in range(2):
                actor = random.choice(actors)
                start_time = current_time - timedelta(hours=random.randint(96, 120))
                end_time = current_time - timedelta(hours=random.randint(48, 72))
                
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
                submissions = []
                predictions = random.sample(SAMPLE_PREDICTIONS, 2)
                for j, (pred_text, sub_type) in enumerate(zip(predictions, ['original', 'competitor'])):
                    creator_wallet = generate_wallet_address()
                    stake_amount = Decimal(str(random.uniform(0.01, 0.025)))  # BASE amounts
                    
                    submission = Submission(
                        market_id=market.id,
                        creator_wallet=creator_wallet,
                        predicted_text=pred_text,
                        submission_type=sub_type,
                        initial_stake_amount=stake_amount,
                        base_tx_hash=generate_transaction_hash()
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
                        'confirmed',
                        related_market_id=market.id,
                        related_submission_id=submission.id
                    )
                    
                    # Add bets
                    for k in range(random.randint(4, 8)):
                        bettor_wallet = generate_wallet_address()
                        bet_amount = Decimal(str(random.uniform(0.003, 0.01)))  # BASE amounts
                        
                        bet = Bet(
                            submission_id=submission.id,
                            bettor_wallet=bettor_wallet,
                            amount=bet_amount,
                            base_tx_hash=generate_transaction_hash(),
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
                            'confirmed',
                            related_market_id=market.id,
                            related_submission_id=submission.id,
                            related_bet_id=bet.id
                        )
                
                # Create oracle submissions
                actual_text = random.choice(predictions)
                for node in random.sample(nodes, 3):
                    oracle_sub = OracleSubmission(
                        market_id=market.id,
                        oracle_wallet=node.node_address,
                        submitted_text=actual_text,
                        signature=f"sig_{uuid.uuid4().hex[:32]}",
                        tweet_id=f"{random.randint(1000000000000000000, 9999999999999999999)}",
                        tweet_timestamp=current_time - timedelta(hours=random.randint(24, 48))
                    )
                    db.session.add(oracle_sub)
            
            # 4. Create RESOLVED markets (3)
            logger.info("Creating resolved markets...")
            for i in range(3):
                actor = random.choice(actors)
                start_time = current_time - timedelta(days=random.randint(7, 14))
                end_time = current_time - timedelta(days=random.randint(4, 6))
                
                market = PredictionMarket(
                    actor_id=actor.id,
                    start_time=start_time,
                    end_time=end_time,
                    oracle_wallets=json.dumps([node.node_address for node in random.sample(nodes, 3)]),
                    status='resolved',
                    resolution_time=end_time + timedelta(hours=2)
                )
                db.session.add(market)
                db.session.flush()
                
                # Create submissions
                submissions = []
                predictions = random.sample(SAMPLE_PREDICTIONS, 3)
                for j, (pred_text, sub_type) in enumerate(zip(predictions, ['original', 'competitor', 'competitor'])):
                    creator_wallet = generate_wallet_address()
                    stake_amount = Decimal(str(random.uniform(0.015, 0.03)))  # BASE amounts
                    
                    submission = Submission(
                        market_id=market.id,
                        creator_wallet=creator_wallet,
                        predicted_text=pred_text,
                        submission_type=sub_type,
                        initial_stake_amount=stake_amount,
                        base_tx_hash=generate_transaction_hash(),
                        levenshtein_distance=random.randint(0, 15) if j > 0 else 0
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
                        'confirmed',
                        related_market_id=market.id,
                        related_submission_id=submission.id
                    )
                    
                    # Add bets
                    bet_count = random.randint(5, 10)
                    for k in range(bet_count):
                        bettor_wallet = generate_wallet_address()
                        bet_amount = Decimal(str(random.uniform(0.005, 0.015)))  # BASE amounts
                        
                        bet = Bet(
                            submission_id=submission.id,
                            bettor_wallet=bettor_wallet,
                            amount=bet_amount,
                            base_tx_hash=generate_transaction_hash(),
                            status='won' if j == 0 else 'lost',
                            payout_amount=bet_amount * Decimal('2.5') if j == 0 else 0
                        )
                        db.session.add(bet)
                        db.session.flush()
                        
                        # Create bet transaction
                        create_transaction(
                            'stake',
                            bettor_wallet,
                            'platform_pool',
                            bet_amount,
                            'confirmed',
                            related_market_id=market.id,
                            related_submission_id=submission.id,
                            related_bet_id=bet.id
                        )
                        
                        # Create payout transaction for winners
                        if j == 0:
                            create_transaction(
                                'payout',
                                'platform_pool',
                                bettor_wallet,
                                bet.payout_amount,
                                'confirmed',
                                related_market_id=market.id,
                                related_submission_id=submission.id,
                                related_bet_id=bet.id
                            )
                
                # Set winning submission and resolution text
                market.winning_submission_id = submissions[0].id
                market.resolution_text = predictions[0]
                submissions[0].is_winner = True
                
                # Create oracle submissions
                for node in random.sample(nodes, 3):
                    oracle_sub = OracleSubmission(
                        market_id=market.id,
                        oracle_wallet=node.node_address,
                        submitted_text=predictions[0],
                        signature=f"sig_{uuid.uuid4().hex[:32]}",
                        status='consensus',
                        is_consensus=True,
                        consensus_percentage=100.0,
                        tweet_id=f"{random.randint(1000000000000000000, 9999999999999999999)}",
                        tweet_timestamp=end_time - timedelta(hours=1)
                    )
                    db.session.add(oracle_sub)
            
            db.session.commit()
            
            # Generate summary
            logger.info("\n=== Test Data Generation Complete ===")
            logger.info(f"Actors created: {len(actors)}")
            logger.info(f"Total markets: {PredictionMarket.query.count()}")
            logger.info(f"  - Active: {PredictionMarket.query.filter_by(status='active').count()}")
            logger.info(f"  - Expired: {PredictionMarket.query.filter_by(status='expired').count()}")
            logger.info(f"  - Validating: {PredictionMarket.query.filter_by(status='validating').count()}")
            logger.info(f"  - Resolved: {PredictionMarket.query.filter_by(status='resolved').count()}")
            logger.info(f"Total submissions: {Submission.query.count()}")
            logger.info(f"Total bets: {Bet.query.count()}")
            logger.info(f"Total transactions: {Transaction.query.count()}")
            logger.info(f"Oracle submissions: {OracleSubmission.query.count()}")
            
            # Show sample actors
            logger.info("\nSample Actors:")
            for actor in actors[:5]:
                logger.info(f"  @{actor.x_username} - {actor.display_name}")
            
        except Exception as e:
            logger.error(f"Error generating test data: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    generate_realistic_data()
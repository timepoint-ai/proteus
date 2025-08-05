"""
Test Data Generation for New Competitive Submission Architecture
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from models import *
from app import db
from datetime import datetime, timedelta
import random
import uuid
import json
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
test_data_new_bp = Blueprint('test_data_new', __name__)

SAMPLE_ACTORS = [
    ("elonmusk", "Elon Musk", "Tech entrepreneur and CEO of Tesla, SpaceX"),
    ("realDonaldTrump", "Donald Trump", "Former US President"),
    ("POTUS", "Joe Biden", "Current US President"),
    ("taylorswift13", "Taylor Swift", "Pop music artist"),
    ("Oprah", "Oprah Winfrey", "Media mogul and talk show host"),
]

SAMPLE_PREDICTIONS = [
    "I think we'll have a colony on Mars by 2030!",
    "The economy is doing great, best it's ever been.",
    "We need to work together to solve climate change.",
    "My new album drops next month, can't wait!",
    "This is the year for personal transformation.",
    "AI will revolutionize everything in the next 5 years.",
    "We're making America great again!",
    "Democracy is under threat, we must defend it.",
    "Love my fans so much! Thank you for the support!",
    "Everyone has the power to change their life.",
]

@test_data_new_bp.route('/')
def index():
    """Display test data generation page"""
    stats = {
        'nodes': NodeOperator.query.count(),
        'actors': Actor.query.count(),
        'markets': PredictionMarket.query.count(),
        'submissions': Submission.query.count(),
        'bets': Bet.query.count(),
        'transactions': Transaction.query.count(),
    }
    return render_template('test_data/new_dashboard.html', stats=stats)

@test_data_new_bp.route('/generate', methods=['POST'])
def generate():
    """Generate test data for the new schema"""
    try:
        # Clear existing data
        db.session.query(Transaction).delete()
        db.session.query(Bet).delete()
        db.session.query(OracleSubmission).delete()
        db.session.query(Submission).delete()
        db.session.query(PredictionMarket).delete()
        db.session.query(Actor).delete()
        db.session.query(NodeOperator).filter(NodeOperator.operator_id != 'default-node-001').delete()
        db.session.commit()
        
        # 1. Create Actors
        actors = []
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
        
        # 2. Create Prediction Markets with Competitive Submissions
        markets = []
        for i in range(10):
            actor = random.choice(actors)
            
            # Create time window for the prediction
            start_time = datetime.utcnow() + timedelta(hours=random.randint(-48, 48))
            end_time = start_time + timedelta(hours=random.randint(1, 24))
            
            # Create oracle wallets
            oracle_wallets = []
            for j in range(3):
                oracle_wallets.append(f"0x{''.join(random.choices('0123456789abcdef', k=40))}")
            
            # Create the prediction market
            market = PredictionMarket(
                actor_id=actor.id,
                start_time=start_time,
                end_time=end_time,
                oracle_wallets=json.dumps(oracle_wallets),
                status='active' if end_time > datetime.utcnow() else 'expired'
            )
            markets.append(market)
            db.session.add(market)
            db.session.flush()
            
            # 3. Create Competing Submissions for each market
            num_submissions = random.randint(2, 5)
            
            for j in range(num_submissions):
                # First submission is original, others are competitors
                submission_type = 'original' if j == 0 else 'competitor'
                
                # Sometimes add a null submission (betting nothing will be said)
                if j == num_submissions - 1 and random.random() > 0.7:
                    submission_type = 'null'
                    predicted_text = None
                else:
                    # Use variations of predictions
                    base_prediction = random.choice(SAMPLE_PREDICTIONS)
                    if submission_type == 'competitor':
                        # Modify the prediction slightly
                        variations = [
                            base_prediction.replace("!", "."),
                            base_prediction.replace("will", "might"),
                            base_prediction.replace("I think", "I believe"),
                            base_prediction.upper(),
                            base_prediction.lower(),
                        ]
                        predicted_text = random.choice(variations)
                    else:
                        predicted_text = base_prediction
                
                submission = Submission(
                    market_id=market.id,
                    creator_wallet=f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                    predicted_text=predicted_text,
                    submission_type=submission_type,
                    initial_stake_amount=Decimal(random.uniform(0.1, 2.0)),
                    currency='ETH',
                    transaction_hash=f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
                )
                db.session.add(submission)
                db.session.flush()
                
                # 4. Create Bets on Submissions
                num_bets = random.randint(0, 10)
                for k in range(num_bets):
                    bet = Bet(
                        submission_id=submission.id,
                        bettor_wallet=f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                        amount=Decimal(random.uniform(0.01, 0.5)),
                        currency='ETH',
                        transaction_hash=f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                        status='confirmed'
                    )
                    db.session.add(bet)
        
        # 5. Create some resolved markets with oracle submissions
        expired_markets = [m for m in markets if m.status == 'expired']
        for market in expired_markets[:3]:  # Resolve first 3 expired markets
            market.status = 'validating'
            
            # Create oracle submission
            oracle_submission = OracleSubmission(
                market_id=market.id,
                oracle_wallet=json.loads(market.oracle_wallets)[0],
                submitted_text=random.choice(SAMPLE_PREDICTIONS),
                signature=f"sig_{''.join(random.choices('0123456789abcdef', k=128))}",
                votes_for=random.randint(5, 10),
                votes_against=random.randint(0, 2),
                status='consensus',
                is_consensus=True
            )
            db.session.add(oracle_submission)
            
            # Resolve the market
            market.status = 'resolved'
            market.resolution_text = oracle_submission.submitted_text
            market.resolution_time = datetime.utcnow()
            
            # Calculate distances and determine winner
            submissions = Submission.query.filter_by(market_id=market.id).all()
            best_submission = None
            lowest_distance = float('inf')
            
            for submission in submissions:
                if submission.predicted_text:
                    # Simple distance calculation for test data
                    distance = abs(len(submission.predicted_text) - len(oracle_submission.submitted_text))
                    submission.levenshtein_distance = distance
                    
                    if distance < lowest_distance:
                        lowest_distance = distance
                        best_submission = submission
            
            if best_submission:
                best_submission.is_winner = True
                market.winning_submission_id = best_submission.id
        
        db.session.commit()
        
        flash('Test data generated successfully!', 'success')
        return redirect(url_for('test_data_new.index'))
        
    except Exception as e:
        logger.error(f"Error generating test data: {e}")
        db.session.rollback()
        flash(f'Error generating test data: {str(e)}', 'error')
        return redirect(url_for('test_data_new.index'))
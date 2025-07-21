"""
Market Resolution Service
Handles the proper status workflow for market and bet resolution
"""

import os
import logging
from datetime import datetime
from decimal import Decimal
from app import db
from models import PredictionMarket, Submission, Bet, Transaction, OracleSubmission
from sqlalchemy import and_
import uuid

logger = logging.getLogger(__name__)

class MarketResolutionService:
    """Service to handle market resolution with proper status workflow"""
    
    def __init__(self):
        # Get platform fee from environment variable (default 7%)
        self.platform_fee_percentage = Decimal(os.environ.get('PLATFORM_FEE', '0.07'))
    
    def check_and_update_expired_markets(self):
        """Check for active markets that have passed their end time and mark as expired"""
        try:
            current_time = datetime.utcnow()
            
            # Find all active markets that have passed their end time
            expired_markets = PredictionMarket.query.filter(
                and_(
                    PredictionMarket.status == 'active',
                    PredictionMarket.end_time < current_time
                )
            ).all()
            
            for market in expired_markets:
                market.status = 'expired'
                logger.info(f"Market {market.id} marked as expired")
            
            db.session.commit()
            return len(expired_markets)
            
        except Exception as e:
            logger.error(f"Error checking expired markets: {e}")
            db.session.rollback()
            return 0
    
    def transition_market_to_validating(self, market_id: str) -> bool:
        """Transition a market from expired to validating when oracle submits"""
        try:
            market = PredictionMarket.query.get(market_id)
            if not market:
                logger.error(f"Market {market_id} not found")
                return False
                
            if market.status != 'expired':
                logger.error(f"Market {market_id} not in expired state")
                return False
                
            market.status = 'validating'
            db.session.commit()
            logger.info(f"Market {market_id} transitioned to validating")
            return True
            
        except Exception as e:
            logger.error(f"Error transitioning market to validating: {e}")
            db.session.rollback()
            return False
    
    def resolve_market(self, market_id: str, oracle_text: str = None) -> bool:
        """Resolve a market after oracle consensus"""
        try:
            market = PredictionMarket.query.get(market_id)
            if not market:
                logger.error(f"Market {market_id} not found")
                return False
                
            if market.status != 'validating':
                logger.error(f"Market {market_id} not in validating state")
                return False
            
            # Check for oracle consensus
            oracle_submission = OracleSubmission.query.filter_by(
                market_id=market_id,
                is_consensus=True,
                status='consensus'
            ).first()
            
            if not oracle_submission:
                logger.error(f"No consensus oracle submission for market {market_id}")
                return False
            
            # Update market resolution
            market.status = 'resolved'
            market.resolution_text = oracle_submission.submitted_text
            market.resolution_time = datetime.utcnow()
            
            # If null oracle, refund all bets
            if oracle_submission.submitted_text is None:
                market.winning_submission_id = None
                self._process_refunds(market)
            else:
                # Find winning submission
                winning_submission = self._find_winning_submission(market, oracle_submission.submitted_text)
                if winning_submission:
                    market.winning_submission_id = winning_submission.id
                    self._process_payouts(market, winning_submission)
                else:
                    # No valid submissions, refund all
                    self._process_refunds(market)
            
            db.session.commit()
            logger.info(f"Market {market.id} resolved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving market: {e}")
            db.session.rollback()
            return False
    
    def _find_winning_submission(self, market: PredictionMarket, oracle_text: str) -> Submission:
        """Find the submission with lowest Levenshtein distance"""
        from services.text_analysis import TextAnalysisService
        text_service = TextAnalysisService()
        
        submissions = Submission.query.filter_by(market_id=market.id).all()
        
        best_submission = None
        lowest_distance = float('inf')
        
        for submission in submissions:
            # Skip null submissions
            if submission.predicted_text is None:
                continue
                
            distance = text_service.calculate_levenshtein_distance(
                submission.predicted_text,
                oracle_text
            )
            
            submission.levenshtein_distance = distance
            
            if distance < lowest_distance:
                lowest_distance = distance
                best_submission = submission
        
        if best_submission:
            best_submission.is_winner = True
            
        return best_submission
    
    def _process_payouts(self, market: PredictionMarket, winning_submission: Submission):
        """Process payouts for winning bets"""
        try:
            # Get all confirmed bets
            all_bets = Bet.query.join(Submission).filter(
                Submission.market_id == market.id,
                Bet.status == 'confirmed'
            ).all()
            
            # Calculate total pot
            total_pot = sum(bet.amount for bet in all_bets)
            
            # Deduct platform fee
            platform_fee = total_pot * self.platform_fee_percentage
            distributable_pot = total_pot - platform_fee
            
            # Get winning bets
            winning_bets = [bet for bet in all_bets if bet.submission_id == winning_submission.id]
            total_winning_amount = sum(bet.amount for bet in winning_bets)
            
            if total_winning_amount > 0:
                # Calculate payout ratio
                payout_ratio = distributable_pot / total_winning_amount
                
                # Process winning bets
                for bet in winning_bets:
                    bet.payout_amount = bet.amount * payout_ratio
                    bet.status = 'won'
                    
                    # Create payout transaction record
                    self._create_payout_transaction(bet, platform_fee / len(winning_bets))
            
            # Mark losing bets
            for bet in all_bets:
                if bet.submission_id != winning_submission.id:
                    bet.status = 'lost'
                    bet.payout_amount = 0
                    
        except Exception as e:
            logger.error(f"Error processing payouts: {e}")
            raise
    
    def _process_refunds(self, market: PredictionMarket):
        """Process refunds for all bets in a market"""
        try:
            # Get all confirmed bets
            all_bets = Bet.query.join(Submission).filter(
                Submission.market_id == market.id,
                Bet.status == 'confirmed'
            ).all()
            
            for bet in all_bets:
                bet.status = 'refunded'
                bet.payout_amount = bet.amount  # Full refund
                
                # Create refund transaction record
                self._create_refund_transaction(bet)
                
        except Exception as e:
            logger.error(f"Error processing refunds: {e}")
            raise
    
    def _create_payout_transaction(self, bet: Bet, platform_fee_share: Decimal):
        """Create a payout transaction record"""
        transaction = Transaction(
            transaction_hash=f"payout_{bet.id}_{uuid.uuid4().hex[:8]}",  # Mock for now
            from_address="platform_wallet",  # Should be from config
            to_address=bet.bettor_wallet,
            amount=bet.payout_amount,
            currency=bet.currency,
            transaction_type='payout',
            related_bet_id=bet.id,
            platform_fee=platform_fee_share,
            status='pending'  # Will be confirmed when blockchain tx completes
        )
        db.session.add(transaction)
    
    def _create_refund_transaction(self, bet: Bet):
        """Create a refund transaction record"""
        transaction = Transaction(
            transaction_hash=f"refund_{bet.id}_{uuid.uuid4().hex[:8]}",  # Mock for now
            from_address="platform_wallet",  # Should be from config
            to_address=bet.bettor_wallet,
            amount=bet.amount,
            currency=bet.currency,
            transaction_type='refund',
            related_bet_id=bet.id,
            platform_fee=0,
            status='pending'  # Will be confirmed when blockchain tx completes
        )
        db.session.add(transaction)
    
    def process_pending_transactions(self):
        """Process pending blockchain transactions"""
        try:
            from services.blockchain import BlockchainService
            blockchain_service = BlockchainService()
            
            # Get pending transactions
            pending_txs = Transaction.query.filter_by(status='pending').all()
            
            for tx in pending_txs:
                # Check blockchain status (mock for now)
                # In production, would check actual blockchain
                tx.status = 'confirmed'
                tx.block_number = 12345678  # Mock block number
                
                # Update bet payout status
                if tx.related_bet_id:
                    bet = Bet.query.get(tx.related_bet_id)
                    if bet:
                        bet.payout_transaction_hash = tx.transaction_hash
            
            db.session.commit()
            return len(pending_txs)
            
        except Exception as e:
            logger.error(f"Error processing pending transactions: {e}")
            db.session.rollback()
            return 0
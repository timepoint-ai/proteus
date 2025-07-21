"""
Bet Resolution Service
Handles the proper status workflow for bet resolution
"""

import logging
from datetime import datetime
from decimal import Decimal
from app import db
from models import Bet, Stake, Transaction, OracleSubmission
from sqlalchemy import and_
import uuid

logger = logging.getLogger(__name__)

class BetResolutionService:
    """Service to handle bet resolution with proper status workflow"""
    
    def __init__(self):
        self.platform_fee_percentage = Decimal('0.05')  # 5% platform fee
    
    def check_and_update_expired_bets(self):
        """Check for active bets that have passed their end time and mark as expired"""
        try:
            current_time = datetime.utcnow()
            
            # Find all active bets that have passed their end time
            expired_bets = Bet.query.filter(
                and_(
                    Bet.status == 'active',
                    Bet.end_time < current_time
                )
            ).all()
            
            for bet in expired_bets:
                bet.status = 'expired'
                logger.info(f"Bet {bet.id} marked as expired")
            
            db.session.commit()
            return len(expired_bets)
            
        except Exception as e:
            logger.error(f"Error updating expired bets: {e}")
            db.session.rollback()
            return 0
    
    def process_oracle_submission(self, bet_id, oracle_submission):
        """Process an oracle submission and update bet status"""
        try:
            bet = Bet.query.get(bet_id)
            if not bet:
                logger.error(f"Bet {bet_id} not found")
                return False
            
            # Update bet status to validating if it's the first oracle submission
            if bet.status == 'expired':
                bet.status = 'validating'
                db.session.commit()
                logger.info(f"Bet {bet_id} moved to validating status")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing oracle submission: {e}")
            db.session.rollback()
            return False
    
    def resolve_bet(self, bet_id, winning_text, levenshtein_distance):
        """
        Resolve a bet with proper status transitions
        1. Mark bet as resolved
        2. Mark all stakes as won/lost
        3. Create payout transactions for winners
        4. Create platform fee transaction
        """
        try:
            bet = Bet.query.get(bet_id)
            if not bet:
                logger.error(f"Bet {bet_id} not found")
                return False
            
            if bet.status != 'validating':
                logger.error(f"Bet {bet_id} not in validating status, cannot resolve")
                return False
            
            # Update bet resolution details
            bet.status = 'resolved'
            bet.resolution_text = winning_text
            bet.levenshtein_distance = levenshtein_distance
            bet.resolution_time = datetime.utcnow()
            
            # Get all confirmed stakes for this bet
            stakes = Stake.query.filter_by(bet_id=bet_id, status='confirmed').all()
            
            if not stakes:
                logger.warning(f"No confirmed stakes found for bet {bet_id}")
                db.session.commit()
                return True
            
            # Calculate total pool and platform fee
            total_pool = sum(Decimal(str(stake.amount)) for stake in stakes)
            platform_fee = total_pool * self.platform_fee_percentage
            distributable_pool = total_pool - platform_fee
            
            # Determine winners (for now, assuming all stakes are "for" the prediction)
            # In a real system, you'd compare with competing bets
            winning_stakes = [s for s in stakes if s.position == 'for']
            losing_stakes = [s for s in stakes if s.position == 'against']
            
            # If no winners, platform keeps all
            if not winning_stakes:
                for stake in stakes:
                    stake.status = 'lost'
            else:
                # Calculate payouts for winners
                total_winning_amount = sum(Decimal(str(s.amount)) for s in winning_stakes)
                
                for stake in winning_stakes:
                    stake.status = 'won'
                    # Calculate proportional payout
                    stake_proportion = Decimal(str(stake.amount)) / total_winning_amount
                    stake.payout_amount = stake.amount + (distributable_pool * stake_proportion)
                    
                    # Create payout transaction
                    payout_tx = Transaction()
                    payout_tx.transaction_hash = f"payout_{uuid.uuid4().hex[:16]}"
                    payout_tx.from_address = "platform_pool"
                    payout_tx.to_address = stake.staker_wallet
                    payout_tx.amount = stake.payout_amount
                    payout_tx.currency = stake.currency
                    payout_tx.transaction_type = 'payout'
                    payout_tx.related_bet_id = bet_id
                    payout_tx.status = 'confirmed'  # In production, this would start as pending
                    payout_tx.created_at = datetime.utcnow()
                    db.session.add(payout_tx)
                    stake.payout_transaction_hash = payout_tx.transaction_hash
                
                # Mark losing stakes
                for stake in losing_stakes:
                    stake.status = 'lost'
            
            # Create platform fee transaction
            if platform_fee > 0:
                fee_tx = Transaction()
                fee_tx.transaction_hash = f"fee_{uuid.uuid4().hex[:16]}"
                fee_tx.from_address = "platform_pool"
                fee_tx.to_address = "platform_treasury"
                fee_tx.amount = platform_fee
                fee_tx.currency = bet.currency
                fee_tx.transaction_type = 'fee'
                fee_tx.related_bet_id = bet_id
                fee_tx.platform_fee = platform_fee
                fee_tx.status = 'confirmed'  # In production, this would start as pending
                fee_tx.created_at = datetime.utcnow()
                db.session.add(fee_tx)
            
            # Update oracle submission status
            oracle_submissions = OracleSubmission.query.filter_by(
                bet_id=bet_id,
                is_consensus=True
            ).all()
            
            for submission in oracle_submissions:
                submission.status = 'consensus'
            
            db.session.commit()
            logger.info(f"Successfully resolved bet {bet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving bet: {e}")
            db.session.rollback()
            return False
    
    def cancel_bet(self, bet_id, reason="Admin cancellation"):
        """
        Cancel a bet and refund all stakes
        """
        try:
            bet = Bet.query.get(bet_id)
            if not bet:
                logger.error(f"Bet {bet_id} not found")
                return False
            
            if bet.status == 'resolved':
                logger.error(f"Cannot cancel resolved bet {bet_id}")
                return False
            
            bet.status = 'cancelled'
            
            # Refund all confirmed stakes
            stakes = Stake.query.filter_by(bet_id=bet_id, status='confirmed').all()
            
            for stake in stakes:
                stake.status = 'refunded'
                
                # Create refund transaction
                refund_tx = Transaction()
                refund_tx.transaction_hash = f"refund_{uuid.uuid4().hex[:16]}"
                refund_tx.from_address = "platform_pool"
                refund_tx.to_address = stake.staker_wallet
                refund_tx.amount = stake.amount
                refund_tx.currency = stake.currency
                refund_tx.transaction_type = 'refund'
                refund_tx.related_bet_id = bet_id
                refund_tx.status = 'confirmed'  # In production, this would start as pending
                refund_tx.created_at = datetime.utcnow()
                db.session.add(refund_tx)
            
            db.session.commit()
            logger.info(f"Successfully cancelled bet {bet_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling bet: {e}")
            db.session.rollback()
            return False
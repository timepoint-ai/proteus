import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
# from app import db  # Phase 7: Database removed
# from models import PredictionMarket, Submission, OracleSubmission, OracleVote, NodeOperator, Bet  # Phase 7: Models removed
from utils.crypto import CryptoUtils
from services.node_communication import NodeCommunicationService
from services.text_analysis import TextAnalysisService
from config import Config

logger = logging.getLogger(__name__)

class OracleService:
    def __init__(self):
        self.crypto_utils = CryptoUtils()
        self.node_comm = NodeCommunicationService()
        self.text_analysis = TextAnalysisService()
        
    def submit_oracle_statement(self, market_id: str, oracle_wallet: str, submitted_text: Optional[str], signature: str) -> bool:
        """Submit an oracle statement for a prediction market"""
        try:
            # Get the market
    # market = PredictionMarket.query.get(market_id)  # Phase 7: Database removed
            if not market:
                logger.error(f"PredictionMarket {market_id} not found")
                return False
                
            # Check if market is expired (not yet validating)
            if market.status != 'expired':
                logger.error(f"PredictionMarket {market_id} is not ready for oracle validation (status: {market.status})")
                return False
                
            # CRITICAL: Check if market's end time has passed
            current_time = datetime.now(timezone.utc)
            if current_time < market.end_time:
                logger.error(f"Cannot submit oracle statement for market {market_id} before end time: {market.end_time}")
                return False
                
            # Check if oracle wallet is authorized
            oracle_wallets = json.loads(market.oracle_wallets)
            if oracle_wallet not in oracle_wallets:
                logger.error(f"Oracle wallet {oracle_wallet} not authorized for market {market_id}")
                return False
                
            # Check if oracle has already submitted
    # existing_submission = OracleSubmission.query.filter_by(  # Phase 7: Database removed
                market_id=market_id,
                oracle_wallet=oracle_wallet
    # ).first()  # Phase 7: Database removed
            
            if existing_submission:
                logger.warning(f"Oracle {oracle_wallet} already submitted for market {market_id}")
                return False
                
            # Verify signature
            message = f"{market_id}:{submitted_text if submitted_text else 'null'}"
            if not self.crypto_utils.verify_signature(message, signature, oracle_wallet):
                logger.error(f"Invalid signature from oracle {oracle_wallet}")
                return False
                
            # Create submission (submitted_text can be None for null oracle)
            submission = OracleSubmission(
                market_id=market_id,
                oracle_wallet=oracle_wallet,
                submitted_text=submitted_text,
                signature=signature
            )
            
    # db.session.add(submission)  # Phase 7: Database removed
            
            # Update market status to validating
            market.status = 'validating'
            
            # Broadcast to network
            self.node_comm.broadcast_oracle_submission({
                'market_id': market_id,
                'oracle_wallet': oracle_wallet,
                'submitted_text': submitted_text,
                'signature': signature,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
    # db.session.commit()  # Phase 7: Database removed
            logger.info(f"Oracle submission created for market {market_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting oracle statement: {e}")
    # db.session.rollback()  # Phase 7: Database removed
            return False
            
    def vote_on_oracle_submission(self, submission_id: str, voter_wallet: str, vote: str, signature: str) -> bool:
        """Vote on an oracle submission"""
        try:
            # Validate vote
            if vote not in ['for', 'against']:
                logger.error(f"Invalid vote: {vote}")
                return False
                
            # Get submission
    # submission = OracleSubmission.query.get(submission_id)  # Phase 7: Database removed
            if not submission:
                logger.error(f"Oracle submission {submission_id} not found")
                return False
                
            # Check if already voted
    # existing_vote = OracleVote.query.filter_by(  # Phase 7: Database removed
                submission_id=submission_id,
                voter_wallet=voter_wallet
    # ).first()  # Phase 7: Database removed
            
            if existing_vote:
                logger.warning(f"Voter {voter_wallet} already voted on submission {submission_id}")
                return False
                
            # Verify signature
            message = f"{submission_id}:{vote}"
            if not self.crypto_utils.verify_signature(message, signature, voter_wallet):
                logger.error(f"Invalid signature from voter {voter_wallet}")
                return False
                
            # Create vote
            oracle_vote = OracleVote(
                submission_id=submission_id,
                voter_wallet=voter_wallet,
                vote=vote,
                signature=signature
            )
            
    # db.session.add(oracle_vote)  # Phase 7: Database removed
            
            # Update vote counts
            if vote == 'for':
                submission.votes_for += 1
            else:
                submission.votes_against += 1
                
            # Check if consensus reached
            total_votes = submission.votes_for + submission.votes_against
            if total_votes >= Config.MIN_ORACLE_VOTES:
                consensus_ratio = submission.votes_for / total_votes
                if consensus_ratio >= Config.CONSENSUS_THRESHOLD:
                    submission.is_consensus = True
                    submission.status = 'consensus'
                    # Trigger market resolution
                    self._resolve_market_with_oracle(submission.market, submission.submitted_text)
                    
    # db.session.commit()  # Phase 7: Database removed
            logger.info(f"Oracle vote recorded: {voter_wallet} voted {vote} on submission {submission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error voting on oracle submission: {e}")
    # db.session.rollback()  # Phase 7: Database removed
            return False
            
    def get_oracle_submissions(self, market_id: str) -> List[Dict[str, Any]]:
        """Get all oracle submissions for a market"""
        try:
    # submissions = OracleSubmission.query.filter_by(market_id=market_id).all()  # Phase 7: Database removed
            
            result = []
            for submission in submissions:
                result.append({
                    'id': str(submission.id),
                    'oracle_wallet': submission.oracle_wallet,
                    'submitted_text': submission.submitted_text,
                    'votes_for': submission.votes_for,
                    'votes_against': submission.votes_against,
                    'is_consensus': submission.is_consensus,
                    'status': submission.status,
                    'created_at': submission.created_at.isoformat()
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting oracle submissions: {e}")
            return []
            
    def finalize_oracle_voting(self, market_id: str):
        """Finalize oracle voting for a market"""
        try:
    # market = PredictionMarket.query.get(market_id)  # Phase 7: Database removed
            if not market or market.status != 'validating':
                logger.error(f"Market {market_id} not in validating state")
                return
                
            # Get all submissions
    # submissions = OracleSubmission.query.filter_by(market_id=market_id).all()  # Phase 7: Database removed
            
            if not submissions:
                logger.warning(f"No oracle submissions for market {market_id}")
                # Market stays in validating state
                return
                
            # Find submission with highest consensus
            best_submission = None
            highest_consensus = 0
            
            for submission in submissions:
                total_votes = submission.votes_for + submission.votes_against
                if total_votes > 0:
                    consensus_ratio = submission.votes_for / total_votes
                    if consensus_ratio > highest_consensus:
                        highest_consensus = consensus_ratio
                        best_submission = submission
                        
            if best_submission and highest_consensus >= Config.CONSENSUS_THRESHOLD:
                # Mark as consensus
                best_submission.is_consensus = True
                best_submission.status = 'consensus'
                
                # Resolve the market
                self._resolve_market_with_oracle(market, best_submission.submitted_text)
                
                logger.info(f"Oracle consensus reached for market {market_id}")
            else:
                logger.warning(f"No oracle consensus reached for market {market_id}")
                # Market stays in validating state
                
    # db.session.commit()  # Phase 7: Database removed
            
        except Exception as e:
            logger.error(f"Error finalizing oracle voting: {e}")
    # db.session.rollback()  # Phase 7: Database removed
            
    def _resolve_market_with_oracle(self, market: Any, oracle_text: Optional[str]):
        """Resolve a market using oracle text"""
        try:
            # Update market with resolution text
            market.resolution_text = oracle_text
            market.resolution_time = datetime.now(timezone.utc)
            
            # If oracle_text is None (null oracle), no submission wins
            if oracle_text is None:
                market.status = 'resolved'
                market.winning_submission_id = None
                self._process_market_refunds(market)
                logger.info(f"Market {market.id} resolved with null oracle - all bets refunded")
                return
            
            # Calculate Levenshtein distances for all submissions
    # submissions = Submission.query.filter_by(market_id=market.id).all()  # Phase 7: Database removed
            
            best_submission = None
            lowest_distance = float('inf')
            
            for submission in submissions:
                # Skip null submissions when oracle has text
                if submission.predicted_text is None:
                    continue
                    
                distance = self.text_analysis.calculate_levenshtein_distance(
                    submission.predicted_text,
                    oracle_text
                )
                
                submission.levenshtein_distance = distance
                
                if distance < lowest_distance:
                    lowest_distance = distance
                    best_submission = submission
            
            # Mark winner
            if best_submission:
                best_submission.is_winner = True
                market.winning_submission_id = best_submission.id
                market.status = 'resolved'
                
                # Process payouts
                self._process_market_payouts(market, best_submission)
                
                logger.info(f"Market {market.id} resolved - winning submission: {best_submission.id} with distance {lowest_distance}")
            else:
                # No valid submissions (all were null)
                market.status = 'resolved'
                market.winning_submission_id = None
                self._process_market_refunds(market)
                logger.info(f"Market {market.id} resolved with no valid submissions - all bets refunded")
            
        except Exception as e:
            logger.error(f"Error resolving market with oracle: {e}")
            
    def _process_market_payouts(self, market: Any, winning_submission: Any):
        """Process payouts for a resolved market"""
        try:
            from services.blockchain import BlockchainService
            blockchain_service = BlockchainService()
            
            # Get all bets on the winning submission
    # winning_bets = Bet.query.filter_by(submission_id=winning_submission.id).all()  # Phase 7: Database removed
            
            # Calculate total pot (all bets on all submissions)
    # all_bets = Bet.query.join(Submission).filter(Submission.market_id == market.id).all()  # Phase 7: Database removed
            total_pot = sum(bet.amount for bet in all_bets if bet.status == 'confirmed')
            
            # Calculate total winning bets
            total_winning_amount = sum(bet.amount for bet in winning_bets if bet.status == 'confirmed')
            
            if total_winning_amount > 0:
                # Calculate payout ratio
                payout_ratio = total_pot / total_winning_amount
                
                # Process each winning bet
                for bet in winning_bets:
                    if bet.status == 'confirmed':
                        payout_amount = bet.amount * payout_ratio
                        bet.payout_amount = payout_amount
                        bet.status = 'won'
                        
                        # TODO: Process actual blockchain payout
                        # bet.payout_transaction_hash = blockchain_service.send_payout(...)
                        
                        logger.info(f"Bet {bet.id} won - payout: {payout_amount}")
            
            # Mark all losing bets
    # losing_bets = Bet.query.join(Submission).filter(  # Phase 7: Database removed
                Submission.market_id == market.id,
                Submission.id != winning_submission.id
    # ).all()  # Phase 7: Database removed
            
            for bet in losing_bets:
                if bet.status == 'confirmed':
                    bet.status = 'lost'
                    logger.info(f"Bet {bet.id} lost")
                    
        except Exception as e:
            logger.error(f"Error processing market payouts: {e}")
            
    def _process_market_refunds(self, market: Any):
        """Process refunds for a market (null oracle or no valid submissions)"""
        try:
            # Get all bets for this market
    # all_bets = Bet.query.join(Submission).filter(Submission.market_id == market.id).all()  # Phase 7: Database removed
            
            for bet in all_bets:
                if bet.status == 'confirmed':
                    bet.status = 'refunded'
                    bet.payout_amount = bet.amount  # Full refund
                    
                    # TODO: Process actual blockchain refund
                    # bet.payout_transaction_hash = blockchain_service.send_refund(...)
                    
                    logger.info(f"Bet {bet.id} refunded - amount: {bet.amount}")
                    
        except Exception as e:
            logger.error(f"Error processing market refunds: {e}")
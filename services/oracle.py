import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app import db
from models import Bet, OracleSubmission, OracleVote, NodeOperator
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
        
    def submit_oracle_statement(self, bet_id: str, oracle_wallet: str, submitted_text: str, signature: str) -> bool:
        """Submit an oracle statement for a bet"""
        try:
            # Get the bet
            bet = Bet.query.get(bet_id)
            if not bet:
                logger.error(f"Bet {bet_id} not found")
                return False
                
            # Check if bet is still active
            if bet.status != 'active':
                logger.error(f"Bet {bet_id} is not active")
                return False
                
            # CRITICAL: Check if bet's end time has passed
            current_time = datetime.utcnow()
            if current_time < bet.end_time:
                logger.error(f"Cannot submit oracle statement for bet {bet_id} before end time: {bet.end_time}")
                return False
                
            # Check if oracle wallet is authorized
            oracle_wallets = json.loads(bet.oracle_wallets)
            if oracle_wallet not in oracle_wallets:
                logger.error(f"Oracle wallet {oracle_wallet} not authorized for bet {bet_id}")
                return False
                
            # Check if oracle has already submitted
            existing_submission = OracleSubmission.query.filter_by(
                bet_id=bet_id,
                oracle_wallet=oracle_wallet
            ).first()
            
            if existing_submission:
                logger.warning(f"Oracle {oracle_wallet} already submitted for bet {bet_id}")
                return False
                
            # Verify signature
            message = f"{bet_id}:{submitted_text}"
            if not self.crypto_utils.verify_signature(message, signature, oracle_wallet):
                logger.error(f"Invalid signature from oracle {oracle_wallet}")
                return False
                
            # Create submission
            submission = OracleSubmission(
                bet_id=bet_id,
                oracle_wallet=oracle_wallet,
                submitted_text=submitted_text,
                signature=signature
            )
            
            db.session.add(submission)
            db.session.commit()
            
            # Broadcast submission to network
            submission_data = {
                'type': 'oracle_submission',
                'bet_id': bet_id,
                'oracle_wallet': oracle_wallet,
                'submitted_text': submitted_text,
                'signature': signature,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.node_comm.broadcast_message(submission_data)
            
            logger.info(f"Oracle submission recorded: {oracle_wallet} -> {bet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting oracle statement: {e}")
            db.session.rollback()
            return False
            
    def vote_on_oracle_submission(self, submission_id: str, voter_wallet: str, vote: str, signature: str) -> bool:
        """Vote on an oracle submission"""
        try:
            # Validate vote
            if vote not in ['for', 'against']:
                logger.error(f"Invalid vote: {vote}")
                return False
                
            # Get submission
            submission = OracleSubmission.query.get(submission_id)
            if not submission:
                logger.error(f"Oracle submission {submission_id} not found")
                return False
                
            # Get the bet
            bet = Bet.query.get(submission.bet_id)
            if not bet:
                logger.error(f"Bet {submission.bet_id} not found")
                return False
                
            # Check if voter is authorized (oracle wallet)
            oracle_wallets = json.loads(bet.oracle_wallets)
            if voter_wallet not in oracle_wallets:
                logger.error(f"Voter {voter_wallet} not authorized")
                return False
                
            # Check if already voted
            existing_vote = OracleVote.query.filter_by(
                submission_id=submission_id,
                voter_wallet=voter_wallet
            ).first()
            
            if existing_vote:
                logger.warning(f"Voter {voter_wallet} already voted on submission {submission_id}")
                return False
                
            # Verify signature
            message = f"{submission_id}:{vote}"
            if not self.crypto_utils.verify_signature(message, signature, voter_wallet):
                logger.error(f"Invalid signature from voter {voter_wallet}")
                return False
                
            # Create vote
            vote_record = OracleVote(
                submission_id=submission_id,
                voter_wallet=voter_wallet,
                vote=vote,
                signature=signature
            )
            
            db.session.add(vote_record)
            
            # Update vote counts
            if vote == 'for':
                submission.votes_for += 1
            else:
                submission.votes_against += 1
                
            db.session.commit()
            
            # Check if voting period expired or consensus reached
            self._check_voting_completion(submission_id)
            
            logger.info(f"Oracle vote recorded: {voter_wallet} -> {vote} for submission {submission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error voting on oracle submission: {e}")
            db.session.rollback()
            return False
            
    def _check_voting_completion(self, submission_id: str):
        """Check if voting is complete for a submission"""
        try:
            submission = OracleSubmission.query.get(submission_id)
            if not submission:
                return
                
            bet = Bet.query.get(submission.bet_id)
            if not bet:
                return
                
            # Check if voting timeout reached
            voting_deadline = submission.created_at + timedelta(seconds=Config.ORACLE_VOTE_TIMEOUT)
            if datetime.utcnow() > voting_deadline:
                self._finalize_oracle_voting(bet.id)
                return
                
            # Check if all oracles have voted
            oracle_wallets = json.loads(bet.oracle_wallets)
            total_votes = submission.votes_for + submission.votes_against
            
            if total_votes >= len(oracle_wallets):
                self._finalize_oracle_voting(bet.id)
                
        except Exception as e:
            logger.error(f"Error checking voting completion: {e}")
            
    def _finalize_oracle_voting(self, bet_id: str):
        """Finalize oracle voting for a bet"""
        try:
            bet = Bet.query.get(bet_id)
            if not bet or bet.status != 'active':
                return
                
            # CRITICAL: Ensure bet's end time has passed
            current_time = datetime.utcnow()
            if current_time < bet.end_time:
                logger.error(f"Cannot finalize oracle voting for bet {bet_id} before end time: {bet.end_time}")
                return
                
            # Get all submissions for this bet
            submissions = OracleSubmission.query.filter_by(bet_id=bet_id).all()
            
            if not submissions:
                logger.warning(f"No oracle submissions for bet {bet_id}")
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
                
                # Resolve the bet
                self._resolve_bet_with_oracle(bet, best_submission.submitted_text)
                
                logger.info(f"Oracle consensus reached for bet {bet_id}: {best_submission.submitted_text}")
            else:
                logger.warning(f"No oracle consensus reached for bet {bet_id}")
                # Could implement fallback logic here
                
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error finalizing oracle voting: {e}")
            db.session.rollback()
            
    def _resolve_bet_with_oracle(self, bet: Bet, oracle_text: str):
        """Resolve a bet using oracle text"""
        try:
            # Calculate Levenshtein distance
            distance = self.text_analysis.calculate_levenshtein_distance(
                bet.predicted_text,
                oracle_text
            )
            
            # Calculate similarity percentage
            max_len = max(len(bet.predicted_text), len(oracle_text))
            similarity = 1 - (distance / max_len) if max_len > 0 else 1
            
            # Update bet with resolution
            bet.status = 'resolved'
            bet.resolution_text = oracle_text
            bet.levenshtein_distance = distance
            bet.resolution_time = datetime.utcnow()
            
            # Determine if bet was successful (based on similarity threshold)
            bet_successful = similarity >= Config.LEVENSHTEIN_THRESHOLD
            
            # Process payouts
            self._process_bet_payouts(bet, bet_successful)
            
            logger.info(f"Bet {bet.id} resolved with similarity {similarity:.2%}")
            
        except Exception as e:
            logger.error(f"Error resolving bet with oracle: {e}")
            
    def _process_bet_payouts(self, bet: Bet, bet_successful: bool):
        """Process payouts for a resolved bet"""
        try:
            from models import Stake
            from services.blockchain import BlockchainService
            
            blockchain_service = BlockchainService()
            
            # Get all stakes for this bet
            stakes = Stake.query.filter_by(bet_id=bet.id).all()
            
            if not stakes:
                logger.info(f"No stakes found for bet {bet.id}")
                return
                
            # Calculate total amounts for each position
            total_for = sum(s.amount for s in stakes if s.position == 'for')
            total_against = sum(s.amount for s in stakes if s.position == 'against')
            total_pool = total_for + total_against
            
            # Determine winning and losing positions
            if bet_successful:
                winning_position = 'for'
                winning_pool = total_for
                losing_pool = total_against
            else:
                winning_position = 'against'
                winning_pool = total_against
                losing_pool = total_for
                
            # Calculate platform fee
            platform_fee = blockchain_service.calculate_platform_fee(total_pool)
            payout_pool = total_pool - platform_fee
            
            # Process payouts for winners
            if winning_pool > 0:
                for stake in stakes:
                    if stake.position == winning_position:
                        # Calculate proportional payout
                        proportion = stake.amount / winning_pool
                        payout = proportion * payout_pool
                        
                        # Update stake with payout
                        stake.payout_amount = payout
                        
                        # Note: In a real implementation, you would send the actual payout transaction
                        # stake.payout_transaction_hash = blockchain_service.send_payout(stake.staker_wallet, payout, stake.currency)
                        
                        logger.info(f"Payout calculated for stake {stake.id}: {payout} {stake.currency}")
                        
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing bet payouts: {e}")
            db.session.rollback()
            
    def get_oracle_status(self, bet_id: str) -> Dict[str, Any]:
        """Get oracle status for a bet"""
        try:
            bet = Bet.query.get(bet_id)
            if not bet:
                return {'error': 'Bet not found'}
                
            oracle_wallets = json.loads(bet.oracle_wallets)
            submissions = OracleSubmission.query.filter_by(bet_id=bet_id).all()
            
            # Group submissions by oracle
            oracle_status = {}
            for wallet in oracle_wallets:
                submission = next((s for s in submissions if s.oracle_wallet == wallet), None)
                if submission:
                    oracle_status[wallet] = {
                        'submitted': True,
                        'text': submission.submitted_text,
                        'votes_for': submission.votes_for,
                        'votes_against': submission.votes_against,
                        'is_consensus': submission.is_consensus
                    }
                else:
                    oracle_status[wallet] = {
                        'submitted': False,
                        'text': None,
                        'votes_for': 0,
                        'votes_against': 0,
                        'is_consensus': False
                    }
                    
            return {
                'bet_id': bet_id,
                'oracle_wallets': oracle_wallets,
                'oracle_status': oracle_status,
                'total_submissions': len(submissions),
                'voting_deadline': (bet.created_at + timedelta(seconds=Config.ORACLE_VOTE_TIMEOUT)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting oracle status: {e}")
            return {'error': 'Internal server error'}
            
    def cleanup_expired_votes(self):
        """Clean up expired oracle votes"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=Config.ORACLE_VOTE_TIMEOUT)
            
            # Find bets with expired voting
            expired_bets = db.session.query(Bet).join(OracleSubmission).filter(
                Bet.status == 'active',
                OracleSubmission.created_at < cutoff_time
            ).all()
            
            for bet in expired_bets:
                self._finalize_oracle_voting(bet.id)
                
            logger.info(f"Cleaned up {len(expired_bets)} expired oracle votes")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired votes: {e}")

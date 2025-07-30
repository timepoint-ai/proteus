import logging
import json
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from app import db
from models import PredictionMarket, Submission, OracleSubmission, OracleVote, NodeOperator, Bet
from utils.crypto import CryptoUtils
from services.node_communication import NodeCommunicationService
from services.text_analysis import TextAnalysisService
from services.blockchain_base import BaseBlockchainService
from config import Config
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

class XcomOracleService:
    """Oracle service with X.com integration for BASE blockchain"""
    
    def __init__(self):
        self.crypto_utils = CryptoUtils()
        self.node_comm = NodeCommunicationService()
        self.text_analysis = TextAnalysisService()
        self.blockchain = BaseBlockchainService()
        self.consensus_threshold = 0.66  # 66% consensus required
        
    def submit_oracle_statement(self, market_id: str, oracle_wallet: str, 
                              actual_text: str, tweet_id: str, 
                              screenshot_base64: str, signature: str) -> bool:
        """Submit an oracle statement with X.com verification for a prediction market"""
        try:
            # Get the market
            market = PredictionMarket.query.get(market_id)
            if not market:
                logger.error(f"PredictionMarket {market_id} not found")
                return False
                
            # Check if market is expired (not yet validating)
            if market.status != 'expired':
                logger.error(f"PredictionMarket {market_id} is not ready for oracle validation (status: {market.status})")
                return False
                
            # CRITICAL: Check if market's end time has passed
            current_time = datetime.utcnow()
            if current_time < market.end_time:
                logger.error(f"Cannot submit oracle statement for market {market_id} before end time: {market.end_time}")
                return False
                
            # Check if oracle wallet is authorized
            oracle_wallets = json.loads(market.oracle_wallets)
            if oracle_wallet not in oracle_wallets:
                logger.error(f"Oracle wallet {oracle_wallet} not authorized for market {market_id}")
                return False
                
            # Check if oracle has already submitted
            existing_submission = OracleSubmission.query.filter_by(
                market_id=market_id,
                oracle_wallet=oracle_wallet
            ).first()
            
            if existing_submission:
                logger.warning(f"Oracle {oracle_wallet} already submitted for market {market_id}")
                return False
                
            # Verify signature
            message = f"{market_id}:{actual_text}:{tweet_id}"
            if not self.crypto_utils.verify_signature(message, signature, oracle_wallet):
                logger.error(f"Invalid signature from oracle {oracle_wallet}")
                return False
                
            # Validate X.com requirement
            if market.xcom_only and not self._verify_xcom_tweet(tweet_id, market.twitter_handle):
                logger.error(f"Tweet {tweet_id} verification failed for handle {market.twitter_handle}")
                return False
                
            # Calculate screenshot hash
            screenshot_hash = hashlib.sha256(screenshot_base64.encode()).hexdigest()
            
            # Create submission with X.com data
            submission = OracleSubmission(
                market_id=market_id,
                oracle_wallet=oracle_wallet,
                submitted_text=actual_text,
                signature=signature,
                tweet_id=tweet_id,
                tweet_verification=json.dumps({
                    'tweet_id': tweet_id,
                    'verified_at': datetime.utcnow().isoformat(),
                    'handle': market.twitter_handle
                }),
                screenshot_proof=screenshot_base64,
                screenshot_hash=screenshot_hash,
                tweet_timestamp=datetime.utcnow()  # Would be fetched from X.com API
            )
            
            db.session.add(submission)
            
            # Update market status to validating
            market.status = 'validating'
            
            # Broadcast to network
            self.node_comm.broadcast_oracle_submission({
                'market_id': market_id,
                'oracle_wallet': oracle_wallet,
                'submitted_text': actual_text,
                'tweet_id': tweet_id,
                'screenshot_hash': screenshot_hash,
                'signature': signature,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            db.session.commit()
            logger.info(f"Oracle submission created for market {market_id} with X.com verification")
            
            # Check if we can auto-resolve based on consensus
            self._check_consensus_and_resolve(market_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting oracle statement: {e}")
            db.session.rollback()
            return False
            
    def _verify_xcom_tweet(self, tweet_id: str, expected_handle: str) -> bool:
        """Verify X.com tweet exists and is from expected handle"""
        # In production, this would call X.com API
        # For now, we'll do basic validation
        try:
            if not tweet_id or not tweet_id.isdigit():
                return False
                
            # Would verify against X.com API that:
            # 1. Tweet exists
            # 2. Tweet is from expected_handle
            # 3. Tweet is public
            # 4. Tweet timestamp is within market window
            
            logger.info(f"X.com verification placeholder for tweet {tweet_id} from {expected_handle}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying X.com tweet: {e}")
            return False
            
    def capture_xcom_screenshot(self, tweet_url: str) -> Optional[str]:
        """Capture screenshot of X.com post and return base64 encoded string"""
        try:
            # In production, this would use Puppeteer or similar to capture screenshot
            # For now, return placeholder
            logger.info(f"Screenshot capture placeholder for {tweet_url}")
            
            # Placeholder screenshot generation
            placeholder_data = f"Screenshot of {tweet_url} captured at {datetime.utcnow().isoformat()}"
            encoded = base64.b64encode(placeholder_data.encode()).decode()
            
            return encoded
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
            
    def vote_on_oracle_submission(self, submission_id: str, voter_wallet: str, 
                                 vote: str, signature: str) -> bool:
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
            oracle_vote = OracleVote(
                submission_id=submission_id,
                voter_wallet=voter_wallet,
                vote=vote,
                signature=signature
            )
            
            db.session.add(oracle_vote)
            
            # Update vote counts
            if vote == 'for':
                submission.votes_for += 1
            else:
                submission.votes_against += 1
                
            db.session.commit()
            
            # Check if consensus reached
            self._check_consensus_and_resolve(submission.market_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error voting on oracle submission: {e}")
            db.session.rollback()
            return False
            
    def _check_consensus_and_resolve(self, market_id: str) -> bool:
        """Check if oracle consensus is reached and resolve market"""
        try:
            market = PredictionMarket.query.get(market_id)
            if not market or market.status == 'resolved':
                return False
                
            # Get all oracle submissions
            submissions = OracleSubmission.query.filter_by(market_id=market_id).all()
            
            # Need at least 3 oracle submissions
            if len(submissions) < 3:
                return False
                
            # Check each submission for consensus
            for submission in submissions:
                total_votes = submission.votes_for + submission.votes_against
                if total_votes >= 3:  # Minimum votes
                    consensus_ratio = submission.votes_for / total_votes
                    if consensus_ratio >= self.consensus_threshold:
                        submission.is_consensus = True
                        submission.status = 'consensus'
                        
                        # Resolve the market
                        return self._resolve_market_with_oracle(market, submission)
                        
            return False
            
        except Exception as e:
            logger.error(f"Error checking consensus: {e}")
            return False
            
    def _resolve_market_with_oracle(self, market: PredictionMarket, 
                                   oracle_submission: OracleSubmission) -> bool:
        """Resolve market based on oracle consensus"""
        try:
            # Get all submissions for this market
            submissions = Submission.query.filter_by(market_id=market.id).all()
            
            if not submissions:
                logger.error(f"No submissions found for market {market.id}")
                return False
                
            # Calculate Levenshtein distances
            actual_text = oracle_submission.submitted_text
            min_distance = float('inf')
            winning_submission = None
            
            for submission in submissions:
                if submission.predicted_text:
                    distance = self.text_analysis.calculate_levenshtein_distance(
                        submission.predicted_text,
                        actual_text
                    )
                    submission.levenshtein_distance = distance
                    
                    if distance < min_distance:
                        min_distance = distance
                        winning_submission = submission
                        
            if winning_submission:
                # Mark winner
                winning_submission.is_winner = True
                market.winning_submission_id = winning_submission.id
                market.status = 'resolved'
                market.resolution_text = actual_text
                market.resolution_time = datetime.utcnow()
                
                # Update bet statuses
                self._update_bet_statuses(market.id, winning_submission.id)
                
                # Broadcast resolution
                self.node_comm.broadcast_market_resolution({
                    'market_id': str(market.id),
                    'winning_submission_id': str(winning_submission.id),
                    'resolution_text': actual_text,
                    'oracle_submission_id': str(oracle_submission.id),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                db.session.commit()
                logger.info(f"Market {market.id} resolved with winner {winning_submission.id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error resolving market: {e}")
            db.session.rollback()
            return False
            
    def _update_bet_statuses(self, market_id: str, winning_submission_id: str):
        """Update bet statuses based on market resolution"""
        try:
            # Get all bets for this market
            all_submissions = Submission.query.filter_by(market_id=market_id).all()
            
            for submission in all_submissions:
                bets = Bet.query.filter_by(submission_id=submission.id).all()
                
                for bet in bets:
                    if submission.id == winning_submission_id:
                        bet.status = 'won'
                    else:
                        bet.status = 'lost'
                        
        except Exception as e:
            logger.error(f"Error updating bet statuses: {e}")
            
    def get_oracle_statistics(self, oracle_wallet: str) -> Dict[str, Any]:
        """Get statistics for an oracle"""
        try:
            submissions = OracleSubmission.query.filter_by(oracle_wallet=oracle_wallet).all()
            
            total_submissions = len(submissions)
            consensus_reached = sum(1 for s in submissions if s.is_consensus)
            
            total_votes_cast = OracleVote.query.filter_by(voter_wallet=oracle_wallet).count()
            
            return {
                'total_submissions': total_submissions,
                'consensus_reached': consensus_reached,
                'consensus_rate': consensus_reached / total_submissions if total_submissions > 0 else 0,
                'total_votes_cast': total_votes_cast,
                'reputation': self._calculate_oracle_reputation(oracle_wallet)
            }
            
        except Exception as e:
            logger.error(f"Error getting oracle statistics: {e}")
            return {}
            
    def _calculate_oracle_reputation(self, oracle_wallet: str) -> float:
        """Calculate oracle reputation based on performance"""
        try:
            # Base reputation
            reputation = 100.0
            
            # Get oracle submissions
            submissions = OracleSubmission.query.filter_by(oracle_wallet=oracle_wallet).all()
            
            for submission in submissions:
                if submission.is_consensus:
                    reputation += 10  # Bonus for consensus
                else:
                    reputation -= 5   # Penalty for no consensus
                    
            # Cap reputation between 0 and 1000
            return max(0, min(1000, reputation))
            
        except Exception as e:
            logger.error(f"Error calculating oracle reputation: {e}")
            return 100.0
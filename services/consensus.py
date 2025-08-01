import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app import db, redis_client
from models import NodeOperator, NodeVote, Actor, OracleSubmission, OracleVote
from utils.crypto import CryptoUtils
from services.node_communication import NodeCommunicationService
from config import Config

logger = logging.getLogger(__name__)

class ConsensusService:
    def __init__(self):
        self.crypto_utils = CryptoUtils()
        self.node_comm = NodeCommunicationService()
        
    @staticmethod
    def initialize_node():
        """Initialize this node operator if not exists"""
        existing_node = NodeOperator.query.filter_by(
            operator_id=Config.NODE_OPERATOR_ID
        ).first()
        
        if not existing_node:
            node = NodeOperator(
                operator_id=Config.NODE_OPERATOR_ID,
                public_key=Config.NODE_PUBLIC_KEY,
                node_address=f"node-{Config.NODE_OPERATOR_ID}",
                status='active'
            )
            db.session.add(node)
            db.session.commit()
            logger.info(f"Initialized node operator: {Config.NODE_OPERATOR_ID}")
            
    def propose_new_node(self, candidate_id: str, public_key: str, node_address: str) -> bool:
        """Propose a new node for network inclusion"""
        try:
            # Check if node already exists
            existing = NodeOperator.query.filter_by(operator_id=candidate_id).first()
            if existing:
                logger.warning(f"Node {candidate_id} already exists")
                return False
                
            # Create pending node
            candidate = NodeOperator(
                operator_id=candidate_id,
                public_key=public_key,
                node_address=node_address,
                status='pending'
            )
            db.session.add(candidate)
            db.session.commit()
            
            # Broadcast proposal to network
            proposal_data = {
                'type': 'node_proposal',
                'candidate_id': candidate_id,
                'public_key': public_key,
                'node_address': node_address,
                'proposer': Config.NODE_OPERATOR_ID,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.node_comm.broadcast_message(proposal_data)
            logger.info(f"Proposed new node: {candidate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error proposing new node: {e}")
            db.session.rollback()
            return False
            
    def vote_on_node(self, candidate_id: str, vote: str, signature: str) -> bool:
        """Vote on a pending node proposal"""
        try:
            # Validate vote
            if vote not in ['approve', 'reject']:
                logger.error(f"Invalid vote: {vote}")
                return False
                
            # Get voter node
            voter = NodeOperator.query.filter_by(
                operator_id=Config.NODE_OPERATOR_ID
            ).first()
            
            if not voter:
                logger.error("Voter node not found")
                return False
                
            # Get candidate node
            candidate = NodeOperator.query.filter_by(operator_id=candidate_id).first()
            if not candidate:
                logger.error(f"Candidate node {candidate_id} not found")
                return False
                
            # Check if already voted
            existing_vote = NodeVote.query.filter_by(
                voter_id=voter.id,
                candidate_id=candidate.id
            ).first()
            
            if existing_vote:
                logger.warning(f"Node {voter.operator_id} already voted on {candidate_id}")
                return False
                
            # Create vote record
            vote_record = NodeVote(
                voter_id=voter.id,
                candidate_id=candidate.id,
                vote=vote,
                signature=signature
            )
            db.session.add(vote_record)
            db.session.commit()
            
            # Check if consensus reached
            self._check_node_consensus(candidate_id)
            
            logger.info(f"Vote recorded: {voter.operator_id} -> {vote} for {candidate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error voting on node: {e}")
            db.session.rollback()
            return False
            
    def _check_node_consensus(self, candidate_id: str):
        """Check if consensus has been reached for a node proposal"""
        try:
            candidate = NodeOperator.query.filter_by(operator_id=candidate_id).first()
            if not candidate:
                return
                
            # Count votes
            votes = NodeVote.query.filter_by(candidate_id=candidate.id).all()
            approve_votes = sum(1 for v in votes if v.vote == 'approve')
            reject_votes = sum(1 for v in votes if v.vote == 'reject')
            
            # Get total active nodes
            total_active = NodeOperator.query.filter_by(status='active').count()
            
            # Check if majority reached
            required_votes = int(total_active * Config.CONSENSUS_THRESHOLD)
            
            if approve_votes >= required_votes:
                candidate.status = 'active'
                db.session.commit()
                
                # Broadcast approval
                approval_data = {
                    'type': 'node_approved',
                    'candidate_id': candidate_id,
                    'approver': Config.NODE_OPERATOR_ID,
                    'timestamp': datetime.utcnow().isoformat()
                }
                self.node_comm.broadcast_message(approval_data)
                
                logger.info(f"Node {candidate_id} approved by consensus")
                
            elif reject_votes >= required_votes:
                candidate.status = 'rejected'
                db.session.commit()
                
                logger.info(f"Node {candidate_id} rejected by consensus")
                
        except Exception as e:
            logger.error(f"Error checking node consensus: {e}")
            db.session.rollback()
            
    # Actor-related consensus methods removed - actors are now public X accounts, no voting needed
            
    def resolve_oracle_consensus(self, bet_id: str) -> Optional[str]:
        """Resolve oracle consensus for a bet"""
        try:
            # Get all oracle submissions for this bet
            submissions = OracleSubmission.query.filter_by(bet_id=bet_id).all()
            
            if not submissions:
                logger.warning(f"No oracle submissions found for bet {bet_id}")
                return None
                
            # Find submission with highest consensus
            best_submission = None
            highest_consensus = 0
            
            for submission in submissions:
                total_votes = submission.votes_for + submission.votes_against
                if total_votes > 0:
                    consensus_ratio = submission.votes_for / total_votes
                    if consensus_ratio > highest_consensus and consensus_ratio >= Config.CONSENSUS_THRESHOLD:
                        highest_consensus = consensus_ratio
                        best_submission = submission
                        
            if best_submission:
                best_submission.is_consensus = True
                db.session.commit()
                
                logger.info(f"Oracle consensus reached for bet {bet_id}: {best_submission.submitted_text}")
                return best_submission.submitted_text
            else:
                logger.warning(f"No oracle consensus reached for bet {bet_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error resolving oracle consensus: {e}")
            return None
            
    def get_network_health(self) -> Dict[str, Any]:
        """Get current network health metrics"""
        try:
            total_nodes = NodeOperator.query.count()
            active_nodes = NodeOperator.query.filter_by(status='active').count()
            pending_nodes = NodeOperator.query.filter_by(status='pending').count()
            
            # Check last seen times
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            online_nodes = NodeOperator.query.filter(
                NodeOperator.status == 'active',
                NodeOperator.last_seen > cutoff_time
            ).count()
            
            return {
                'total_nodes': total_nodes,
                'active_nodes': active_nodes,
                'pending_nodes': pending_nodes,
                'online_nodes': online_nodes,
                'network_health': online_nodes / max(active_nodes, 1),
                'consensus_threshold': Config.CONSENSUS_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Error getting network health: {e}")
            return {
                'total_nodes': 0,
                'active_nodes': 0,
                'pending_nodes': 0,
                'online_nodes': 0,
                'network_health': 0.0,
                'consensus_threshold': Config.CONSENSUS_THRESHOLD
            }

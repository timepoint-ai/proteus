import logging
from datetime import datetime, timedelta, timezone
from app import celery

# Chain-only mode: db and models may not be available
# Legacy V1 services are optional
LEGACY_AVAILABLE = False
try:
    from models import NodeOperator, Actor, OracleSubmission, Bet
    from services.consensus import ConsensusService
    from services.oracle import OracleService
    from services.node_communication import NodeCommunicationService
    LEGACY_AVAILABLE = True
except ImportError:
    NodeOperator = None
    Actor = None
    OracleSubmission = None
    Bet = None
    ConsensusService = None
    OracleService = None
    NodeCommunicationService = None

from config import Config

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def process_node_proposal(self, candidate_id, public_key, node_address, proposer_id):
    """
    Process a node proposal from another node
    """
    try:
        consensus_service = ConsensusService()
        
        # Propose the node
        success = consensus_service.propose_new_node(
            candidate_id=candidate_id,
            public_key=public_key,
            node_address=node_address
        )
        
        if success:
            logger.info(f"Node proposal processed: {candidate_id}")
            return {
                'status': 'success',
                'candidate_id': candidate_id,
                'proposer_id': proposer_id,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error(f"Failed to process node proposal: {candidate_id}")
            return {
                'status': 'failed',
                'candidate_id': candidate_id,
                'error': 'Proposal processing failed'
            }
            
    except Exception as e:
        logger.error(f"Error processing node proposal: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'candidate_id': candidate_id
        }

@celery.task(bind=True)
def process_actor_proposal(self, actor_id, name, description, wallet_address, is_unknown, proposer_id):
    """
    Process an actor proposal from another node
    """
    try:
        consensus_service = ConsensusService()
        
        # Propose the actor
        success = consensus_service.propose_actor(
            name=name,
            description=description,
            wallet_address=wallet_address,
            is_unknown=is_unknown
        )
        
        if success:
            logger.info(f"Actor proposal processed: {name}")
            return {
                'status': 'success',
                'actor_id': actor_id,
                'name': name,
                'proposer_id': proposer_id,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error(f"Failed to process actor proposal: {name}")
            return {
                'status': 'failed',
                'actor_id': actor_id,
                'error': 'Proposal processing failed'
            }
            
    except Exception as e:
        logger.error(f"Error processing actor proposal: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'actor_id': actor_id
        }

@celery.task(bind=True)
def auto_vote_on_node(self, candidate_id, voting_strategy='approve_known'):
    """
    Automatically vote on a node proposal based on strategy
    """
    try:
        consensus_service = ConsensusService()
        
        # Get candidate node
        candidate = NodeOperator.query.filter_by(operator_id=candidate_id).first()
        if not candidate:
            logger.error(f"Candidate node not found: {candidate_id}")
            return {
                'status': 'error',
                'error': 'Candidate node not found'
            }
        
        # Determine vote based on strategy
        vote = 'approve'  # Default
        
        if voting_strategy == 'approve_known':
            # Check if this is a known node
            if candidate.node_address not in Config.KNOWN_NODES:
                vote = 'reject'
                logger.info(f"Rejecting unknown node: {candidate_id}")
            else:
                logger.info(f"Approving known node: {candidate_id}")
        
        # Generate signature (simplified for demo)
        from utils.crypto import CryptoUtils
        crypto_utils = CryptoUtils()
        signature = crypto_utils.sign_message(f"node_vote:{candidate_id}:{vote}")
        
        # Cast vote
        success = consensus_service.vote_on_node(
            candidate_id=candidate_id,
            vote=vote,
            signature=signature
        )
        
        if success:
            logger.info(f"Auto-voted {vote} on node {candidate_id}")
            return {
                'status': 'success',
                'candidate_id': candidate_id,
                'vote': vote,
                'strategy': voting_strategy,
                'voted_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error(f"Failed to auto-vote on node: {candidate_id}")
            return {
                'status': 'failed',
                'candidate_id': candidate_id,
                'error': 'Voting failed'
            }
            
    except Exception as e:
        logger.error(f"Error auto-voting on node: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'candidate_id': candidate_id
        }

@celery.task(bind=True)
def auto_vote_on_actor(self, actor_id, voting_strategy='approve_non_unknown'):
    """
    Automatically vote on an actor proposal based on strategy
    """
    try:
        consensus_service = ConsensusService()
        
        # Get actor
        actor = Actor.query.get(actor_id)
        if not actor:
            logger.error(f"Actor not found: {actor_id}")
            return {
                'status': 'error',
                'error': 'Actor not found'
            }
        
        # Determine vote based on strategy
        vote = 'approve'  # Default
        
        if voting_strategy == 'approve_non_unknown':
            # Reject unknown actors by default
            if actor.is_unknown:
                vote = 'reject'
                logger.info(f"Rejecting unknown actor: {actor.name}")
            else:
                logger.info(f"Approving known actor: {actor.name}")
        
        # Generate signature (simplified for demo)
        from utils.crypto import CryptoUtils
        crypto_utils = CryptoUtils()
        signature = crypto_utils.sign_message(f"actor_vote:{actor_id}:{vote}")
        
        # Cast vote
        success = consensus_service.vote_on_actor(
            actor_id=actor_id,
            vote=vote,
            signature=signature
        )
        
        if success:
            logger.info(f"Auto-voted {vote} on actor {actor.name}")
            return {
                'status': 'success',
                'actor_id': actor_id,
                'vote': vote,
                'strategy': voting_strategy,
                'voted_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error(f"Failed to auto-vote on actor: {actor.name}")
            return {
                'status': 'failed',
                'actor_id': actor_id,
                'error': 'Voting failed'
            }
            
    except Exception as e:
        logger.error(f"Error auto-voting on actor: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'actor_id': actor_id
        }

@celery.task(bind=True)
def check_oracle_voting_timeouts(self):
    """
    Check for oracle voting timeouts and finalize voting
    """
    try:
        oracle_service = OracleService()
        
        # Clean up expired votes
        oracle_service.cleanup_expired_votes()
        
        logger.info("Oracle voting timeout check completed")
        
        return {
            'status': 'success',
            'checked_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking oracle voting timeouts: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def monitor_consensus_health(self):
    """
    Monitor consensus health and alert if issues detected
    """
    try:
        consensus_service = ConsensusService()
        
        # Get network health
        health = consensus_service.get_network_health()
        
        # Check for health issues
        issues = []
        
        if health['network_health'] < 0.5:
            issues.append('Low network health: less than 50% nodes online')
        
        if health['active_nodes'] < 3:
            issues.append('Too few active nodes for reliable consensus')
        
        if health['pending_nodes'] > health['active_nodes']:
            issues.append('More pending nodes than active nodes')
        
        # Log issues
        if issues:
            for issue in issues:
                logger.warning(f"Consensus health issue: {issue}")
        else:
            logger.info("Consensus health check: all systems healthy")
        
        return {
            'status': 'success',
            'health': health,
            'issues': issues,
            'checked_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoring consensus health: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def process_pending_consensus_items(self):
    """
    Process pending consensus items (nodes, actors)
    """
    try:
        # Process pending node proposals
        pending_nodes = NodeOperator.query.filter_by(status='pending').all()
        
        for node in pending_nodes:
            # Schedule auto-vote task
            auto_vote_on_node.delay(node.operator_id)
        
        # Process pending actor proposals
        pending_actors = Actor.query.filter_by(status='pending').all()
        
        for actor in pending_actors:
            # Schedule auto-vote task
            auto_vote_on_actor.delay(str(actor.id))
        
        logger.info(f"Processed {len(pending_nodes)} pending nodes and {len(pending_actors)} pending actors")
        
        return {
            'status': 'success',
            'pending_nodes': len(pending_nodes),
            'pending_actors': len(pending_actors),
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing pending consensus items: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def resolve_expired_bets(self):
    """
    Resolve bets that have passed their end time
    """
    try:
        oracle_service = OracleService()
        
        # Find bets that have expired
        expired_bets = Bet.query.filter(
            Bet.status == 'active',
            Bet.end_time < datetime.now(timezone.utc)
        ).all()
        
        resolved_count = 0
        
        for bet in expired_bets:
            try:
                # Try to resolve with oracle consensus
                consensus_text = oracle_service.resolve_oracle_consensus(str(bet.id))
                
                if consensus_text:
                    resolved_count += 1
                    logger.info(f"Resolved bet {bet.id} with oracle consensus")
                else:
                    logger.warning(f"No oracle consensus for expired bet {bet.id}")
                    
            except Exception as e:
                logger.error(f"Error resolving bet {bet.id}: {e}")
        
        logger.info(f"Resolved {resolved_count} out of {len(expired_bets)} expired bets")
        
        return {
            'status': 'success',
            'total_expired': len(expired_bets),
            'resolved_count': resolved_count,
            'resolved_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resolving expired bets: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def broadcast_consensus_update(self, update_type, data):
    """
    Broadcast consensus update to network
    """
    try:
        node_comm_service = NodeCommunicationService()
        
        # Broadcast message
        message = {
            'type': update_type,
            'data': data,
            'broadcasted_by': Config.NODE_OPERATOR_ID
        }
        
        node_comm_service.broadcast_message(message)
        
        logger.info(f"Broadcast consensus update: {update_type}")
        
        return {
            'status': 'success',
            'update_type': update_type,
            'broadcasted_at': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting consensus update: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

# Setup periodic tasks
@celery.on_after_configure.connect
def setup_consensus_periodic_tasks(sender, **kwargs):
    """Setup periodic consensus tasks"""
    
    # Check oracle voting timeouts every minute
    sender.add_periodic_task(
        60.0,
        check_oracle_voting_timeouts.s(),
        name='check_oracle_voting_timeouts'
    )
    
    # Monitor consensus health every 5 minutes
    sender.add_periodic_task(
        300.0,
        monitor_consensus_health.s(),
        name='monitor_consensus_health'
    )
    
    # Process pending consensus items every 30 seconds
    sender.add_periodic_task(
        30.0,
        process_pending_consensus_items.s(),
        name='process_pending_consensus_items'
    )
    
    # Resolve expired bets every 10 minutes (legacy V1)
    sender.add_periodic_task(
        600.0,
        resolve_expired_bets.s(),
        name='resolve_expired_bets'
    )

    # Resolve V2 pending markets every 5 minutes
    sender.add_periodic_task(
        300.0,
        resolve_v2_pending_markets.s(),
        name='resolve_v2_pending_markets'
    )


# ====================================================================
# V2 BLOCKCHAIN-BASED RESOLUTION TASKS
# ====================================================================
# These tasks work directly with PredictionMarketV2 on the blockchain
# without requiring the legacy database models.
# ====================================================================

@celery.task(bind=True)
def resolve_v2_pending_markets(self):
    """
    Check for V2 markets that are pending resolution and attempt auto-resolution.
    This task requires:
    - OWNER_PRIVATE_KEY env var for signing transactions
    - X_BEARER_TOKEN env var for fetching tweets (optional, manual fallback)
    """
    import asyncio

    try:
        from services.v2_resolution import get_resolution_service

        resolution_service = get_resolution_service()
        stats = resolution_service.get_resolution_stats()

        # Check if we have the required configuration
        if not stats.get('owner_key_configured'):
            logger.info("V2 resolution skipped - OWNER_PRIVATE_KEY not configured")
            return {
                'status': 'skipped',
                'reason': 'owner_key_not_configured'
            }

        # Get pending markets
        pending = resolution_service.get_pending_markets()

        if not pending:
            logger.debug("No V2 markets pending resolution")
            return {
                'status': 'success',
                'pending_count': 0,
                'resolved_count': 0
            }

        logger.info(f"Found {len(pending)} V2 markets pending resolution")

        # Track resolution results
        resolved_count = 0
        failed_count = 0
        skipped_count = 0

        for market in pending:
            market_id = market['id']
            actor_handle = market['actor_handle']

            # Skip if not enough submissions
            if not market.get('can_resolve'):
                logger.debug(f"Market {market_id} not resolvable (needs 2+ submissions)")
                skipped_count += 1
                continue

            # Check if X.com API is configured
            if not stats.get('xcom_api_configured'):
                logger.warning(f"Market {market_id} needs manual resolution - X.com API not configured")
                skipped_count += 1
                continue

            try:
                # Attempt to fetch latest tweet from actor
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    tweet_data = loop.run_until_complete(
                        resolution_service.fetch_actual_tweet(actor_handle)
                    )
                finally:
                    loop.close()

                if not tweet_data:
                    logger.warning(f"Could not fetch tweet for @{actor_handle} (market {market_id})")
                    skipped_count += 1
                    continue

                actual_text = tweet_data.get('text', '')
                if not actual_text:
                    logger.warning(f"Empty tweet text for @{actor_handle} (market {market_id})")
                    skipped_count += 1
                    continue

                # Attempt resolution
                result = resolution_service.resolve_market(market_id, actual_text)

                if result['success']:
                    resolved_count += 1
                    logger.info(f"Auto-resolved market {market_id} for @{actor_handle}, tx: {result['tx_hash']}")
                else:
                    failed_count += 1
                    logger.error(f"Failed to resolve market {market_id}: {result.get('error')}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Error auto-resolving market {market_id}: {e}")

        logger.info(f"V2 resolution complete: {resolved_count} resolved, {failed_count} failed, {skipped_count} skipped")

        return {
            'status': 'success',
            'pending_count': len(pending),
            'resolved_count': resolved_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
            'resolved_at': datetime.now(timezone.utc).isoformat()
        }

    except ImportError as e:
        logger.error(f"V2 resolution service not available: {e}")
        return {
            'status': 'error',
            'error': 'V2 resolution service not available'
        }
    except Exception as e:
        logger.error(f"Error in V2 resolution task: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


@celery.task(bind=True)
def check_v2_resolution_health(self):
    """
    Check health of V2 resolution system
    """
    try:
        from services.v2_resolution import get_resolution_service

        resolution_service = get_resolution_service()
        stats = resolution_service.get_resolution_stats()

        # Log health status
        logger.info(f"V2 Resolution Health: {stats.get('total_markets', 0)} total, "
                   f"{stats.get('pending_resolution', 0)} pending, "
                   f"{stats.get('resolved_markets', 0)} resolved")

        # Check for configuration issues
        issues = []

        if not stats.get('owner_key_configured'):
            issues.append('OWNER_PRIVATE_KEY not configured')

        if not stats.get('xcom_api_configured'):
            issues.append('X.com API not configured (manual resolution only)')

        if stats.get('pending_resolution', 0) > 10:
            issues.append(f"High number of pending markets: {stats.get('pending_resolution')}")

        if issues:
            for issue in issues:
                logger.warning(f"V2 Resolution Issue: {issue}")

        return {
            'status': 'success',
            'stats': stats,
            'issues': issues,
            'checked_at': datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking V2 resolution health: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import json
from services.blockchain import BlockchainService
from services.consensus import ConsensusService
from services.ledger import LedgerService
from services.oracle import OracleService
from services.time_sync import TimeSyncService
from services.text_analysis import TextAnalysisService
from services.node_communication import NodeCommunicationService
from models import Bet, Stake, Actor, NodeOperator, Transaction, OracleSubmission
from app import db
from utils.validation import ValidationUtils
from utils.crypto import CryptoUtils

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# Initialize services
blockchain_service = BlockchainService()
consensus_service = ConsensusService()
ledger_service = LedgerService()
oracle_service = OracleService()
time_sync_service = TimeSyncService()
text_analysis_service = TextAnalysisService()
node_comm_service = NodeCommunicationService()
validation_utils = ValidationUtils()
crypto_utils = CryptoUtils()

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'clockchain-node'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'error': 'Service unavailable'}), 500

@api_bp.route('/time/current', methods=['GET'])
def get_current_time():
    """Get current Pacific time"""
    try:
        health_status = time_sync_service.get_time_health_status()
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        return jsonify({'error': 'Failed to get current time'}), 500

@api_bp.route('/actors', methods=['GET'])
def get_actors():
    """Get all approved actors"""
    try:
        exclude_unknown = request.args.get('exclude_unknown', 'false').lower() == 'true'
        
        query = Actor.query.filter_by(status='approved')
        if exclude_unknown:
            query = query.filter_by(is_unknown=False)
            
        actors = query.all()
        
        actors_data = []
        for actor in actors:
            actors_data.append({
                'id': str(actor.id),
                'name': actor.name,
                'description': actor.description,
                'wallet_address': actor.wallet_address,
                'is_unknown': actor.is_unknown,
                'approval_votes': actor.approval_votes,
                'created_at': actor.created_at.isoformat()
            })
            
        return jsonify({
            'actors': actors_data,
            'total': len(actors_data),
            'exclude_unknown': exclude_unknown
        })
        
    except Exception as e:
        logger.error(f"Error getting actors: {e}")
        return jsonify({'error': 'Failed to get actors'}), 500

@api_bp.route('/actors', methods=['POST'])
def propose_actor():
    """Propose a new actor"""
    try:
        data = request.get_json()
        
        # Validate request
        validation_result = validation_utils.validate_actor_proposal(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
            
        # Propose actor
        success = consensus_service.propose_actor(
            name=data['name'],
            description=data.get('description', ''),
            wallet_address=data.get('wallet_address'),
            is_unknown=data.get('is_unknown', False)
        )
        
        if success:
            return jsonify({'message': 'Actor proposed successfully'})
        else:
            return jsonify({'error': 'Failed to propose actor'}), 500
            
    except Exception as e:
        logger.error(f"Error proposing actor: {e}")
        return jsonify({'error': 'Failed to propose actor'}), 500

@api_bp.route('/actors/<actor_id>/vote', methods=['POST'])
def vote_on_actor(actor_id):
    """Vote on an actor proposal"""
    try:
        data = request.get_json()
        
        # Validate request
        validation_result = validation_utils.validate_actor_vote(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
            
        # Vote on actor
        success = consensus_service.vote_on_actor(
            actor_id=actor_id,
            vote=data['vote'],
            signature=data['signature']
        )
        
        if success:
            return jsonify({'message': 'Vote recorded successfully'})
        else:
            return jsonify({'error': 'Failed to record vote'}), 500
            
    except Exception as e:
        logger.error(f"Error voting on actor: {e}")
        return jsonify({'error': 'Failed to vote on actor'}), 500

@api_bp.route('/bets', methods=['GET'])
def get_bets():
    """Get all bets"""
    try:
        status = request.args.get('status', 'active')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = Bet.query.filter_by(status=status)
        
        # Pagination
        bets = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        bets_data = []
        for bet in bets.items:
            # Get actor info
            actor = Actor.query.get(bet.actor_id)
            
            # Get stakes count
            stakes_count = Stake.query.filter_by(bet_id=bet.id).count()
            
            # Calculate total volume
            total_volume = db.session.query(
                db.func.sum(Stake.amount)
            ).filter(Stake.bet_id == bet.id).scalar() or 0
            
            bets_data.append({
                'id': str(bet.id),
                'creator_wallet': bet.creator_wallet,
                'actor': {
                    'id': str(actor.id),
                    'name': actor.name,
                    'is_unknown': actor.is_unknown
                } if actor else None,
                'predicted_text': bet.predicted_text,
                'start_time': bet.start_time.isoformat(),
                'end_time': bet.end_time.isoformat(),
                'oracle_wallets': json.loads(bet.oracle_wallets),
                'initial_stake_amount': str(bet.initial_stake_amount),
                'currency': bet.currency,
                'transaction_hash': bet.transaction_hash,
                'status': bet.status,
                'stakes_count': stakes_count,
                'total_volume': str(total_volume),
                'resolution_text': bet.resolution_text,
                'levenshtein_distance': bet.levenshtein_distance,
                'resolution_time': bet.resolution_time.isoformat() if bet.resolution_time else None,
                'created_at': bet.created_at.isoformat()
            })
            
        return jsonify({
            'bets': bets_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': bets.total,
                'pages': bets.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting bets: {e}")
        return jsonify({'error': 'Failed to get bets'}), 500

@api_bp.route('/bets', methods=['POST'])
def create_bet():
    """Create a new bet"""
    try:
        data = request.get_json()
        
        # Validate request
        validation_result = validation_utils.validate_bet_creation(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
            
        # Validate transaction
        tx_data = None
        if data['currency'] == 'ETH':
            tx_data = blockchain_service.validate_eth_transaction(data['transaction_hash'])
        elif data['currency'] == 'BTC':
            tx_data = blockchain_service.validate_btc_transaction(data['transaction_hash'])
            
        if not tx_data:
            return jsonify({'error': 'Invalid transaction'}), 400
            
        # Validate text content
        text_validation = text_analysis_service.validate_text_content(data['predicted_text'])
        if not text_validation['valid']:
            return jsonify({'error': text_validation['error']}), 400
            
        # Create bet
        bet = Bet(
            creator_wallet=data['creator_wallet'],
            actor_id=data['actor_id'],
            predicted_text=data['predicted_text'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            oracle_wallets=json.dumps(data['oracle_wallets']),
            initial_stake_amount=Decimal(data['initial_stake_amount']),
            currency=data['currency'],
            transaction_hash=data['transaction_hash']
        )
        
        db.session.add(bet)
        db.session.commit()
        
        # Record transaction
        ledger_service.record_transaction({
            'hash': data['transaction_hash'],
            'from': tx_data['from'],
            'to': tx_data['to'],
            'amount': tx_data.get('value', tx_data.get('total_output', 0)),
            'currency': data['currency'],
            'type': 'bet_creation',
            'bet_id': str(bet.id),
            'block_number': tx_data.get('block_number', tx_data.get('block_height'))
        })
        
        # Create time entry
        ledger_service.create_time_entry('bet_created', {
            'bet_id': str(bet.id),
            'creator_wallet': bet.creator_wallet,
            'actor_id': str(bet.actor_id),
            'predicted_text': bet.predicted_text,
            'initial_stake_amount': str(bet.initial_stake_amount),
            'currency': bet.currency
        })
        
        # Broadcast to network
        node_comm_service.broadcast_message({
            'type': 'bet_created',
            'bet_id': str(bet.id),
            'creator_wallet': bet.creator_wallet,
            'actor_id': str(bet.actor_id),
            'predicted_text': bet.predicted_text,
            'transaction_hash': bet.transaction_hash
        })
        
        return jsonify({
            'bet_id': str(bet.id),
            'message': 'Bet created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating bet: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create bet'}), 500

@api_bp.route('/bets/<bet_id>/stakes', methods=['POST'])
def place_stake(bet_id):
    """Place a stake on a bet"""
    try:
        data = request.get_json()
        
        # Validate request
        validation_result = validation_utils.validate_stake_placement(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
            
        # Get bet
        bet = Bet.query.get(bet_id)
        if not bet:
            return jsonify({'error': 'Bet not found'}), 404
            
        if bet.status != 'active':
            return jsonify({'error': 'Bet is not active'}), 400
            
        # Validate transaction
        tx_data = None
        if data['currency'] == 'ETH':
            tx_data = blockchain_service.validate_eth_transaction(data['transaction_hash'])
        elif data['currency'] == 'BTC':
            tx_data = blockchain_service.validate_btc_transaction(data['transaction_hash'])
            
        if not tx_data:
            return jsonify({'error': 'Invalid transaction'}), 400
            
        # Create stake
        stake = Stake(
            bet_id=bet_id,
            staker_wallet=data['staker_wallet'],
            amount=Decimal(data['amount']),
            currency=data['currency'],
            transaction_hash=data['transaction_hash'],
            position=data['position']
        )
        
        db.session.add(stake)
        db.session.commit()
        
        # Record transaction
        ledger_service.record_transaction({
            'hash': data['transaction_hash'],
            'from': tx_data['from'],
            'to': tx_data['to'],
            'amount': tx_data.get('value', tx_data.get('total_output', 0)),
            'currency': data['currency'],
            'type': 'stake',
            'bet_id': bet_id,
            'block_number': tx_data.get('block_number', tx_data.get('block_height'))
        })
        
        # Create time entry
        ledger_service.create_time_entry('stake_placed', {
            'stake_id': str(stake.id),
            'bet_id': bet_id,
            'staker_wallet': stake.staker_wallet,
            'amount': str(stake.amount),
            'currency': stake.currency,
            'position': stake.position
        })
        
        # Broadcast to network
        node_comm_service.broadcast_message({
            'type': 'stake_placed',
            'stake_id': str(stake.id),
            'bet_id': bet_id,
            'staker_wallet': stake.staker_wallet,
            'amount': str(stake.amount),
            'position': stake.position
        })
        
        return jsonify({
            'stake_id': str(stake.id),
            'message': 'Stake placed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error placing stake: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to place stake'}), 500

@api_bp.route('/oracle/submit', methods=['POST'])
def submit_oracle_statement():
    """Submit an oracle statement"""
    try:
        data = request.get_json()
        
        # Validate request
        validation_result = validation_utils.validate_oracle_submission(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
            
        # Submit oracle statement
        success = oracle_service.submit_oracle_statement(
            bet_id=data['bet_id'],
            oracle_wallet=data['oracle_wallet'],
            submitted_text=data['submitted_text'],
            signature=data['signature']
        )
        
        if success:
            return jsonify({'message': 'Oracle statement submitted successfully'})
        else:
            return jsonify({'error': 'Failed to submit oracle statement'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting oracle statement: {e}")
        return jsonify({'error': 'Failed to submit oracle statement'}), 500

@api_bp.route('/oracle/vote', methods=['POST'])
def vote_on_oracle():
    """Vote on an oracle submission"""
    try:
        data = request.get_json()
        
        # Validate request
        validation_result = validation_utils.validate_oracle_vote(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
            
        # Vote on oracle
        success = oracle_service.vote_on_oracle_submission(
            submission_id=data['submission_id'],
            voter_wallet=data['voter_wallet'],
            vote=data['vote'],
            signature=data['signature']
        )
        
        if success:
            return jsonify({'message': 'Oracle vote recorded successfully'})
        else:
            return jsonify({'error': 'Failed to record oracle vote'}), 500
            
    except Exception as e:
        logger.error(f"Error voting on oracle: {e}")
        return jsonify({'error': 'Failed to vote on oracle'}), 500

@api_bp.route('/oracle/status/<bet_id>', methods=['GET'])
def get_oracle_status(bet_id):
    """Get oracle status for a bet"""
    try:
        status = oracle_service.get_oracle_status(bet_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting oracle status: {e}")
        return jsonify({'error': 'Failed to get oracle status'}), 500

@api_bp.route('/text/analyze', methods=['POST'])
def analyze_text():
    """Analyze text differences"""
    try:
        data = request.get_json()
        
        if 'text1' not in data or 'text2' not in data:
            return jsonify({'error': 'Both text1 and text2 are required'}), 400
            
        analysis = text_analysis_service.analyze_text_differences(
            data['text1'],
            data['text2']
        )
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        return jsonify({'error': 'Failed to analyze text'}), 500

@api_bp.route('/ledger/summary', methods=['GET'])
def get_ledger_summary():
    """Get ledger summary"""
    try:
        summary = ledger_service.get_ledger_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting ledger summary: {e}")
        return jsonify({'error': 'Failed to get ledger summary'}), 500

@api_bp.route('/network/status', methods=['GET'])
def get_network_status():
    """Get network status"""
    try:
        # Get consensus health
        consensus_health = consensus_service.get_network_health()
        
        # Get connection status
        connection_status = node_comm_service.get_connection_status()
        
        # Get ledger summary
        ledger_summary = ledger_service.get_ledger_summary()
        
        return jsonify({
            'consensus': consensus_health,
            'connections': connection_status,
            'ledger': ledger_summary
        })
        
    except Exception as e:
        logger.error(f"Error getting network status: {e}")
        return jsonify({'error': 'Failed to get network status'}), 500

@api_bp.route('/node/message', methods=['POST'])
def receive_node_message():
    """Receive message from another node (HTTP fallback)"""
    try:
        data = request.get_json()
        
        # Verify message signature
        message_copy = data.copy()
        signature = message_copy.pop('signature', None)
        
        if not signature:
            return jsonify({'error': 'Message signature required'}), 400
            
        # Process message based on type
        message_type = data.get('type')
        
        if message_type == 'oracle_submission':
            success = oracle_service.submit_oracle_statement(
                data['bet_id'],
                data['oracle_wallet'],
                data['submitted_text'],
                data['signature']
            )
            
            if success:
                return jsonify({'message': 'Oracle submission processed'})
            else:
                return jsonify({'error': 'Failed to process oracle submission'}), 500
                
        elif message_type == 'reconciliation_request':
            success = ledger_service.reconcile_time_entries(
                data['start_time_ms'],
                data['end_time_ms']
            )
            
            if success:
                return jsonify({'message': 'Reconciliation processed'})
            else:
                return jsonify({'error': 'Failed to process reconciliation'}), 500
                
        else:
            logger.warning(f"Unknown message type: {message_type}")
            return jsonify({'error': 'Unknown message type'}), 400
            
    except Exception as e:
        logger.error(f"Error receiving node message: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

@api_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Get transaction history"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        currency = request.args.get('currency')
        transaction_type = request.args.get('type')
        
        query = Transaction.query
        
        if currency:
            query = query.filter_by(currency=currency)
            
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
            
        # Order by creation time
        query = query.order_by(Transaction.created_at.desc())
        
        # Pagination
        transactions = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        transactions_data = []
        for tx in transactions.items:
            transactions_data.append({
                'id': str(tx.id),
                'transaction_hash': tx.transaction_hash,
                'from_address': tx.from_address,
                'to_address': tx.to_address,
                'amount': str(tx.amount),
                'currency': tx.currency,
                'transaction_type': tx.transaction_type,
                'related_bet_id': str(tx.related_bet_id) if tx.related_bet_id else None,
                'platform_fee': str(tx.platform_fee),
                'status': tx.status,
                'block_number': tx.block_number,
                'created_at': tx.created_at.isoformat()
            })
            
        return jsonify({
            'transactions': transactions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': transactions.total,
                'pages': transactions.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({'error': 'Failed to get transactions'}), 500

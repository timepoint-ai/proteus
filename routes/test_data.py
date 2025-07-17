from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import random
import string
from sqlalchemy import func, desc
from models import (
    NodeOperator, Actor, Bet, Stake, Transaction, 
    OracleSubmission, SyntheticTimeEntry, NetworkMetrics
)
from app import db
from services.time_sync import TimeSyncService
from services.blockchain import BlockchainService
import json

logger = logging.getLogger(__name__)

test_data_bp = Blueprint('test_data', __name__)

# Initialize services
time_sync_service = TimeSyncService()
blockchain_service = BlockchainService()

@test_data_bp.route('/')
def test_data_dashboard():
    """Test data management dashboard"""
    stats = {
        'total_nodes': NodeOperator.query.count(),
        'total_actors': Actor.query.count(),
        'total_bets': Bet.query.count(),
        'total_stakes': Stake.query.count(),
        'total_transactions': Transaction.query.count(),
        'total_oracle_submissions': OracleSubmission.query.count(),
        'total_network_metrics': NetworkMetrics.query.count(),
        'total_time_entries': SyntheticTimeEntry.query.count()
    }
    
    return render_template('test_data/dashboard.html', stats=stats)

@test_data_bp.route('/generate', methods=['POST'])
def generate_test_data():
    """Generate comprehensive test data"""
    try:
        data_type = request.form.get('data_type')
        quantity = int(request.form.get('quantity', 5))
        
        if data_type == 'nodes':
            _generate_test_nodes(quantity)
        elif data_type == 'actors':
            _generate_test_actors(quantity)
        elif data_type == 'bets':
            _generate_test_bets(quantity)
        elif data_type == 'stakes':
            _generate_test_stakes(quantity)
        elif data_type == 'transactions':
            _generate_test_transactions(quantity)
        elif data_type == 'oracle_submissions':
            _generate_test_oracle_submissions(quantity)
        elif data_type == 'network_metrics':
            _generate_test_network_metrics(quantity)
        elif data_type == 'time_entries':
            _generate_test_time_entries(quantity)
        elif data_type == 'full_dataset':
            _generate_full_test_dataset()
        else:
            flash('Invalid data type', 'error')
            return redirect(url_for('test_data.test_data_dashboard'))
        
        db.session.commit()
        flash(f'Successfully generated {data_type} test data', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating test data: {e}")
        flash(f'Error generating test data: {str(e)}', 'error')
    
    return redirect(url_for('test_data.test_data_dashboard'))

@test_data_bp.route('/clear', methods=['POST'])
def clear_test_data():
    """Clear test data with proper cascading"""
    try:
        data_type = request.form.get('data_type')
        
        if data_type == 'all':
            # Clear in proper order to handle foreign key constraints
            OracleSubmission.query.delete()
            Stake.query.delete()
            Bet.query.delete()
            Transaction.query.delete()
            SyntheticTimeEntry.query.delete()
            NetworkMetrics.query.delete()
            Actor.query.delete()
            NodeOperator.query.delete()
        elif data_type == 'nodes':
            # Clear dependent records first
            OracleSubmission.query.delete()
            Stake.query.delete()
            Bet.query.delete()
            Transaction.query.delete()
            SyntheticTimeEntry.query.delete()
            NetworkMetrics.query.delete()
            NodeOperator.query.delete()
        elif data_type == 'actors':
            # Clear dependent records first
            Bet.query.filter(Bet.actor_id.in_(
                db.session.query(Actor.id).subquery()
            )).delete(synchronize_session=False)
            Actor.query.delete()
        elif data_type == 'bets':
            # Clear dependent records first
            Stake.query.delete()
            OracleSubmission.query.delete()
            Bet.query.delete()
        elif data_type == 'stakes':
            Stake.query.delete()
        elif data_type == 'transactions':
            Transaction.query.delete()
        elif data_type == 'oracle_submissions':
            OracleSubmission.query.delete()
        elif data_type == 'network_metrics':
            NetworkMetrics.query.delete()
        elif data_type == 'time_entries':
            SyntheticTimeEntry.query.delete()
        else:
            flash('Invalid data type', 'error')
            return redirect(url_for('test_data.test_data_dashboard'))
        
        db.session.commit()
        flash(f'Successfully cleared {data_type} data', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error clearing test data: {e}")
        flash(f'Error clearing test data: {str(e)}', 'error')
    
    return redirect(url_for('test_data.test_data_dashboard'))

def _generate_test_nodes(quantity):
    """Generate test node operators"""
    statuses = ['active', 'inactive', 'pending']
    
    for i in range(quantity):
        operator_id = f"test-node-{random.randint(1000, 9999)}"
        node = NodeOperator(
            operator_id=operator_id,
            status=random.choice(statuses),
            public_key=f"pk_test_{operator_id}_{random.randint(1000, 9999)}",
            node_address=f"0x{''.join(random.choices(string.hexdigits.lower(), k=40))}",
            last_seen=datetime.utcnow() - timedelta(minutes=random.randint(0, 60)),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
        )
        db.session.add(node)

def _generate_test_actors(quantity):
    """Generate test actors"""
    actor_names = [
        "John Smith", "Jane Doe", "Robert Johnson", "Emily Davis",
        "Michael Wilson", "Sarah Brown", "David Miller", "Lisa Anderson",
        "James Taylor", "Jessica Garcia", "William Martinez", "Ashley Rodriguez"
    ]
    
    for i in range(quantity):
        actor = Actor(
            name=random.choice(actor_names),
            description=f"Test actor {i+1} for prediction markets",
            wallet_address=f"0x{''.join(random.choices(string.hexdigits.lower(), k=40))}",
            is_unknown=random.choice([True, False]),
            approval_votes=random.randint(0, 50),
            rejection_votes=random.randint(0, 20),
            status=random.choice(['approved', 'pending', 'rejected']),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 100))
        )
        db.session.add(actor)

def _generate_test_bets(quantity):
    """Generate test bets"""
    # Get existing actors and nodes
    actors = Actor.query.all()
    nodes = NodeOperator.query.all()
    
    if not actors or not nodes:
        flash('Need actors and nodes to generate bets', 'error')
        return
    
    statuses = ['active', 'resolved', 'cancelled']
    currencies = ['ETH', 'BTC']
    
    for i in range(quantity):
        actor = random.choice(actors)
        oracle_nodes = random.sample(nodes, min(3, len(nodes)))  # Select 3 random oracle nodes
        
        # Create time windows
        start_time = datetime.utcnow() + timedelta(days=random.randint(1, 30))
        end_time = start_time + timedelta(hours=random.randint(1, 24))
        resolution_time = end_time + timedelta(hours=random.randint(1, 72))
        
        bet = Bet(
            creator_wallet=f"0x{''.join(random.choices(string.hexdigits.lower(), k=40))}",
            actor_id=actor.id,
            predicted_text=f"This is a test prediction statement {i+1} for {actor.name}",
            start_time=start_time,
            end_time=end_time,
            oracle_wallets=json.dumps([node.node_address for node in oracle_nodes]),
            initial_stake_amount=Decimal(random.uniform(0.1, 10.0)),
            currency=random.choice(currencies),
            transaction_hash=f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}",
            status=random.choice(statuses),
            resolution_time=resolution_time,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
        )
        
        if bet.status == 'resolved':
            bet.resolution_text = f"This is the actual statement that was made by {actor.name}"
            bet.levenshtein_distance = random.randint(0, 50)
        
        db.session.add(bet)

def _generate_test_stakes(quantity):
    """Generate test stakes"""
    bets = Bet.query.all()
    nodes = NodeOperator.query.all()
    
    if not bets or not nodes:
        flash('Need bets and nodes to generate stakes', 'error')
        return
    
    positions = ['for', 'against']
    currencies = ['ETH', 'BTC']
    
    for i in range(quantity):
        bet = random.choice(bets)
        node = random.choice(nodes)
        
        # Avoid duplicate stakes for same bet/staker combination
        existing_stake = Stake.query.filter_by(bet_id=bet.id, staker_wallet=node.node_address).first()
        if existing_stake:
            continue
            
        stake = Stake(
            bet_id=bet.id,
            staker_wallet=node.node_address,
            amount=Decimal(random.uniform(0.1, 5.0)),
            currency=random.choice(currencies),
            transaction_hash=f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}",
            position=random.choice(positions),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        
        # Add payout if bet is resolved
        if bet.status == 'resolved':
            stake.payout_amount = stake.amount * Decimal(random.uniform(0.8, 1.5))
            stake.payout_transaction_hash = f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}"
        
        db.session.add(stake)

def _generate_test_transactions(quantity):
    """Generate test transactions"""
    nodes = NodeOperator.query.all()
    bets = Bet.query.all()
    
    if not nodes:
        flash('Need nodes to generate transactions', 'error')
        return
    
    transaction_types = ['stake', 'payout', 'fee']
    currencies = ['ETH', 'BTC']
    statuses = ['pending', 'confirmed', 'failed']
    
    for i in range(quantity):
        from_node = random.choice(nodes)
        to_node = random.choice(nodes)
        
        transaction = Transaction(
            transaction_hash=f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}",
            from_address=from_node.node_address,
            to_address=to_node.node_address,
            amount=Decimal(random.uniform(0.1, 10.0)),
            currency=random.choice(currencies),
            transaction_type=random.choice(transaction_types),
            related_bet_id=random.choice(bets).id if bets and random.random() > 0.5 else None,
            platform_fee=Decimal(random.uniform(0.01, 0.1)),
            status=random.choice(statuses),
            block_number=random.randint(1000000, 2000000),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        
        db.session.add(transaction)

def _generate_test_oracle_submissions(quantity):
    """Generate test oracle submissions"""
    bets = Bet.query.all()
    nodes = NodeOperator.query.all()
    
    if not bets or not nodes:
        flash('Need bets and nodes to generate oracle submissions', 'error')
        return
    
    for i in range(quantity):
        bet = random.choice(bets)
        oracle_node = random.choice(nodes)
        
        submission = OracleSubmission(
            bet_id=bet.id,
            oracle_wallet=oracle_node.node_address,
            submitted_text=f"Oracle submission {i+1} for bet {bet.id}",
            signature=f"oracle_signature_{i}_{random.randint(1000, 9999)}",
            votes_for=random.randint(0, 10),
            votes_against=random.randint(0, 5),
            is_consensus=random.choice([True, False]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
        )
        
        db.session.add(submission)

def _generate_test_network_metrics(quantity):
    """Generate test network metrics"""
    for i in range(quantity):
        metric = NetworkMetrics(
            timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
            active_nodes=random.randint(5, 50),
            total_bets=random.randint(10, 500),
            total_stakes=random.randint(100, 5000),
            total_volume_eth=Decimal(random.uniform(10.0, 1000.0)),
            total_volume_btc=Decimal(random.uniform(1.0, 50.0)),
            platform_fees_eth=Decimal(random.uniform(0.1, 10.0)),
            platform_fees_btc=Decimal(random.uniform(0.01, 0.5)),
            consensus_accuracy=random.uniform(0.7, 1.0)
        )
        
        db.session.add(metric)

def _generate_test_time_entries(quantity):
    """Generate test synthetic time entries"""
    nodes = NodeOperator.query.all()
    
    if not nodes:
        flash('Need nodes to generate time entries', 'error')
        return
    
    entry_types = ['bet_created', 'stake_placed', 'resolution', 'oracle_submission', 'consensus_reached']
    
    for i in range(quantity):
        node = random.choice(nodes)
        
        # Generate Pacific Time in milliseconds
        pacific_time_ms = int(datetime.utcnow().timestamp() * 1000) + random.randint(-86400000, 86400000)
        
        entry = SyntheticTimeEntry(
            timestamp_ms=pacific_time_ms,
            entry_type=random.choice(entry_types),
            entry_data=json.dumps({
                'test_data': f'Entry {i+1}',
                'node_id': str(node.id),
                'random_value': random.randint(1, 1000)
            }),
            node_id=node.id,
            signature=f"test_signature_{i}_{random.randint(1000, 9999)}",
            reconciled=random.choice([True, False]),
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        
        db.session.add(entry)

def _generate_full_test_dataset():
    """Generate a complete test dataset with proper relationships"""
    # Generate in proper order to handle foreign key constraints
    _generate_test_nodes(10)
    db.session.commit()
    
    _generate_test_actors(8)
    db.session.commit()
    
    _generate_test_bets(15)
    db.session.commit()
    
    _generate_test_stakes(25)
    db.session.commit()
    
    _generate_test_transactions(20)
    db.session.commit()
    
    _generate_test_oracle_submissions(12)
    db.session.commit()
    
    _generate_test_network_metrics(50)
    db.session.commit()
    
    _generate_test_time_entries(30)
    db.session.commit()

@test_data_bp.route('/second_node')
def second_node_simulator():
    """Second node simulator for testing distributed functionality"""
    return render_template('test_data/second_node.html')

@test_data_bp.route('/second_node/start', methods=['POST'])
def start_second_node():
    """Start second node simulation"""
    try:
        # Create a second node operator
        second_node = NodeOperator(
            operator_id="simulator-node-002",
            status="active",
            public_key="pk_simulator_002",
            node_address="0x" + "".join(random.choices(string.hexdigits.lower(), k=40)),
            last_seen=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        db.session.add(second_node)
        db.session.commit()
        
        # Generate some activity from this node
        _generate_activity_for_node(second_node)
        
        flash('Second node simulator started successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting second node: {e}")
        flash(f'Error starting second node: {str(e)}', 'error')
    
    return redirect(url_for('test_data.second_node_simulator'))

def _generate_activity_for_node(node):
    """Generate realistic activity for a node"""
    # Create some stakes
    active_bets = Bet.query.filter_by(status='active').limit(5).all()
    for bet in active_bets:
        stake = Stake(
            bet_id=bet.id,
            staker_wallet=node.node_address,
            amount=Decimal(random.uniform(1.0, 10.0)),
            currency=random.choice(['ETH', 'BTC']),
            transaction_hash=f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}",
            position=random.choice(['for', 'against']),
            created_at=datetime.utcnow()
        )
        db.session.add(stake)
    
    # Create some transactions
    for i in range(3):
        transaction = Transaction(
            transaction_hash=f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}",
            from_address=node.node_address,
            to_address=f"0x{''.join(random.choices(string.hexdigits.lower(), k=40))}",
            amount=Decimal(random.uniform(0.1, 5.0)),
            currency=random.choice(['ETH', 'BTC']),
            transaction_type='stake',
            platform_fee=Decimal(random.uniform(0.01, 0.1)),
            status='confirmed',
            block_number=random.randint(1000000, 2000000),
            created_at=datetime.utcnow()
        )
        db.session.add(transaction)
    
    # Create time sync entry
    time_entry = SyntheticTimeEntry(
        timestamp_ms=int(datetime.utcnow().timestamp() * 1000),
        entry_type='node_activity',
        entry_data=json.dumps({
            'node_id': str(node.id),
            'operator_id': node.operator_id,
            'activity_type': 'simulator_startup'
        }),
        node_id=node.id,
        signature=f"node_{node.operator_id}_signature",
        reconciled=True,
        created_at=datetime.utcnow()
    )
    db.session.add(time_entry)
    
    db.session.commit()

@test_data_bp.route('/api/node_status/<operator_id>')
def get_node_status(operator_id):
    """Get status of a specific node"""
    node = NodeOperator.query.filter_by(operator_id=operator_id).first()
    if not node:
        return jsonify({'error': 'Node not found'}), 404
    
    # Get node statistics
    stakes = Stake.query.filter_by(staker_wallet=node.node_address).count()
    transactions = Transaction.query.filter_by(from_address=node.node_address).count()
    time_entries = SyntheticTimeEntry.query.filter_by(node_id=node.id).count()
    
    return jsonify({
        'operator_id': node.operator_id,
        'status': node.status,
        'node_address': node.node_address,
        'public_key': node.public_key[:20] + '...' if len(node.public_key) > 20 else node.public_key,
        'total_stakes': stakes,
        'total_transactions': transactions,
        'total_time_entries': time_entries,
        'last_seen': node.last_seen.isoformat() if node.last_seen else None,
        'created_at': node.created_at.isoformat() if node.created_at else None
    })
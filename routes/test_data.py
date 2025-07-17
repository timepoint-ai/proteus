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
    node_types = ['validator', 'oracle', 'observer']
    statuses = ['active', 'inactive', 'pending']
    
    for i in range(quantity):
        node_id = f"test-node-{random.randint(1000, 9999)}"
        node = NodeOperator(
            node_id=node_id,
            node_type=random.choice(node_types),
            status=random.choice(statuses),
            public_key=f"pk_test_{node_id}_{random.randint(1000, 9999)}",
            eth_address=f"0x{''.join(random.choices(string.hexdigits.lower(), k=40))}",
            btc_address=f"{''.join(random.choices(string.ascii_letters + string.digits, k=34))}",
            stake_amount=Decimal(random.uniform(100, 10000)),
            reputation_score=random.randint(0, 100),
            last_heartbeat=datetime.utcnow() - timedelta(minutes=random.randint(0, 60)),
            joined_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
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
            status=random.choice(['approved', 'pending', 'rejected']),
            category=random.choice(['politician', 'celebrity', 'business', 'sports']),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 100)),
            votes_for=random.randint(0, 50),
            votes_against=random.randint(0, 20)
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
    
    for i in range(quantity):
        actor = random.choice(actors)
        oracle_node = random.choice(nodes)
        
        # Create time windows
        start_time = datetime.utcnow() + timedelta(days=random.randint(1, 30))
        end_time = start_time + timedelta(hours=random.randint(1, 24))
        resolution_time = end_time + timedelta(hours=random.randint(1, 72))
        
        bet = Bet(
            actor_id=actor.id,
            predicted_text=f"This is a test prediction statement {i+1} for {actor.name}",
            start_time=start_time,
            end_time=end_time,
            resolution_time=resolution_time,
            oracle_node_id=oracle_node.id,
            status=random.choice(statuses),
            platform_fee=Decimal('0.01'),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
        )
        
        if bet.status == 'resolved':
            bet.actual_text = f"This is the actual statement that was made by {actor.name}"
            bet.similarity_score = random.uniform(0.5, 1.0)
            bet.resolved_at = datetime.utcnow() - timedelta(days=random.randint(1, 5))
        
        db.session.add(bet)

def _generate_test_stakes(quantity):
    """Generate test stakes"""
    bets = Bet.query.all()
    nodes = NodeOperator.query.all()
    
    if not bets or not nodes:
        flash('Need bets and nodes to generate stakes', 'error')
        return
    
    for i in range(quantity):
        bet = random.choice(bets)
        node = random.choice(nodes)
        
        # Avoid duplicate stakes
        existing_stake = Stake.query.filter_by(bet_id=bet.id, staker_node_id=node.id).first()
        if existing_stake:
            continue
            
        stake = Stake(
            bet_id=bet.id,
            staker_node_id=node.id,
            stake_amount=Decimal(random.uniform(10, 1000)),
            prediction_confidence=random.uniform(0.1, 1.0),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        
        # Add payout if bet is resolved
        if bet.status == 'resolved':
            stake.payout_amount = stake.stake_amount * Decimal(random.uniform(0.8, 1.5))
            stake.resolved_at = bet.resolved_at
        
        db.session.add(stake)

def _generate_test_transactions(quantity):
    """Generate test transactions"""
    nodes = NodeOperator.query.all()
    
    if not nodes:
        flash('Need nodes to generate transactions', 'error')
        return
    
    transaction_types = ['stake', 'payout', 'fee', 'penalty']
    
    for i in range(quantity):
        node = random.choice(nodes)
        
        transaction = Transaction(
            transaction_type=random.choice(transaction_types),
            amount=Decimal(random.uniform(1, 1000)),
            from_node_id=node.id,
            to_node_id=random.choice(nodes).id if random.random() > 0.5 else None,
            description=f"Test transaction {i+1}",
            eth_tx_hash=f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}",
            btc_tx_hash=f"{''.join(random.choices(string.hexdigits.lower(), k=64))}",
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
            oracle_node_id=oracle_node.id,
            submitted_text=f"Oracle submission {i+1} for bet {bet.id}",
            confidence_score=random.uniform(0.5, 1.0),
            submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
            verified=random.choice([True, False]),
            consensus_reached=random.choice([True, False])
        )
        
        db.session.add(submission)

def _generate_test_network_metrics(quantity):
    """Generate test network metrics"""
    for i in range(quantity):
        metric = NetworkMetrics(
            active_nodes=random.randint(5, 50),
            total_bets=random.randint(10, 500),
            total_stakes=Decimal(random.uniform(1000, 50000)),
            network_health_score=random.uniform(0.5, 1.0),
            consensus_participation=random.uniform(0.6, 1.0),
            timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 168))
        )
        
        db.session.add(metric)

def _generate_test_time_entries(quantity):
    """Generate test synthetic time entries"""
    nodes = NodeOperator.query.all()
    
    if not nodes:
        flash('Need nodes to generate time entries', 'error')
        return
    
    for i in range(quantity):
        node = random.choice(nodes)
        
        pacific_time = time_sync_service.get_current_pacific_time()
        
        entry = SyntheticTimeEntry(
            node_id=node.id,
            pacific_time=pacific_time,
            utc_time=datetime.utcnow(),
            milliseconds=random.randint(0, 999),
            signature=f"test_signature_{i}",
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
            node_id="simulator-node-002",
            node_type="validator",
            status="active",
            public_key="pk_simulator_002",
            eth_address="0x" + "".join(random.choices(string.hexdigits.lower(), k=40)),
            btc_address="".join(random.choices(string.ascii_letters + string.digits, k=34)),
            stake_amount=Decimal('5000'),
            reputation_score=95,
            last_heartbeat=datetime.utcnow(),
            joined_at=datetime.utcnow()
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
            staker_node_id=node.id,
            stake_amount=Decimal(random.uniform(100, 1000)),
            prediction_confidence=random.uniform(0.7, 1.0),
            created_at=datetime.utcnow()
        )
        db.session.add(stake)
    
    # Create some transactions
    for i in range(3):
        transaction = Transaction(
            transaction_type='stake',
            amount=Decimal(random.uniform(100, 500)),
            from_node_id=node.id,
            description=f"Node {node.node_id} stake transaction",
            eth_tx_hash=f"0x{''.join(random.choices(string.hexdigits.lower(), k=64))}",
            created_at=datetime.utcnow()
        )
        db.session.add(transaction)
    
    # Create time sync entry
    time_entry = SyntheticTimeEntry(
        node_id=node.id,
        pacific_time=time_sync_service.get_current_pacific_time(),
        utc_time=datetime.utcnow(),
        milliseconds=random.randint(0, 999),
        signature=f"node_{node.node_id}_signature",
        created_at=datetime.utcnow()
    )
    db.session.add(time_entry)
    
    db.session.commit()

@test_data_bp.route('/api/node_status/<node_id>')
def get_node_status(node_id):
    """Get status of a specific node"""
    node = NodeOperator.query.filter_by(node_id=node_id).first()
    if not node:
        return jsonify({'error': 'Node not found'}), 404
    
    # Get node statistics
    stakes = Stake.query.filter_by(staker_node_id=node.id).count()
    transactions = Transaction.query.filter_by(from_node_id=node.id).count()
    time_entries = SyntheticTimeEntry.query.filter_by(node_id=node.id).count()
    
    return jsonify({
        'node_id': node.node_id,
        'status': node.status,
        'stake_amount': float(node.stake_amount),
        'reputation_score': node.reputation_score,
        'total_stakes': stakes,
        'total_transactions': transactions,
        'total_time_entries': time_entries,
        'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None
    })
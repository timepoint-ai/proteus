from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, desc
from models import (
    NodeOperator, Actor, Bet, Stake, Transaction, 
    OracleSubmission, SyntheticTimeEntry, NetworkMetrics
)
from app import db
from services.consensus import ConsensusService
from services.ledger import LedgerService
from services.oracle import OracleService
from services.time_sync import TimeSyncService
from services.node_communication import NodeCommunicationService
from services.blockchain import BlockchainService
from config import Config

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

# Initialize services
consensus_service = ConsensusService()
ledger_service = LedgerService()
oracle_service = OracleService()
time_sync_service = TimeSyncService()
node_comm_service = NodeCommunicationService()
blockchain_service = BlockchainService()

@admin_bp.route('/')
def dashboard():
    """Main dashboard view"""
    try:
        # Get basic statistics
        stats = {
            'total_nodes': NodeOperator.query.count(),
            'active_nodes': NodeOperator.query.filter_by(status='active').count(),
            'total_bets': Bet.query.count(),
            'active_bets': Bet.query.filter_by(status='active').count(),
            'total_stakes': Stake.query.count(),
            'approved_actors': Actor.query.filter_by(status='approved').count(),
            'pending_actors': Actor.query.filter_by(status='pending').count(),
            'total_transactions': Transaction.query.count()
        }
        
        # Get recent activity
        recent_bets = Bet.query.order_by(desc(Bet.created_at)).limit(5).all()
        recent_transactions = Transaction.query.order_by(desc(Transaction.created_at)).limit(10).all()
        
        # Get network health
        network_health = consensus_service.get_network_health()
        
        # Get time sync status
        time_status = time_sync_service.get_time_health_status()
        
        # Get ledger summary
        ledger_summary = ledger_service.get_ledger_summary()
        
        return render_template('dashboard.html',
                             stats=stats,
                             recent_bets=recent_bets,
                             recent_transactions=recent_transactions,
                             network_health=network_health,
                             time_status=time_status,
                             ledger_summary=ledger_summary)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', 
                             stats={}, 
                             recent_bets=[], 
                             recent_transactions=[],
                             network_health={},
                             time_status={},
                             ledger_summary={})

@admin_bp.route('/network')
def network_view():
    """Network monitoring view"""
    try:
        # Get all nodes
        nodes = NodeOperator.query.all()
        
        # Get connection status
        connection_status = node_comm_service.get_connection_status()
        
        # Get network metrics
        latest_metrics = NetworkMetrics.query.order_by(desc(NetworkMetrics.timestamp)).first()
        
        # Get consensus health
        consensus_health = consensus_service.get_network_health()
        
        return render_template('network.html',
                             nodes=nodes,
                             connection_status=connection_status,
                             latest_metrics=latest_metrics,
                             consensus_health=consensus_health)
        
    except Exception as e:
        logger.error(f"Error loading network view: {e}")
        flash(f'Error loading network view: {str(e)}', 'error')
        return render_template('network.html',
                             nodes=[],
                             connection_status={},
                             latest_metrics=None,
                             consensus_health={})

@admin_bp.route('/transactions')
def transactions_view():
    """Transactions monitoring view"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Get transactions with pagination
        transactions = Transaction.query.order_by(desc(Transaction.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get transaction statistics
        stats = {
            'total_transactions': Transaction.query.count(),
            'pending_transactions': Transaction.query.filter_by(status='pending').count(),
            'confirmed_transactions': Transaction.query.filter_by(status='confirmed').count(),
            'failed_transactions': Transaction.query.filter_by(status='failed').count()
        }
        
        # Get volume by currency
        eth_volume = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.currency == 'ETH',
            Transaction.status == 'confirmed'
        ).scalar() or 0
        
        btc_volume = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.currency == 'BTC',
            Transaction.status == 'confirmed'
        ).scalar() or 0
        
        # Get platform fees
        eth_fees = db.session.query(func.sum(Transaction.platform_fee)).filter(
            Transaction.currency == 'ETH',
            Transaction.status == 'confirmed'
        ).scalar() or 0
        
        btc_fees = db.session.query(func.sum(Transaction.platform_fee)).filter(
            Transaction.currency == 'BTC',
            Transaction.status == 'confirmed'
        ).scalar() or 0
        
        stats.update({
            'eth_volume': eth_volume,
            'btc_volume': btc_volume,
            'eth_fees': eth_fees,
            'btc_fees': btc_fees
        })
        
        return render_template('transactions.html',
                             transactions=transactions,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading transactions view: {e}")
        flash(f'Error loading transactions view: {str(e)}', 'error')
        return render_template('transactions.html',
                             transactions=None,
                             stats={})

@admin_bp.route('/actors')
def actors_view():
    """Actors management view"""
    try:
        # Get all actors
        actors = Actor.query.all()
        
        # Group by status
        approved_actors = [a for a in actors if a.status == 'approved']
        pending_actors = [a for a in actors if a.status == 'pending']
        rejected_actors = [a for a in actors if a.status == 'rejected']
        
        return render_template('actors.html',
                             approved_actors=approved_actors,
                             pending_actors=pending_actors,
                             rejected_actors=rejected_actors)
        
    except Exception as e:
        logger.error(f"Error loading actors view: {e}")
        flash(f'Error loading actors view: {str(e)}', 'error')
        return render_template('actors.html',
                             approved_actors=[],
                             pending_actors=[],
                             rejected_actors=[])

@admin_bp.route('/bets')
def bets_view():
    """Bets monitoring view"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        per_page = 20
        
        # Build query
        query = Bet.query
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
            
        # Get bets with pagination
        bets = query.order_by(desc(Bet.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get bet statistics
        stats = {
            'total_bets': Bet.query.count(),
            'active_bets': Bet.query.filter_by(status='active').count(),
            'resolved_bets': Bet.query.filter_by(status='resolved').count(),
            'cancelled_bets': Bet.query.filter_by(status='cancelled').count()
        }
        
        return render_template('bets.html',
                             bets=bets,
                             stats=stats,
                             status_filter=status_filter)
        
    except Exception as e:
        logger.error(f"Error loading bets view: {e}")
        flash(f'Error loading bets view: {str(e)}', 'error')
        return render_template('bets.html',
                             bets=None,
                             stats={},
                             status_filter='all')

@admin_bp.route('/oracles')
def oracles_view():
    """Oracle submissions monitoring view"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Get oracle submissions with pagination
        submissions = OracleSubmission.query.order_by(desc(OracleSubmission.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get oracle statistics
        stats = {
            'total_submissions': OracleSubmission.query.count(),
            'consensus_submissions': OracleSubmission.query.filter_by(is_consensus=True).count(),
            'pending_submissions': OracleSubmission.query.filter_by(is_consensus=False).count()
        }
        
        return render_template('oracles.html',
                             submissions=submissions,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading oracles view: {e}")
        flash(f'Error loading oracles view: {str(e)}', 'error')
        return render_template('oracles.html',
                             submissions=None,
                             stats={})

@admin_bp.route('/time-sync')
def time_sync_view():
    """Time synchronization monitoring view"""
    try:
        # Get time sync status
        time_status = time_sync_service.get_time_health_status()
        
        # Get recent time entries
        recent_entries = SyntheticTimeEntry.query.order_by(
            desc(SyntheticTimeEntry.timestamp_ms)
        ).limit(50).all()
        
        # Get reconciliation statistics
        total_entries = SyntheticTimeEntry.query.count()
        reconciled_entries = SyntheticTimeEntry.query.filter_by(reconciled=True).count()
        
        stats = {
            'total_entries': total_entries,
            'reconciled_entries': reconciled_entries,
            'reconciliation_rate': reconciled_entries / max(total_entries, 1),
            'unreconciled_entries': total_entries - reconciled_entries
        }
        
        return render_template('time_sync.html',
                             time_status=time_status,
                             recent_entries=recent_entries,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading time sync view: {e}")
        flash(f'Error loading time sync view: {str(e)}', 'error')
        return render_template('time_sync.html',
                             time_status={},
                             recent_entries=[],
                             stats={})

# API endpoints for real-time updates

@admin_bp.route('/api/stats')
def api_stats():
    """Get current statistics"""
    try:
        stats = {
            'total_nodes': NodeOperator.query.count(),
            'active_nodes': NodeOperator.query.filter_by(status='active').count(),
            'total_bets': Bet.query.count(),
            'active_bets': Bet.query.filter_by(status='active').count(),
            'total_stakes': Stake.query.count(),
            'total_transactions': Transaction.query.count(),
            'timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/network-health')
def api_network_health():
    """Get network health status"""
    try:
        health = consensus_service.get_network_health()
        return jsonify(health)
    except Exception as e:
        logger.error(f"Error getting network health: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/time-status')
def api_time_status():
    """Get time synchronization status"""
    try:
        status = time_sync_service.get_time_health_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting time status: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/ledger-summary')
def api_ledger_summary():
    """Get ledger summary"""
    try:
        summary = ledger_service.get_ledger_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting ledger summary: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/connection-status')
def api_connection_status():
    """Get node connection status"""
    try:
        status = node_comm_service.get_connection_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        return jsonify({'error': str(e)}), 500

# Admin actions

@admin_bp.route('/actions/reconcile', methods=['POST'])
def trigger_reconciliation():
    """Trigger manual reconciliation"""
    try:
        # Get time range from request
        hours = request.form.get('hours', 1, type=int)
        end_time = time_sync_service.get_pacific_time_ms()
        start_time = end_time - (hours * 3600 * 1000)
        
        # Trigger reconciliation
        success = ledger_service.reconcile_time_entries(start_time, end_time)
        
        if success:
            flash(f'Reconciliation triggered for last {hours} hours', 'success')
        else:
            flash('Reconciliation failed', 'error')
            
        return redirect(url_for('admin.dashboard'))
        
    except Exception as e:
        logger.error(f"Error triggering reconciliation: {e}")
        flash(f'Error triggering reconciliation: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/actions/sync-time', methods=['POST'])
def sync_time():
    """Trigger time synchronization"""
    try:
        success = time_sync_service.synchronize_with_network()
        
        if success:
            flash('Time synchronization completed', 'success')
        else:
            flash('Time synchronization failed', 'error')
            
        return redirect(url_for('admin.time_sync_view'))
        
    except Exception as e:
        logger.error(f"Error syncing time: {e}")
        flash(f'Error syncing time: {str(e)}', 'error')
        return redirect(url_for('admin.time_sync_view'))

@admin_bp.route('/actions/cleanup-votes', methods=['POST'])
def cleanup_oracle_votes():
    """Clean up expired oracle votes"""
    try:
        oracle_service.cleanup_expired_votes()
        flash('Oracle vote cleanup completed', 'success')
        return redirect(url_for('admin.oracles_view'))
        
    except Exception as e:
        logger.error(f"Error cleaning up votes: {e}")
        flash(f'Error cleaning up votes: {str(e)}', 'error')
        return redirect(url_for('admin.oracles_view'))

@admin_bp.route('/actions/update-metrics', methods=['POST'])
def update_metrics():
    """Update network metrics"""
    try:
        success = ledger_service.update_network_metrics()
        
        if success:
            flash('Network metrics updated', 'success')
        else:
            flash('Failed to update network metrics', 'error')
            
        return redirect(url_for('admin.network_view'))
        
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        flash(f'Error updating metrics: {str(e)}', 'error')
        return redirect(url_for('admin.network_view'))

@admin_bp.route('/actions/restart-communication', methods=['POST'])
def restart_communication():
    """Restart node communication service"""
    try:
        node_comm_service.stop_communication_service()
        node_comm_service.start_communication_service()
        flash('Node communication service restarted', 'success')
        return redirect(url_for('admin.network_view'))
        
    except Exception as e:
        logger.error(f"Error restarting communication: {e}")
        flash(f'Error restarting communication: {str(e)}', 'error')
        return redirect(url_for('admin.network_view'))

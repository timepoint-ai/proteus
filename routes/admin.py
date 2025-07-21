from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, desc
from models import (
    NodeOperator, Actor, PredictionMarket, Submission, Bet, Transaction, 
    OracleSubmission, SyntheticTimeEntry, NetworkMetrics,
    AIAgentProfile, VerificationModule, BittensorIntegration, TransparencyAudit
)
from app import db
from services.consensus import ConsensusService
from services.ledger import LedgerService
from services.oracle import OracleService
from services.time_sync import TimeSyncService
from services.node_communication import NodeCommunicationService
from services.blockchain import BlockchainService
from services.ai_transparency import AITransparencyService
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
ai_transparency_service = AITransparencyService()

@admin_bp.route('/')
def dashboard():
    """Main dashboard view"""
    try:
        # Get basic statistics
        stats = {
            'total_nodes': NodeOperator.query.count(),
            'active_nodes': NodeOperator.query.filter_by(status='active').count(),
            'total_markets': PredictionMarket.query.count(),
            'active_markets': PredictionMarket.query.filter_by(status='active').count(),
            'total_submissions': Submission.query.count(),
            'total_bets': Bet.query.count(),
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

@admin_bp.route('/markets')
def markets_view():
    """Markets monitoring view"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        per_page = 20
        
        # Build query
        query = PredictionMarket.query
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
            
        # Get markets with pagination
        markets = query.order_by(desc(PredictionMarket.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get market statistics
        stats = {
            'total_markets': PredictionMarket.query.count(),
            'active_markets': PredictionMarket.query.filter_by(status='active').count(),
            'expired_markets': PredictionMarket.query.filter_by(status='expired').count(),
            'validating_markets': PredictionMarket.query.filter_by(status='validating').count(),
            'resolved_markets': PredictionMarket.query.filter_by(status='resolved').count(),
            'total_submissions': Submission.query.count(),
            'total_bets': Bet.query.count()
        }
        
        return render_template('admin/markets.html',
                             markets=markets,
                             stats=stats,
                             status_filter=status_filter)
        
    except Exception as e:
        logger.error(f"Error loading markets view: {e}")
        flash(f'Error loading markets view: {str(e)}', 'error')
        return render_template('admin/markets.html',
                             markets=None,
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
        
        return render_template('admin/oracles.html',
                             submissions=submissions,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading oracles view: {e}")
        flash(f'Error loading oracles view: {str(e)}', 'error')
        return render_template('admin/oracles.html',
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
        
        return render_template('admin/time_sync.html',
                             time_status=time_status,
                             recent_entries=recent_entries,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading time sync view: {e}")
        flash(f'Error loading time sync view: {str(e)}', 'error')
        return render_template('admin/time_sync.html',
                             time_status={},
                             recent_entries=[],
                             stats={})

@admin_bp.route('/ai_transparency')
def ai_transparency_view():
    """AI transparency monitoring view"""
    try:
        # Get statistics
        stats = {
            'ai_agents': AIAgentProfile.query.count(),
            'bittensor_integrations': BittensorIntegration.query.count(),
            'transparent_submissions': Submission.query.filter(Submission.ai_agent_id.isnot(None)).count(),
            'total_bonuses': db.session.query(func.sum(Submission.total_reward_bonus)).scalar() or 0
        }
        
        # Get AI agents with details
        ai_agents = db.session.query(AIAgentProfile).outerjoin(
            BittensorIntegration, AIAgentProfile.agent_id == BittensorIntegration.ai_agent_id
        ).all()
        
        # Calculate statistics for each agent
        for agent in ai_agents:
            agent.total_submissions = Submission.query.filter_by(ai_agent_id=agent.agent_id).count()
            agent.winning_submissions = Submission.query.filter_by(
                ai_agent_id=agent.agent_id, 
                is_winner=True
            ).count()
            agent.total_earned = db.session.query(func.sum(Submission.initial_stake_amount)).filter(
                Submission.ai_agent_id == agent.agent_id,
                Submission.is_winner == True
            ).scalar() or 0
            agent.bittensor = BittensorIntegration.query.filter_by(ai_agent_id=agent.agent_id).first()
        
        # Get recent submissions with transparency modules
        recent_submissions = Submission.query.filter(
            Submission.ai_agent_id.isnot(None)
        ).order_by(desc(Submission.created_at)).limit(10).all()
        
        # Get recent transparency audits
        recent_audits = TransparencyAudit.query.order_by(
            desc(TransparencyAudit.created_at)
        ).limit(10).all()
        
        return render_template('admin/ai_transparency.html',
                             stats=stats,
                             ai_agents=ai_agents,
                             recent_submissions=recent_submissions,
                             recent_audits=recent_audits)
        
    except Exception as e:
        logger.error(f"Error loading AI transparency view: {e}")
        flash(f'Error loading AI transparency view: {str(e)}', 'error')
        return render_template('admin/ai_transparency.html',
                             stats={},
                             ai_agents=[],
                             recent_submissions=[],
                             recent_audits=[])

# API endpoints for real-time updates

@admin_bp.route('/api/stats')
def api_stats():
    """Get current statistics"""
    try:
        stats = {
            'total_nodes': NodeOperator.query.count(),
            'active_nodes': NodeOperator.query.filter_by(status='active').count(),
            'total_markets': PredictionMarket.query.count(),
            'active_markets': PredictionMarket.query.filter_by(status='active').count(),
            'total_submissions': Submission.query.count(),
            'total_bets': Bet.query.count(),
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

@admin_bp.route('/ai_transparency/agent/<agent_id>')
def api_agent_details(agent_id):
    """Get AI agent details"""
    try:
        agent = AIAgentProfile.query.get(agent_id)
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
            
        # Calculate detailed statistics
        total_submissions = Submission.query.filter_by(ai_agent_id=agent.agent_id).count()
        winning_submissions = Submission.query.filter_by(
            ai_agent_id=agent.agent_id, 
            is_winner=True
        ).count()
        
        # Get Bittensor info
        bittensor = BittensorIntegration.query.filter_by(ai_agent_id=agent.agent_id).first()
        
        agent_data = {
            'id': agent.id,
            'agent_id': agent.agent_id,
            'agent_name': agent.agent_name,
            'organization': agent.organization,
            'transparency_score': agent.transparency_score,
            'transparency_level': agent.transparency_level,
            'total_submissions': total_submissions,
            'winning_submissions': winning_submissions,
            'win_rate': round((winning_submissions / max(total_submissions, 1)) * 100, 1),
            'average_accuracy': agent.average_accuracy,
            'total_earned': float(db.session.query(func.sum(Submission.initial_stake_amount)).filter(
                Submission.ai_agent_id == agent.agent_id,
                Submission.is_winner == True
            ).scalar() or 0),
            'bittensor': {
                'subnet_id': bittensor.subnet_id,
                'neuron_type': bittensor.neuron_type,
                'tao_staked': float(bittensor.tao_staked),
                'yuma_score': float(bittensor.yuma_score)
            } if bittensor else None
        }
        
        return jsonify(agent_data)
        
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/ai_transparency/audit/<audit_id>')
def api_audit_details(audit_id):
    """Get audit details"""
    try:
        audit = TransparencyAudit.query.get(audit_id)
        if not audit:
            return jsonify({'error': 'Audit not found'}), 404
            
        audit_data = {
            'id': audit.id,
            'agent_id': audit.agent_id,
            'auditor_name': audit.auditor_name,
            'audit_type': audit.audit_type,
            'audit_passed': audit.audit_passed,
            'findings': audit.findings,
            'created_at': audit.created_at.isoformat(),
            'expires_at': audit.expires_at.isoformat() if audit.expires_at else None
        }
        
        return jsonify(audit_data)
        
    except Exception as e:
        logger.error(f"Error getting audit details: {e}")
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

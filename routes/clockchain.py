from flask import Blueprint, render_template, request, jsonify
from models import SyntheticTimeEntry, Bet, Stake, Transaction, OracleSubmission, NodeOperator, Actor
from sqlalchemy import desc
import json
import logging
from datetime import datetime, timedelta
from services.time_sync import TimeSyncService

logger = logging.getLogger(__name__)
clockchain_bp = Blueprint('clockchain', __name__)
time_sync_service = TimeSyncService()

@clockchain_bp.route('/clockchain')
def clockchain_view():
    """Display the Clockchain timeline view"""
    try:
        # Get current Pacific time
        time_status = time_sync_service.get_time_health_status()
        
        # Get time range parameters
        hours_before = request.args.get('hours_before', 24, type=int)
        hours_after = request.args.get('hours_after', 24, type=int)
        
        # Calculate time range
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(hours=hours_before)
        end_time = current_time + timedelta(hours=hours_after)
        
        # Convert to milliseconds for query
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        # Get time entries in range
        time_entries = SyntheticTimeEntry.query.filter(
            SyntheticTimeEntry.timestamp_ms.between(start_ms, end_ms)
        ).order_by(desc(SyntheticTimeEntry.timestamp_ms)).all()
        
        # Process entries for display
        timeline_events = []
        for entry in time_entries:
            event_data = json.loads(entry.entry_data) if entry.entry_data else {}
            
            # Get related node info
            node = NodeOperator.query.get(entry.node_id) if entry.node_id else None
            
            # Parse event type and create display data
            event = {
                'id': str(entry.id),
                'timestamp_ms': entry.timestamp_ms,
                'timestamp': datetime.fromtimestamp(entry.timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                'type': entry.entry_type,
                'node': {
                    'id': str(node.id) if node else None,
                    'operator_id': node.operator_id if node else 'Unknown',
                    'address': node.node_address[:10] + '...' if node else 'Unknown'
                },
                'data': event_data,
                'reconciled': entry.reconciled,
                'signature': entry.signature[:20] + '...' if entry.signature else None
            }
            
            # Add type-specific details
            if entry.entry_type == 'bet_created' and 'bet_id' in event_data:
                bet = Bet.query.get(event_data['bet_id'])
                if bet:
                    actor = Actor.query.get(bet.actor_id) if bet.actor_id else None
                    event['bet_details'] = {
                        'actor': actor.name if actor else 'Unknown',
                        'predicted_text': bet.predicted_text[:50] + '...' if len(bet.predicted_text) > 50 else bet.predicted_text,
                        'amount': str(bet.initial_stake_amount),
                        'currency': bet.currency
                    }
                    
            elif entry.entry_type == 'stake_placed' and 'stake_id' in event_data:
                stake = Stake.query.get(event_data['stake_id'])
                if stake and stake.bet:
                    actor = Actor.query.get(stake.bet.actor_id) if stake.bet.actor_id else None
                    event['stake_details'] = {
                        'bet_id': str(stake.bet_id),
                        'actor': actor.name if actor else 'Unknown',
                        'amount': str(stake.amount),
                        'currency': stake.currency,
                        'position': stake.position
                    }
                    
            elif entry.entry_type == 'oracle_submission' and 'submission_id' in event_data:
                submission = OracleSubmission.query.get(event_data['submission_id'])
                if submission and submission.bet:
                    actor = Actor.query.get(submission.bet.actor_id) if submission.bet.actor_id else None
                    event['oracle_details'] = {
                        'bet_id': str(submission.bet_id),
                        'actor': actor.name if actor else 'Unknown',
                        'submitted_text': submission.submitted_text[:50] + '...' if len(submission.submitted_text) > 50 else submission.submitted_text,
                        'consensus': submission.is_consensus
                    }
                    
            timeline_events.append(event)
        
        # Get active bets for context
        active_bets = Bet.query.filter_by(status='active').order_by(desc(Bet.created_at)).limit(10).all()
        
        # Process active bets
        active_bets_data = []
        for bet in active_bets:
            actor = Actor.query.get(bet.actor_id) if bet.actor_id else None
            active_bets_data.append({
                'id': str(bet.id),
                'actor': actor.name if actor else 'Unknown',
                'predicted_text': bet.predicted_text[:50] + '...' if len(bet.predicted_text) > 50 else bet.predicted_text,
                'end_time': bet.end_time.strftime('%Y-%m-%d %H:%M') if bet.end_time else 'Unknown',
                'stake_count': Stake.query.filter_by(bet_id=bet.id).count()
            })
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_events=timeline_events,
                             active_bets=active_bets_data,
                             hours_before=hours_before,
                             hours_after=hours_after,
                             current_time_ms=int(current_time.timestamp() * 1000))
        
    except Exception as e:
        logger.error(f"Error loading clockchain view: {e}")
        return render_template('clockchain/timeline.html',
                             time_status={},
                             timeline_events=[],
                             active_bets=[],
                             hours_before=24,
                             hours_after=24,
                             current_time_ms=0)

@clockchain_bp.route('/api/clockchain/events')
def get_clockchain_events():
    """Get clockchain events for a specific time range"""
    try:
        # Get time range from query params
        start_ms = request.args.get('start_ms', type=int)
        end_ms = request.args.get('end_ms', type=int)
        
        if not start_ms or not end_ms:
            return jsonify({'error': 'start_ms and end_ms parameters required'}), 400
            
        # Query events in range
        time_entries = SyntheticTimeEntry.query.filter(
            SyntheticTimeEntry.timestamp_ms.between(start_ms, end_ms)
        ).order_by(desc(SyntheticTimeEntry.timestamp_ms)).limit(100).all()
        
        events = []
        for entry in time_entries:
            event_data = json.loads(entry.entry_data) if entry.entry_data else {}
            events.append({
                'id': str(entry.id),
                'timestamp_ms': entry.timestamp_ms,
                'type': entry.entry_type,
                'data': event_data,
                'reconciled': entry.reconciled
            })
            
        return jsonify({
            'events': events,
            'count': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error getting clockchain events: {e}")
        return jsonify({'error': 'Failed to get events'}), 500
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from models import SyntheticTimeEntry, Bet, Stake, Transaction, OracleSubmission, NodeOperator, Actor
from sqlalchemy import desc
from app import db
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
        
        # Get time range parameters (default 1440 hours = 60 days)
        hours_before = request.args.get('hours_before', 1440, type=int)
        hours_after = request.args.get('hours_after', 1440, type=int)
        
        # Limit to reasonable maximum to prevent memory issues
        max_hours = 10000000
        hours_before = min(hours_before, max_hours)
        hours_after = min(hours_after, max_hours)
        
        # Calculate time range
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(hours=hours_before)
        end_time = current_time + timedelta(hours=hours_after)
        
        # Get all active and recent bets in the time range (limit to prevent overload)
        max_records = 200  # Limit number of records to load
        
        # First count total records
        total_count = Bet.query.filter(
            ((Bet.start_time <= end_time) & (Bet.end_time >= start_time)) |
            (Bet.created_at.between(start_time, end_time))
        ).count()
        
        # Then get limited records
        bets_in_range = Bet.query.filter(
            ((Bet.start_time <= end_time) & (Bet.end_time >= start_time)) |
            (Bet.created_at.between(start_time, end_time))
        ).order_by(Bet.start_time).limit(max_records).all()
        
        has_more_records = total_count > max_records
        
        # Group bets by actor and time period
        timeline_segments = []
        for bet in bets_in_range:
            actor = Actor.query.get(bet.actor_id) if bet.actor_id else None
            
            # Get all stakes for this bet
            stakes = Stake.query.filter_by(bet_id=bet.id).all()
            total_volume = sum(stake.amount for stake in stakes)
            
            # Get competing submissions (other bets for same actor in overlapping time)
            competing_bets = Bet.query.filter(
                Bet.id != bet.id,
                Bet.actor_id == bet.actor_id,
                Bet.start_time <= bet.end_time,
                Bet.end_time >= bet.start_time
            ).all()
            
            # Check if oracle submission is allowed
            oracle_allowed = current_time >= bet.end_time if bet.end_time else False
            time_until_oracle = max(0, (bet.end_time - current_time).total_seconds()) if bet.end_time and not oracle_allowed else 0
            
            segment = {
                'id': str(bet.id),
                'actor': {
                    'id': str(actor.id) if actor else None,
                    'name': actor.name if actor else 'Unknown',
                    'is_unknown': actor.is_unknown if actor else True
                },
                'predicted_text': bet.predicted_text,
                'start_time': bet.start_time,
                'end_time': bet.end_time,
                'start_ms': int(bet.start_time.timestamp() * 1000) if bet.start_time else 0,
                'end_ms': int(bet.end_time.timestamp() * 1000) if bet.end_time else 0,
                'initial_stake': str(bet.initial_stake_amount),
                'currency': bet.currency,
                'status': bet.status,
                'creator_wallet': bet.creator_wallet[:10] + '...' if bet.creator_wallet else '',
                'stake_count': len(stakes),
                'total_volume': str(total_volume),
                'competing_count': len(competing_bets),
                'oracle_allowed': oracle_allowed,
                'time_until_oracle': time_until_oracle,
                'competing_bets': [{
                    'id': str(cb.id),
                    'predicted_text': cb.predicted_text[:50] + '...' if len(cb.predicted_text) > 50 else cb.predicted_text,
                    'creator': cb.creator_wallet[:10] + '...',
                    'volume': str(sum(s.amount for s in Stake.query.filter_by(bet_id=cb.id).all()))
                } for cb in competing_bets[:3]]  # Show max 3 competitors
            }
            
            # Add resolution info if available
            if bet.status == 'resolved':
                segment['resolution'] = {
                    'actual_text': bet.resolution_text,
                    'levenshtein_distance': bet.levenshtein_distance,
                    'resolution_time': bet.resolution_time.isoformat() if bet.resolution_time else None
                }
                
            timeline_segments.append(segment)
        
        # Sort segments by start time
        timeline_segments.sort(key=lambda x: x['start_ms'])
        
        # Calculate timeline boundaries
        min_time_ms = int(start_time.timestamp() * 1000)
        max_time_ms = int(end_time.timestamp() * 1000)
        current_time_ms = int(current_time.timestamp() * 1000)
        
        # Get aggregate statistics
        active_bet_count = Bet.query.filter_by(status='active').count()
        total_bet_volume = db.session.query(db.func.sum(Stake.amount)).scalar() or 0
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_segments=timeline_segments,
                             hours_before=hours_before,
                             hours_after=hours_after,
                             current_time_ms=current_time_ms,
                             min_time_ms=min_time_ms,
                             max_time_ms=max_time_ms,
                             active_bet_count=active_bet_count,
                             total_bet_volume=str(total_bet_volume),
                             total_count=total_count,
                             displayed_count=len(bets_in_range),
                             has_more_records=has_more_records,
                             now_marker_shown=False)
        
    except Exception as e:
        logger.error(f"Error loading clockchain view: {e}")
        return render_template('clockchain/timeline.html',
                             time_status={},
                             timeline_segments=[],
                             hours_before=24,
                             hours_after=24,
                             current_time_ms=0,
                             min_time_ms=0,
                             max_time_ms=0,
                             active_bet_count=0,
                             total_bet_volume='0')

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

@clockchain_bp.route('/clockchain/submission/<submission_id>')
def submission_detail(submission_id):
    """Display detailed view of a single submission"""
    try:
        # Get the bet/submission
        bet = Bet.query.get(submission_id)
        if not bet:
            flash('Submission not found', 'error')
            return redirect(url_for('clockchain.clockchain_view'))
            
        actor = Actor.query.get(bet.actor_id) if bet.actor_id else None
        
        # Get all stakes on this bet
        stakes = Stake.query.filter_by(bet_id=submission_id).order_by(desc(Stake.created_at)).all()
        
        # Process stakes with more details
        stakes_data = []
        for stake in stakes:
            stakes_data.append({
                'id': str(stake.id),
                'staker_wallet': stake.staker_wallet,
                'amount': str(stake.amount),
                'currency': stake.currency,
                'position': stake.position,
                'transaction_hash': stake.transaction_hash,
                'created_at': stake.created_at.strftime('%Y-%m-%d %H:%M:%S') if stake.created_at else ''
            })
            
        # Get competing submissions
        competing_bets = []
        if bet.actor_id:
            competing = Bet.query.filter(
                Bet.id != bet.id,
                Bet.actor_id == bet.actor_id,
                Bet.start_time <= bet.end_time,
                Bet.end_time >= bet.start_time
            ).all()
            
            for cb in competing:
                cb_stakes = Stake.query.filter_by(bet_id=cb.id).all()
                competing_bets.append({
                    'id': str(cb.id),
                    'creator_wallet': cb.creator_wallet,
                    'predicted_text': cb.predicted_text,
                    'start_time': cb.start_time.strftime('%Y-%m-%d %H:%M') if cb.start_time else '',
                    'end_time': cb.end_time.strftime('%Y-%m-%d %H:%M') if cb.end_time else '',
                    'status': cb.status,
                    'stake_count': len(cb_stakes),
                    'total_volume': str(sum(s.amount for s in cb_stakes))
                })
                
        # Get oracle submissions for this bet
        oracle_submissions = OracleSubmission.query.filter_by(bet_id=submission_id).order_by(desc(OracleSubmission.created_at)).all()
        
        # Calculate totals
        total_volume = sum(stake.amount for stake in stakes)
        
        submission_data = {
            'id': str(bet.id),
            'creator_wallet': bet.creator_wallet,
            'actor': {
                'id': str(actor.id) if actor else None,
                'name': actor.name if actor else 'Unknown',
                'is_unknown': actor.is_unknown if actor else True
            },
            'predicted_text': bet.predicted_text,
            'start_time': bet.start_time,
            'end_time': bet.end_time,
            'initial_stake_amount': str(bet.initial_stake_amount),
            'currency': bet.currency,
            'transaction_hash': bet.transaction_hash,
            'status': bet.status,
            'oracle_wallets': json.loads(bet.oracle_wallets) if bet.oracle_wallets else [],
            'platform_fee': str(bet.platform_fee) if bet.platform_fee else '0',
            'created_at': bet.created_at,
            'stakes': stakes_data,
            'total_volume': str(total_volume),
            'stake_count': len(stakes),
            'competing_submissions': competing_bets,
            'oracle_submissions': [{
                'id': str(os.id),
                'oracle_wallet': os.oracle_wallet,
                'submitted_text': os.submitted_text,
                'votes_for': os.votes_for,
                'votes_against': os.votes_against,
                'is_consensus': os.is_consensus,
                'created_at': os.created_at.strftime('%Y-%m-%d %H:%M:%S') if os.created_at else ''
            } for os in oracle_submissions]
        }
        
        # Add resolution info if available
        if bet.status == 'resolved':
            submission_data['resolution'] = {
                'text': bet.resolution_text,
                'levenshtein_distance': bet.levenshtein_distance,
                'resolution_time': bet.resolution_time
            }
            
        return render_template('clockchain/submission_detail.html', submission=submission_data)
        
    except Exception as e:
        logger.error(f"Error loading submission detail: {e}")
        flash('Error loading submission details', 'error')
        return redirect(url_for('clockchain.clockchain_view'))
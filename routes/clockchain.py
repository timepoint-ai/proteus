from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from models import SyntheticTimeEntry, PredictionMarket, Submission, Bet, Transaction, OracleSubmission, NodeOperator, Actor
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
        total_count = PredictionMarket.query.filter(
            ((PredictionMarket.start_time <= end_time) & (PredictionMarket.end_time >= start_time)) |
            (PredictionMarket.created_at.between(start_time, end_time))
        ).count()
        
        # Then get limited records
        markets_in_range = PredictionMarket.query.filter(
            ((PredictionMarket.start_time <= end_time) & (PredictionMarket.end_time >= start_time)) |
            (PredictionMarket.created_at.between(start_time, end_time))
        ).order_by(PredictionMarket.start_time).limit(max_records).all()
        
        has_more_records = total_count > max_records
        
        # Group markets by actor and time period
        timeline_segments = []
        for market in markets_in_range:
            actor = Actor.query.get(market.actor_id) if market.actor_id else None
            
            # Get all submissions for this market
            submissions = Submission.query.filter_by(market_id=market.id).all()
            
            # Calculate total volume from all bets on all submissions
            total_volume = 0
            for submission in submissions:
                bets = Bet.query.filter_by(submission_id=submission.id).all()
                total_volume += sum(bet.amount for bet in bets)
            
            # Get oracle status
            oracle_allowed = current_time >= market.end_time if market.end_time else False
            time_until_oracle = max(0, (market.end_time - current_time).total_seconds()) if market.end_time and not oracle_allowed else 0
            
            # Build segment for each market
            segment = {
                'id': str(market.id),
                'actor': {
                    'id': str(actor.id) if actor else None,
                    'name': actor.name if actor else 'Unknown',
                    'is_unknown': actor.is_unknown if actor else True
                },
                'start_time': market.start_time,
                'end_time': market.end_time,
                'start_ms': int(market.start_time.timestamp() * 1000) if market.start_time else 0,
                'end_ms': int(market.end_time.timestamp() * 1000) if market.end_time else 0,
                'status': market.status,
                'submission_count': len(submissions),
                'total_volume': str(total_volume),
                'oracle_allowed': oracle_allowed,
                'time_until_oracle': time_until_oracle,
                'submissions': []
            }
            
            # Add submission details
            for submission in submissions:
                sub_data = {
                    'id': str(submission.id),
                    'predicted_text': submission.predicted_text if submission.predicted_text else '[No prediction]',
                    'submission_type': submission.submission_type,
                    'creator': submission.creator_wallet[:10] + '...' if submission.creator_wallet else '',
                    'initial_stake': str(submission.initial_stake_amount),
                    'currency': submission.currency,
                    'is_winner': submission.is_winner
                }
                segment['submissions'].append(sub_data)
            
            # Add resolution info if available
            if market.status == 'resolved':
                segment['resolution'] = {
                    'actual_text': market.resolution_text,
                    'resolution_time': market.resolution_time.isoformat() if market.resolution_time else None,
                    'winning_submission_id': str(market.winning_submission_id) if market.winning_submission_id else None
                }
                
            timeline_segments.append(segment)
        
        # Sort segments by start time
        timeline_segments.sort(key=lambda x: x['start_ms'])
        
        # Calculate timeline boundaries
        min_time_ms = int(start_time.timestamp() * 1000)
        max_time_ms = int(end_time.timestamp() * 1000)
        current_time_ms = int(current_time.timestamp() * 1000)
        
        # Get aggregate statistics
        active_market_count = PredictionMarket.query.filter_by(status='active').count()
        total_bet_volume = db.session.query(db.func.sum(Bet.amount)).scalar() or 0
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_segments=timeline_segments,
                             hours_before=hours_before,
                             hours_after=hours_after,
                             current_time_ms=current_time_ms,
                             min_time_ms=min_time_ms,
                             max_time_ms=max_time_ms,
                             active_bet_count=active_market_count,
                             total_bet_volume=str(total_bet_volume),
                             total_count=total_count,
                             displayed_count=len(markets_in_range),
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
                             total_bet_volume='0',
                             total_count=0,
                             displayed_count=0,
                             has_more_records=False,
                             now_marker_shown=False)

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
        
        # Get related transactions
        related_transactions = Transaction.query.filter_by(related_bet_id=submission_id).order_by(desc(Transaction.created_at)).all()
        transactions_data = []
        for tx in related_transactions:
            transactions_data.append({
                'id': str(tx.id),
                'transaction_hash': tx.transaction_hash,
                'transaction_type': tx.transaction_type,
                'amount': str(tx.amount),
                'currency': tx.currency,
                'from_address': tx.from_address,
                'to_address': tx.to_address,
                'status': tx.status,
                'created_at': tx.created_at.strftime('%Y-%m-%d %H:%M:%S') if tx.created_at else ''
            })
        
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
            'created_at': bet.created_at,
            'stakes': stakes_data,
            'total_volume': str(total_volume),
            'stake_count': len(stakes),
            'competing_submissions': competing_bets,
            'related_transactions': transactions_data,
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
        flash(f'Error loading submission details: {str(e)}', 'error')
        return redirect(url_for('clockchain.clockchain_view'))
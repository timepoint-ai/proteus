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
    """Display the Clockchain timeline view with upcoming events first"""
    try:
        # Get current Pacific time
        time_status = time_sync_service.get_time_health_status()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Show 10 items per page
        
        # Calculate time range
        current_time = datetime.utcnow()
        
        # Get upcoming markets first (markets that haven't ended yet)
        upcoming_query = PredictionMarket.query.filter(
            PredictionMarket.end_time > current_time
        ).order_by(PredictionMarket.start_time)
        
        # Get past markets
        past_query = PredictionMarket.query.filter(
            PredictionMarket.end_time <= current_time
        ).order_by(desc(PredictionMarket.end_time))
        
        # Combine queries - upcoming first, then past
        if page == 1:
            # First page shows all upcoming + some past
            upcoming_markets = upcoming_query.all()
            remaining_slots = max(0, per_page - len(upcoming_markets))
            past_markets = past_query.limit(remaining_slots).all()
            markets_in_range = upcoming_markets + past_markets
            total_count = upcoming_query.count() + past_query.count()
        else:
            # Other pages show only past markets
            offset = (page - 1) * per_page - upcoming_query.count()
            markets_in_range = past_query.offset(max(0, offset)).limit(per_page).all()
            total_count = upcoming_query.count() + past_query.count()
        
        has_more_pages = total_count > page * per_page
        
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
            
            # Get the primary submission (original submission)
            primary_submission = next((s for s in submissions if s.submission_type == 'original'), submissions[0] if submissions else None)
            
            # Build segment for each market
            segment = {
                'id': str(market.id),
                'actor': {
                    'id': str(actor.id) if actor else None,
                    'x_username': actor.x_username if actor else 'Unknown',
                    'display_name': actor.display_name if actor else 'Unknown',
                    'verified': actor.verified if actor else False,
                    'follower_count': actor.follower_count if actor else 0,
                    'is_test_account': actor.is_test_account if actor else False
                },
                'start_time': market.start_time,
                'end_time': market.end_time,
                'start_ms': int(market.start_time.timestamp() * 1000) if market.start_time else 0,
                'end_ms': int(market.end_time.timestamp() * 1000) if market.end_time else 0,
                'status': market.status,
                'submission_count': len(submissions),
                'total_volume': str(total_volume),
                'currency': 'BASE',
                'predicted_text': primary_submission.predicted_text if primary_submission else '[No prediction]',
                'creator_wallet': primary_submission.creator_wallet[:10] + '...' if primary_submission and primary_submission.creator_wallet else 'Unknown',
                'initial_stake': str(primary_submission.initial_stake_amount) if primary_submission else '0',
                'stake_count': sum(len(Bet.query.filter_by(submission_id=sub.id).all()) for sub in submissions),
                'oracle_allowed': oracle_allowed,
                'time_until_oracle': time_until_oracle,
                'submissions': [],
                'competing_bets': []
            }
            
            # Add submission details and competing submissions
            for submission in submissions:
                sub_data = {
                    'id': str(submission.id),
                    'predicted_text': submission.predicted_text if submission.predicted_text else '[No prediction]',
                    'submission_type': submission.submission_type,
                    'creator': submission.creator_wallet[:10] + '...' if submission.creator_wallet else '',
                    'initial_stake': str(submission.initial_stake_amount),
                    'currency': 'BASE',
                    'is_winner': submission.is_winner
                }
                segment['submissions'].append(sub_data)
                
                # Add to competing bets if not the primary submission
                if submission != primary_submission:
                    bets = Bet.query.filter_by(submission_id=submission.id).all()
                    volume = sum(bet.amount for bet in bets)
                    segment['competing_bets'].append({
                        'id': str(submission.id),
                        'predicted_text': submission.predicted_text or '[No prediction]',
                        'creator': submission.creator_wallet[:10] + '...' if submission.creator_wallet else 'Unknown',
                        'volume': str(volume)
                    })
            
            # Add resolution info if available
            if market.status == 'resolved':
                # Get winning submission to get Levenshtein distance
                winning_submission = Submission.query.get(market.winning_submission_id) if market.winning_submission_id else None
                segment['resolution'] = {
                    'actual_text': market.resolution_text,
                    'resolution_time': market.resolution_time.isoformat() if market.resolution_time else None,
                    'winning_submission_id': str(market.winning_submission_id) if market.winning_submission_id else None,
                    'levenshtein_distance': winning_submission.levenshtein_distance if winning_submission else None
                }
                
            timeline_segments.append(segment)
        
        # Sort segments by start time
        timeline_segments.sort(key=lambda x: x['start_ms'])
        
        # Calculate timeline boundaries for display
        current_time_ms = int(current_time.timestamp() * 1000)
        
        # Get aggregate statistics
        active_market_count = PredictionMarket.query.filter_by(status='active').count()
        total_bet_volume = db.session.query(db.func.sum(Bet.amount)).scalar() or 0
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_segments=timeline_segments,
                             current_page=page,
                             has_more_pages=has_more_pages,
                             current_time_ms=current_time_ms,
                             active_bet_count=active_market_count,
                             total_bet_volume=str(total_bet_volume),
                             total_count=total_count,
                             displayed_count=len(markets_in_range),
                             view_type='all')
        
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

@clockchain_bp.route('/clockchain/markets/create')
def create_market():
    """Display market creation form"""
    return render_template('markets/create.html')

@clockchain_bp.route('/clockchain/market/<market_id>')
def market_detail(market_id):
    """Display detailed view of a prediction market"""
    try:
        market = PredictionMarket.query.get(market_id)
        if not market:
            flash('Market not found', 'error')
            return redirect(url_for('clockchain.clockchain_view'))
            
        actor = Actor.query.get(market.actor_id) if market.actor_id else None
        submissions = Submission.query.filter_by(market_id=market.id).all()
        
        # Get all bets for this market with transaction status
        all_bets = []
        total_volume = 0
        for submission in submissions:
            bets = Bet.query.filter_by(submission_id=submission.id).all()
            for bet in bets:
                # Get transaction status for this bet
                transaction = Transaction.query.filter_by(
                    transaction_hash=bet.transaction_hash
                ).first()
                
                # Use transaction status if available, otherwise use bet status
                if transaction:
                    bet.display_status = transaction.status
                else:
                    bet.display_status = bet.status or 'pending'
                
                total_volume += bet.amount
                all_bets.append({
                    'submission': submission,
                    'bet': bet,
                    'submission_text': submission.predicted_text[:50] + '...' if submission.predicted_text and len(submission.predicted_text) > 50 else submission.predicted_text or '[No prediction]'
                })
        
        return render_template('clockchain/market_detail.html',
                             market=market,
                             actor=actor,
                             submissions=submissions,
                             all_bets=all_bets,
                             total_volume=total_volume)
                             
    except Exception as e:
        logger.error(f"Error loading market detail: {e}")
        flash('Error loading market details', 'error')
        return redirect(url_for('clockchain.clockchain_view'))


@clockchain_bp.route('/clockchain/submission/<submission_id>')
def submission_detail(submission_id):
    """Display detailed view of a submission"""
    try:
        submission = Submission.query.get(submission_id)
        if not submission:
            flash('Submission not found', 'error')
            return redirect(url_for('clockchain.clockchain_view'))
            
        market = PredictionMarket.query.get(submission.market_id)
        if not market:
            flash('Market not found', 'error')
            return redirect(url_for('clockchain.clockchain_view'))
            
        actor = Actor.query.get(market.actor_id) if market.actor_id else None
        
        # Get all bets for this submission
        bets = Bet.query.filter_by(submission_id=submission.id).all()
        total_volume = sum(bet.amount for bet in bets)
        
        # Get competing submissions
        competing_submissions = Submission.query.filter(
            Submission.market_id == market.id,
            Submission.id != submission.id
        ).all()
        
        # Get transactions for this submission
        transactions = Transaction.query.filter_by(
            reference_id=str(submission.id),
            reference_type='submission'
        ).all()
        
        # Get oracle submissions for this market
        oracle_submissions = OracleSubmission.query.filter_by(
            market_id=market.id
        ).order_by(OracleSubmission.created_at.desc()).all()
        
        submission_data = {
            'id': str(submission.id),
            'creator_wallet': submission.creator_wallet,
            'actor': {
                'id': str(actor.id) if actor else None,
                'name': actor.name if actor else 'Unknown',
                'is_unknown': actor.is_unknown if actor else True
            },
            'predicted_text': submission.predicted_text,
            'submission_type': submission.submission_type,
            'market': {
                'id': str(market.id),
                'start_time': market.start_time,
                'end_time': market.end_time,
                'status': market.status,
                'resolution_text': market.resolution_text,
                'winning_submission_id': str(market.winning_submission_id) if market.winning_submission_id else None
            },
            'initial_stake_amount': str(submission.initial_stake_amount),
            'currency': 'BASE',
            'transaction_hash': submission.transaction_hash,
            'is_winner': submission.is_winner,
            'levenshtein_distance': submission.levenshtein_distance,
            'created_at': submission.created_at,
            'bets': [{
                'id': str(bet.id),
                'bettor_wallet': bet.bettor_wallet,
                'amount': str(bet.amount),
                'currency': bet.currency,
                'status': bet.status,
                'created_at': bet.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for bet in bets],
            'total_volume': str(total_volume),
            'bet_count': len(bets),
            'competing_submissions': [{
                'id': str(comp.id),
                'predicted_text': comp.predicted_text or '[No prediction]',
                'creator_wallet': comp.creator_wallet,
                'initial_stake': str(comp.initial_stake_amount),
                'currency': comp.currency,
                'is_winner': comp.is_winner,
                'levenshtein_distance': comp.levenshtein_distance
            } for comp in competing_submissions],
            'related_transactions': [{
                'id': str(tx.id),
                'hash': tx.transaction_hash,
                'currency': tx.currency,
                'amount': str(tx.amount),
                'status': tx.status,
                'created_at': tx.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for tx in transactions],
            'oracle_submissions': [{
                'id': str(os.id),
                'oracle_wallet': os.oracle_wallet,
                'submitted_text': os.submitted_text,
                'votes_for': os.votes_for,
                'votes_against': os.votes_against,
                'is_consensus': os.is_consensus,
                'status': os.status,
                'created_at': os.created_at.strftime('%Y-%m-%d %H:%M:%S') if os.created_at else ''
            } for os in oracle_submissions]
        }
        
        # Add resolution info if available
        if market.status == 'resolved':
            submission_data['resolution'] = {
                'text': market.resolution_text,
                'winning_submission_id': str(market.winning_submission_id) if market.winning_submission_id else None,
                'resolution_time': market.resolution_time
            }
            
        return render_template('clockchain/submission_detail.html', submission=submission_data)
        
    except Exception as e:
        logger.error(f"Error loading submission detail: {e}")
        flash(f'Error loading submission details: {str(e)}', 'error')
        return redirect(url_for('clockchain.clockchain_view'))


@clockchain_bp.route('/clockchain/resolved')
def resolved_view():
    """Display resolved prediction markets"""
    try:
        time_status = time_sync_service.get_time_health_status()
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get resolved markets
        query = PredictionMarket.query.filter_by(status='resolved').order_by(desc(PredictionMarket.resolution_time))
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        markets_in_range = paginated.items
        total_count = paginated.total
        has_more_pages = paginated.has_next
        
        # Build timeline segments (reuse the same logic)
        timeline_segments = []
        for market in markets_in_range:
            actor = Actor.query.get(market.actor_id) if market.actor_id else None
            submissions = Submission.query.filter_by(market_id=market.id).all()
            
            # Calculate total volume
            total_volume = 0
            for submission in submissions:
                bets = Bet.query.filter_by(submission_id=submission.id).all()
                total_volume += sum(bet.amount for bet in bets)
            
            primary_submission = next((s for s in submissions if s.submission_type == 'original'), submissions[0] if submissions else None)
            winning_submission = Submission.query.get(market.winning_submission_id) if market.winning_submission_id else None
            
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
                'currency': 'BASE',
                'predicted_text': primary_submission.predicted_text if primary_submission else '[No prediction]',
                'resolution': {
                    'actual_text': market.resolution_text,
                    'resolution_time': market.resolution_time.isoformat() if market.resolution_time else None,
                    'winning_submission_id': str(market.winning_submission_id) if market.winning_submission_id else None,
                    'levenshtein_distance': winning_submission.levenshtein_distance if winning_submission else None
                }
            }
            timeline_segments.append(segment)
        
        active_market_count = PredictionMarket.query.filter_by(status='active').count()
        total_bet_volume = db.session.query(db.func.sum(Bet.amount)).scalar() or 0
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_segments=timeline_segments,
                             current_page=page,
                             has_more_pages=has_more_pages,
                             current_time_ms=int(datetime.utcnow().timestamp() * 1000),
                             active_bet_count=active_market_count,
                             total_bet_volume=str(total_bet_volume),
                             total_count=total_count,
                             displayed_count=len(markets_in_range),
                             view_type='resolved')
    except Exception as e:
        logger.error(f"Error loading resolved view: {e}")
        return render_template('clockchain/timeline.html',
                             time_status={},
                             timeline_segments=[],
                             current_page=1,
                             has_more_pages=False,
                             current_time_ms=0,
                             active_bet_count=0,
                             total_bet_volume='0',
                             total_count=0,
                             displayed_count=0,
                             view_type='resolved')


@clockchain_bp.route('/clockchain/active')
def active_view():
    """Display active prediction markets"""
    try:
        time_status = time_sync_service.get_time_health_status()
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get active markets
        query = PredictionMarket.query.filter_by(status='active').order_by(PredictionMarket.start_time)
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        markets_in_range = paginated.items
        total_count = paginated.total
        has_more_pages = paginated.has_next
        
        # Build timeline segments
        timeline_segments = []
        current_time = datetime.utcnow()
        
        for market in markets_in_range:
            actor = Actor.query.get(market.actor_id) if market.actor_id else None
            submissions = Submission.query.filter_by(market_id=market.id).all()
            
            # Calculate total volume
            total_volume = 0
            for submission in submissions:
                bets = Bet.query.filter_by(submission_id=submission.id).all()
                total_volume += sum(bet.amount for bet in bets)
            
            oracle_allowed = current_time >= market.end_time if market.end_time else False
            time_until_oracle = max(0, (market.end_time - current_time).total_seconds()) if market.end_time and not oracle_allowed else 0
            
            primary_submission = next((s for s in submissions if s.submission_type == 'original'), submissions[0] if submissions else None)
            
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
                'currency': 'BASE',
                'predicted_text': primary_submission.predicted_text if primary_submission else '[No prediction]',
                'oracle_allowed': oracle_allowed,
                'time_until_oracle': time_until_oracle
            }
            timeline_segments.append(segment)
        
        active_market_count = total_count
        total_bet_volume = db.session.query(db.func.sum(Bet.amount)).scalar() or 0
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_segments=timeline_segments,
                             current_page=page,
                             has_more_pages=has_more_pages,
                             current_time_ms=int(datetime.utcnow().timestamp() * 1000),
                             active_bet_count=active_market_count,
                             total_bet_volume=str(total_bet_volume),
                             total_count=total_count,
                             displayed_count=len(markets_in_range),
                             view_type='active')
    except Exception as e:
        logger.error(f"Error loading active view: {e}")
        return render_template('clockchain/timeline.html',
                             time_status={},
                             timeline_segments=[],
                             current_page=1,
                             has_more_pages=False,
                             current_time_ms=0,
                             active_bet_count=0,
                             total_bet_volume='0',
                             total_count=0,
                             displayed_count=0,
                             view_type='active')
        
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
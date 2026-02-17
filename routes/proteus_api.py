"""API endpoints for Proteus pagination"""
import logging
from flask import Blueprint, request, jsonify
# from models import PredictionMarket, Actor, Submission, Bet  # Phase 7: Models removed
# from app import db  # Phase 7: Database removed
from datetime import datetime, timezone
# from sqlalchemy import desc  # Phase 7: SQLAlchemy removed

logger = logging.getLogger(__name__)
proteus_api_bp = Blueprint('proteus_api', __name__)


@proteus_api_bp.route('/api/proteus/markets')
def api_markets():
    """API endpoint for paginated all markets"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        current_time = datetime.now(timezone.utc)
        
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
        
        # Build response segments
        segments = []
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
            winning_submission = Submission.query.get(market.winning_submission_id) if market.winning_submission_id else None
            
            segment = {
                'id': str(market.id),
                'actor': {
                    'id': str(actor.id) if actor else None,
                    'name': actor.name if actor else 'Unknown',
                    'is_unknown': actor.is_unknown if actor else True
                },
                'start_time': market.start_time.isoformat() if market.start_time else None,
                'end_time': market.end_time.isoformat() if market.end_time else None,
                'status': market.status,
                'submission_count': len(submissions),
                'total_volume': str(total_volume),
                'currency': primary_submission.currency if primary_submission else 'ETH',
                'predicted_text': primary_submission.predicted_text if primary_submission else '[No prediction]',
                'oracle_allowed': oracle_allowed,
                'time_until_oracle': time_until_oracle,
                'resolution': {
                    'actual_text': market.resolution_text,
                    'resolution_time': market.resolution_time.isoformat() if market.resolution_time else None,
                    'winning_submission_id': str(market.winning_submission_id) if market.winning_submission_id else None,
                    'levenshtein_distance': winning_submission.levenshtein_distance if winning_submission else None
                } if market.status == 'resolved' else None
            }
            segments.append(segment)
        
        return jsonify({
            'segments': segments,
            'has_more': has_more_pages,
            'page': page,
            'total_count': total_count
        })
    except Exception as e:
        logger.error(f"Error in API markets: {e}")
        return jsonify({'error': str(e)}), 500


@proteus_api_bp.route('/api/proteus/resolved')
def api_resolved():
    """API endpoint for paginated resolved markets"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        query = PredictionMarket.query.filter_by(status='resolved').order_by(desc(PredictionMarket.resolution_time))
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        segments = []
        for market in paginated.items:
            actor = Actor.query.get(market.actor_id) if market.actor_id else None
            submissions = Submission.query.filter_by(market_id=market.id).all()
            
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
                'start_time': market.start_time.isoformat() if market.start_time else None,
                'end_time': market.end_time.isoformat() if market.end_time else None,
                'status': market.status,
                'submission_count': len(submissions),
                'total_volume': str(total_volume),
                'currency': primary_submission.currency if primary_submission else 'ETH',
                'predicted_text': primary_submission.predicted_text if primary_submission else '[No prediction]',
                'resolution': {
                    'actual_text': market.resolution_text,
                    'resolution_time': market.resolution_time.isoformat() if market.resolution_time else None,
                    'winning_submission_id': str(market.winning_submission_id) if market.winning_submission_id else None,
                    'levenshtein_distance': winning_submission.levenshtein_distance if winning_submission else None
                }
            }
            segments.append(segment)
        
        return jsonify({
            'segments': segments,
            'has_more': paginated.has_next,
            'page': page,
            'total_count': paginated.total
        })
    except Exception as e:
        logger.error(f"Error in API resolved: {e}")
        return jsonify({'error': str(e)}), 500


@proteus_api_bp.route('/api/proteus/active')
def api_active():
    """API endpoint for paginated active markets"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        current_time = datetime.now(timezone.utc)
        
        query = PredictionMarket.query.filter_by(status='active').order_by(PredictionMarket.start_time)
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        segments = []
        for market in paginated.items:
            actor = Actor.query.get(market.actor_id) if market.actor_id else None
            submissions = Submission.query.filter_by(market_id=market.id).all()
            
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
                'start_time': market.start_time.isoformat() if market.start_time else None,
                'end_time': market.end_time.isoformat() if market.end_time else None,
                'status': market.status,
                'submission_count': len(submissions),
                'total_volume': str(total_volume),
                'currency': primary_submission.currency if primary_submission else 'ETH',
                'predicted_text': primary_submission.predicted_text if primary_submission else '[No prediction]',
                'oracle_allowed': oracle_allowed,
                'time_until_oracle': time_until_oracle
            }
            segments.append(segment)
        
        return jsonify({
            'segments': segments,
            'has_more': paginated.has_next,
            'page': page,
            'total_count': paginated.total
        })
    except Exception as e:
        logger.error(f"Error in API active: {e}")
        return jsonify({'error': str(e)}), 500
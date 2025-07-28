"""Routes for actors pages"""
import logging
from flask import Blueprint, render_template, abort
from models import Actor, PredictionMarket, Submission, Bet
from app import db
from datetime import datetime
from sqlalchemy import desc

logger = logging.getLogger(__name__)
actors_bp = Blueprint('actors', __name__)


@actors_bp.route('/actors')
def actors_list():
    """Display list of all actors"""
    try:
        # Get all actors with their statistics
        actors = Actor.query.order_by(Actor.name).all()
        
        actor_stats = []
        for actor in actors:
            # Get market statistics
            markets = PredictionMarket.query.filter_by(actor_id=actor.id).all()
            active_markets = [m for m in markets if m.status == 'active']
            resolved_markets = [m for m in markets if m.status == 'resolved']
            
            # Calculate total volume
            total_volume = 0
            for market in markets:
                submissions = Submission.query.filter_by(market_id=market.id).all()
                for submission in submissions:
                    bets = Bet.query.filter_by(submission_id=submission.id).all()
                    total_volume += sum(bet.amount for bet in bets)
            
            actor_stats.append({
                'actor': actor,
                'total_markets': len(markets),
                'active_markets': len(active_markets),
                'resolved_markets': len(resolved_markets),
                'total_volume': total_volume
            })
        
        return render_template('actors/list.html', actor_stats=actor_stats)
    except Exception as e:
        logger.error(f"Error loading actors list: {e}")
        return render_template('actors/list.html', actor_stats=[])


@actors_bp.route('/actors/<int:actor_id>')
def actor_detail(actor_id):
    """Display detailed page for a specific actor"""
    try:
        actor = Actor.query.get_or_404(actor_id)
        
        # Get all markets for this actor
        markets_query = PredictionMarket.query.filter_by(actor_id=actor.id)
        
        # Separate active and resolved markets
        active_markets = markets_query.filter_by(status='active').order_by(PredictionMarket.start_time).all()
        resolved_markets = markets_query.filter_by(status='resolved').order_by(desc(PredictionMarket.resolution_time)).limit(10).all()
        
        # Calculate statistics
        total_markets = markets_query.count()
        total_volume = 0
        total_predictions = 0
        
        # Process markets to get detailed info
        active_market_data = []
        resolved_market_data = []
        
        for market in active_markets:
            submissions = Submission.query.filter_by(market_id=market.id).all()
            market_volume = 0
            
            for submission in submissions:
                bets = Bet.query.filter_by(submission_id=submission.id).all()
                market_volume += sum(bet.amount for bet in bets)
            
            total_volume += market_volume
            total_predictions += len(submissions)
            
            primary_submission = next((s for s in submissions if s.submission_type == 'original'), submissions[0] if submissions else None)
            
            active_market_data.append({
                'market': market,
                'submissions': submissions,
                'volume': market_volume,
                'primary_submission': primary_submission
            })
        
        for market in resolved_markets:
            submissions = Submission.query.filter_by(market_id=market.id).all()
            market_volume = 0
            
            for submission in submissions:
                bets = Bet.query.filter_by(submission_id=submission.id).all()
                market_volume += sum(bet.amount for bet in bets)
            
            total_volume += market_volume
            total_predictions += len(submissions)
            
            primary_submission = next((s for s in submissions if s.submission_type == 'original'), submissions[0] if submissions else None)
            winning_submission = Submission.query.get(market.winning_submission_id) if market.winning_submission_id else None
            
            resolved_market_data.append({
                'market': market,
                'submissions': submissions,
                'volume': market_volume,
                'primary_submission': primary_submission,
                'winning_submission': winning_submission
            })
        
        return render_template('actors/detail.html',
                             actor=actor,
                             active_markets=active_market_data,
                             resolved_markets=resolved_market_data,
                             total_markets=total_markets,
                             total_volume=total_volume,
                             total_predictions=total_predictions)
                             
    except Exception as e:
        logger.error(f"Error loading actor detail: {e}")
        abort(404)
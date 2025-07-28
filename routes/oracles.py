"""Routes for oracle pages"""
import logging
from flask import Blueprint, render_template, abort
from models import OracleSubmission, PredictionMarket, Actor, Submission, NodeOperator
from app import db
from datetime import datetime
from sqlalchemy import desc, func

logger = logging.getLogger(__name__)
oracles_bp = Blueprint('oracles', __name__)


@oracles_bp.route('/oracles')
def oracles_list():
    """Display list of all active oracles and their submission history"""
    try:
        # Get unique oracle wallets with their submission counts
        oracle_stats = db.session.query(
            OracleSubmission.oracle_wallet,
            func.count(OracleSubmission.id).label('total_submissions'),
            func.sum(func.cast(OracleSubmission.is_consensus, db.Integer)).label('consensus_count'),
            func.max(OracleSubmission.created_at).label('last_submission')
        ).group_by(OracleSubmission.oracle_wallet).all()
        
        oracle_data = []
        for oracle_wallet, total_submissions, consensus_count, last_submission in oracle_stats:
            # Get recent submissions for this oracle
            recent_submissions = OracleSubmission.query.filter_by(
                oracle_wallet=oracle_wallet
            ).order_by(desc(OracleSubmission.created_at)).limit(5).all()
            
            # Calculate accuracy rate
            accuracy_rate = (consensus_count / total_submissions * 100) if total_submissions > 0 else 0
            
            oracle_data.append({
                'wallet': oracle_wallet,
                'total_submissions': total_submissions,
                'consensus_count': consensus_count or 0,
                'accuracy_rate': accuracy_rate,
                'last_submission': last_submission,
                'recent_submissions': recent_submissions
            })
        
        # Sort by total submissions
        oracle_data.sort(key=lambda x: x['total_submissions'], reverse=True)
        
        return render_template('oracles/list.html', oracle_data=oracle_data)
    except Exception as e:
        logger.error(f"Error loading oracles list: {e}")
        return render_template('oracles/list.html', oracle_data=[])


@oracles_bp.route('/oracles/<oracle_wallet>')
def oracle_detail(oracle_wallet):
    """Display detailed page for a specific oracle"""
    try:
        # Get all submissions for this oracle
        submissions = OracleSubmission.query.filter_by(
            oracle_wallet=oracle_wallet
        ).order_by(desc(OracleSubmission.created_at)).all()
        
        if not submissions:
            abort(404)
        
        # Calculate statistics
        total_submissions = len(submissions)
        consensus_count = sum(1 for s in submissions if s.is_consensus)
        accuracy_rate = (consensus_count / total_submissions * 100) if total_submissions > 0 else 0
        
        # Group submissions by status
        pending_submissions = [s for s in submissions if s.status == 'pending']
        consensus_submissions = [s for s in submissions if s.status == 'consensus']
        rejected_submissions = [s for s in submissions if s.status == 'rejected']
        
        # Get detailed submission data
        submission_data = []
        for submission in submissions[:50]:  # Limit to 50 most recent
            # Get related market and actor
            market = PredictionMarket.query.get(submission.market_id) if submission.market_id else None
            actor = Actor.query.get(market.actor_id) if market and market.actor_id else None
            
            submission_data.append({
                'submission': submission,
                'market': market,
                'actor': actor
            })
        
        oracle_info = {
            'wallet': oracle_wallet,
            'total_submissions': total_submissions,
            'consensus_count': consensus_count,
            'accuracy_rate': accuracy_rate,
            'pending_count': len(pending_submissions),
            'rejected_count': len(rejected_submissions)
        }
        
        return render_template('oracles/detail.html', 
                             oracle_info=oracle_info,
                             submission_data=submission_data)
    except Exception as e:
        logger.error(f"Error loading oracle detail: {e}")
        abort(404)
"""
Script to recalculate and fix all Levenshtein distances for resolved markets
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import PredictionMarket, Submission
from services.text_analysis import TextAnalysisService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_levenshtein_distances():
    """Recalculate all Levenshtein distances for resolved markets"""
    with app.app_context():
        text_service = TextAnalysisService()
        
        # Get all resolved markets
        resolved_markets = PredictionMarket.query.filter_by(status='resolved').all()
        
        fixed_count = 0
        total_count = 0
        
        for market in resolved_markets:
            if not market.resolution_text:
                logger.warning(f"Market {market.id} has no resolution text, skipping")
                continue
                
            logger.info(f"Processing market {market.id}")
            
            # Get all submissions for this market
            submissions = Submission.query.filter_by(market_id=market.id).all()
            
            for submission in submissions:
                total_count += 1
                
                # Skip null submissions
                if submission.predicted_text is None:
                    logger.info(f"  Submission {submission.id} is null, skipping")
                    continue
                
                # Calculate Levenshtein distance
                distance = text_service.calculate_levenshtein_distance(
                    submission.predicted_text,
                    market.resolution_text
                )
                
                # Update if different from current value
                if submission.levenshtein_distance != distance:
                    old_distance = submission.levenshtein_distance
                    submission.levenshtein_distance = distance
                    fixed_count += 1
                    logger.info(f"  Updated submission {submission.id}: {old_distance} -> {distance}")
                    logger.info(f"    Predicted: '{submission.predicted_text}'")
                    logger.info(f"    Actual: '{market.resolution_text}'")
                else:
                    logger.info(f"  Submission {submission.id} already has correct distance: {distance}")
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"\nFixed {fixed_count} out of {total_count} submissions")
        logger.info("Levenshtein distance recalculation complete!")

if __name__ == "__main__":
    fix_levenshtein_distances()
"""
Create test actors using public X.com accounts
These are real public figures for testing purposes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Actor
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test actors using real public X.com accounts
TEST_ACTORS = [
    {
        'x_username': 'elonmusk',
        'display_name': 'Elon Musk',
        'bio': 'CEO of Tesla, SpaceX, X Corp',
        'verified': True,
        'follower_count': 150000000,
        'is_test_account': True
    },
    {
        'x_username': 'taylorswift13',
        'display_name': 'Taylor Swift',
        'bio': 'Singer, Songwriter',
        'verified': True,
        'follower_count': 95000000,
        'is_test_account': True
    },
    {
        'x_username': 'BillGates',
        'display_name': 'Bill Gates',
        'bio': 'Co-chair of the Bill & Melinda Gates Foundation',
        'verified': True,
        'follower_count': 64000000,
        'is_test_account': True
    },
    {
        'x_username': 'Oprah',
        'display_name': 'Oprah Winfrey',
        'bio': 'Media mogul, philanthropist',
        'verified': True,
        'follower_count': 43000000,
        'is_test_account': True
    },
    {
        'x_username': 'GordonRamsay',
        'display_name': 'Gordon Ramsay',
        'bio': 'Chef, TV personality',
        'verified': True,
        'follower_count': 15000000,
        'is_test_account': True
    },
    {
        'x_username': 'MrBeast',
        'display_name': 'MrBeast',
        'bio': 'YouTuber, Philanthropist',
        'verified': True,
        'follower_count': 25000000,
        'is_test_account': True
    },
    {
        'x_username': 'cristiano',
        'display_name': 'Cristiano Ronaldo',
        'bio': 'Professional footballer',
        'verified': True,
        'follower_count': 110000000,
        'is_test_account': True
    },
    {
        'x_username': 'jimmyfallon',
        'display_name': 'Jimmy Fallon',
        'bio': 'Host of The Tonight Show',
        'verified': True,
        'follower_count': 52000000,
        'is_test_account': True
    }
]

def create_test_actors():
    """Create test actors in the database"""
    with app.app_context():
        try:
            created_count = 0
            updated_count = 0
            
            for actor_data in TEST_ACTORS:
                # Check if actor already exists
                existing_actor = Actor.query.filter_by(x_username=actor_data['x_username']).first()
                
                if existing_actor:
                    # Update existing actor
                    existing_actor.display_name = actor_data['display_name']
                    existing_actor.bio = actor_data['bio']
                    existing_actor.verified = actor_data['verified']
                    existing_actor.follower_count = actor_data['follower_count']
                    existing_actor.is_test_account = actor_data['is_test_account']
                    existing_actor.last_sync = datetime.utcnow()
                    existing_actor.status = 'active'
                    updated_count += 1
                    logger.info(f"Updated actor: @{actor_data['x_username']}")
                else:
                    # Create new actor
                    new_actor = Actor(
                        x_username=actor_data['x_username'],
                        display_name=actor_data['display_name'],
                        bio=actor_data['bio'],
                        verified=actor_data['verified'],
                        follower_count=actor_data['follower_count'],
                        is_test_account=actor_data['is_test_account'],
                        status='active',
                        last_sync=datetime.utcnow()
                    )
                    db.session.add(new_actor)
                    created_count += 1
                    logger.info(f"Created actor: @{actor_data['x_username']}")
            
            db.session.commit()
            
            logger.info(f"\nSummary:")
            logger.info(f"Created {created_count} new actors")
            logger.info(f"Updated {updated_count} existing actors")
            logger.info(f"Total test actors: {len(TEST_ACTORS)}")
            
            # List all actors
            all_actors = Actor.query.order_by(Actor.follower_count.desc()).all()
            logger.info(f"\nAll actors in database:")
            for actor in all_actors:
                logger.info(f"  @{actor.x_username} - {actor.display_name} ({actor.follower_count:,} followers)")
            
        except Exception as e:
            logger.error(f"Error creating test actors: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_test_actors()
"""
Create test actors for X.com username system
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Actor
from datetime import datetime
import random

# Sample actors with X.com usernames
SAMPLE_ACTORS = [
    ("elonmusk", "Elon Musk", "CEO of Tesla and SpaceX, tech entrepreneur"),
    ("taylorswift13", "Taylor Swift", "Global pop star and songwriter"),
    ("BillGates", "Bill Gates", "Microsoft founder and philanthropist"),
    ("Oprah", "Oprah Winfrey", "Media mogul and talk show host"),
    ("GordonRamsay", "Gordon Ramsay", "Chef, TV personality"),
    ("MrBeast", "MrBeast", "YouTuber, Philanthropist"),
    ("cristiano", "Cristiano Ronaldo", "Professional footballer"),
    ("jimmyfallon", "Jimmy Fallon", "Host of The Tonight Show")
]

def create_test_actors():
    """Create test actors with X.com usernames"""
    with app.app_context():
        try:
            # Clear existing test actors
            print("Clearing existing test actors...")
            Actor.query.filter_by(is_test_account=True).delete()
            db.session.commit()
            
            # Create actors one by one
            print("Creating test actors...")
            for x_username, display_name, bio in SAMPLE_ACTORS:
                # Check if actor already exists
                existing = Actor.query.filter_by(x_username=x_username).first()
                if existing:
                    print(f"Actor @{x_username} already exists, skipping...")
                    continue
                
                actor = Actor(
                    x_username=x_username,
                    display_name=display_name,
                    bio=bio,
                    verified=True,
                    follower_count=random.randint(1000000, 100000000),
                    is_test_account=True,
                    status='active',
                    last_sync=datetime.utcnow()
                )
                db.session.add(actor)
                db.session.commit()  # Commit each actor individually
                print(f"Created actor: @{x_username} - {display_name}")
            
            # Display summary
            total_actors = Actor.query.filter_by(is_test_account=True).count()
            print(f"\nTotal test actors created: {total_actors}")
            
            print("\nTest actors:")
            for actor in Actor.query.filter_by(is_test_account=True).all():
                print(f"  @{actor.x_username} - {actor.display_name} ({actor.follower_count:,} followers)")
                
        except Exception as e:
            print(f"Error creating test actors: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_test_actors()
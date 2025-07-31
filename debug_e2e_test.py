#!/usr/bin/env python3
"""Debug script for E2E test"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, PredictionMarket, Submission, Bet, Transaction, OracleSubmission, Actor
from routes.test_manager import run_full_e2e_test, add_test_step
from app import app

def debug_e2e():
    """Run E2E test with detailed debugging"""
    with app.app_context():
        results = []
        
        # Clean up test data first
        print("Cleaning up old test data...")
        PredictionMarket.query.filter_by(twitter_handle='test_actor').delete()
        Actor.query.filter_by(twitter_handle='test_actor').delete()
        db.session.commit()
        
        # Run the full E2E test
        print("\nRunning E2E test...")
        results = run_full_e2e_test(results)
        
        # Print results
        print("\n=== E2E Test Results ===")
        for result in results:
            status = result['status']
            name = result['name']
            error = result.get('error', '')
            details = result.get('details', {})
            
            if status == 'failed':
                print(f"❌ {name}: {status}")
                if error:
                    print(f"   Error: {error}")
            elif status == 'passed':
                print(f"✅ {name}: {status}")
            else:
                print(f"ℹ️  {name}: {status}")
            
            if details and name in ['Calculate Submission Distances', 'Determine Winner']:
                print(f"   Details: {details}")
        
        # Check if market resolution failed
        if any(r['name'] == 'Market Resolution Test' and r['status'] == 'failed' for r in results):
            print("\n=== Debugging Market Resolution ===")
            market = PredictionMarket.query.filter_by(twitter_handle='test_actor').first()
            if market:
                print(f"Market ID: {market.id}")
                print(f"Market Status: {market.status}")
                print(f"Submissions: {len(market.submissions)}")
                
                oracle = OracleSubmission.query.filter_by(market_id=market.id).first()
                if oracle:
                    print(f"Oracle Text: {oracle.submitted_text}")
                
                for i, sub in enumerate(market.submissions):
                    print(f"\nSubmission {i+1}:")
                    print(f"  ID: {sub.id}")
                    print(f"  Predicted Text: {sub.predicted_text}")
                    print(f"  Levenshtein Distance: {sub.levenshtein_distance}")
                    print(f"  Is Winner: {sub.is_winner}")

if __name__ == "__main__":
    debug_e2e()
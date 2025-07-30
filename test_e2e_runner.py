#!/usr/bin/env python3
"""
E2E Test Runner for BASE Sepolia integration
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_e2e_tests():
    """Run complete E2E test workflow"""
    from app import app, db
    from models import Actor, PredictionMarket, Submission, Bet, OracleSubmission, Transaction
    from services.blockchain_base import BaseBlockchainService
    from routes.test_manager import (
        run_wallet_connection_test,
        run_market_creation_test,
        run_submission_creation_test,
        run_bet_placement_test,
        run_oracle_submission_test,
        run_market_resolution_test,
        clean_test_data
    )
    
    with app.app_context():
        logger.info("Starting E2E Test Suite")
        
        # Initialize results
        results = {
            'test_case': 'Full E2E Test',
            'status': 'running',
            'steps': [],
            'errors': [],
            'started_at': datetime.utcnow().isoformat()
        }
        
        # Clean any existing test data
        logger.info("Cleaning existing test data...")
        try:
            clean_test_data()
            logger.info("Test data cleaned successfully")
        except Exception as e:
            logger.warning(f"Error cleaning test data: {e}")
        
        # Test 1: Wallet Connection
        logger.info("\n=== Test 1: Wallet Connection ===")
        wallet_results = run_wallet_connection_test({'steps': [], 'errors': []})
        if wallet_results['errors']:
            logger.error(f"Wallet Connection Test Failed: {wallet_results['errors']}")
            return
        logger.info("✓ Wallet Connection Test Passed")
        
        # Test 2: Market Creation
        logger.info("\n=== Test 2: Market Creation ===")
        market_results = run_market_creation_test({'steps': [], 'errors': []})
        if market_results['errors']:
            logger.error(f"Market Creation Test Failed: {market_results['errors']}")
            return
        logger.info("✓ Market Creation Test Passed")
        
        # Test 3: Submission Creation
        logger.info("\n=== Test 3: Submission Creation ===")
        submission_results = run_submission_creation_test({'steps': [], 'errors': []})
        if submission_results['errors']:
            logger.error(f"Submission Creation Test Failed: {submission_results['errors']}")
            return
        logger.info("✓ Submission Creation Test Passed")
        
        # Test 4: Bet Placement
        logger.info("\n=== Test 4: Bet Placement ===")
        bet_results = run_bet_placement_test({'steps': [], 'errors': []})
        if bet_results['errors']:
            logger.error(f"Bet Placement Test Failed: {bet_results['errors']}")
            for error in bet_results['errors']:
                logger.error(f"  Error: {error}")
            return
        logger.info("✓ Bet Placement Test Passed")
        
        # Test 5: Oracle Submission
        logger.info("\n=== Test 5: Oracle Submission ===")
        oracle_results = run_oracle_submission_test({'steps': [], 'errors': []})
        if oracle_results['errors']:
            logger.error(f"Oracle Submission Test Failed: {oracle_results['errors']}")
            return
        logger.info("✓ Oracle Submission Test Passed")
        
        # Test 6: Market Resolution
        logger.info("\n=== Test 6: Market Resolution ===")
        resolution_results = run_market_resolution_test({'steps': [], 'errors': []})
        if resolution_results['errors']:
            logger.error(f"Market Resolution Test Failed: {resolution_results['errors']}")
            return
        logger.info("✓ Market Resolution Test Passed")
        
        # Clean up test data
        logger.info("\n=== Cleaning Up Test Data ===")
        clean_test_data()
        logger.info("✓ Test data cleaned")
        
        logger.info("\n✅ ALL E2E TESTS PASSED!")

if __name__ == "__main__":
    run_e2e_tests()
#!/usr/bin/env python3
"""
Migration script to update database schema for BASE blockchain integration
Removes multi-currency support and adds X.com oracle fields
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from app import app, db
from models import Transaction, NetworkMetrics, OracleSubmission
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Perform database migration for BASE blockchain integration"""
    with app.app_context():
        try:
            logger.info("Starting database migration to BASE blockchain...")
            
            # Check if migration is needed
            inspector = db.inspect(db.engine)
            
            # Check Transaction table
            transaction_columns = [col['name'] for col in inspector.get_columns('transactions')]
            
            if 'currency' in transaction_columns:
                logger.info("Removing currency column from transactions table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE transactions DROP COLUMN currency"))
                    conn.commit()
                    
            # Add BASE-specific columns to transactions if not exists
            if 'gas_used' not in transaction_columns:
                logger.info("Adding BASE-specific columns to transactions...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN gas_used BIGINT"))
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN gas_price NUMERIC(20, 8)"))
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN nonce INTEGER"))
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN contract_address VARCHAR(128)"))
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN method_signature VARCHAR(256)"))
                    conn.commit()
                    
            # Check NetworkMetrics table
            metrics_columns = [col['name'] for col in inspector.get_columns('network_metrics')]
            
            if 'total_volume_btc' in metrics_columns:
                logger.info("Updating NetworkMetrics for BASE-only support...")
                with db.engine.connect() as conn:
                    # Drop BTC columns
                    conn.execute(text("ALTER TABLE network_metrics DROP COLUMN total_volume_btc"))
                    conn.execute(text("ALTER TABLE network_metrics DROP COLUMN platform_fees_btc"))
                    
                    # Rename ETH columns to BASE
                    conn.execute(text("ALTER TABLE network_metrics RENAME COLUMN total_volume_eth TO total_volume_base"))
                    conn.execute(text("ALTER TABLE network_metrics RENAME COLUMN platform_fees_eth TO platform_fees_base"))
                    
                    # Add X.com metrics
                    conn.execute(text("ALTER TABLE network_metrics ADD COLUMN total_tweets_verified INTEGER DEFAULT 0"))
                    conn.execute(text("ALTER TABLE network_metrics ADD COLUMN average_levenshtein_distance FLOAT DEFAULT 0.0"))
                    conn.commit()
                    
            # Check PredictionMarket table for X.com fields
            market_columns = [col['name'] for col in inspector.get_columns('prediction_markets')]
            
            if 'twitter_handle' not in market_columns:
                logger.info("Adding X.com fields to prediction_markets...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN twitter_handle VARCHAR(256)"))
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN target_tweet_id VARCHAR(128)"))
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN xcom_only BOOLEAN DEFAULT TRUE"))
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN contract_address VARCHAR(128)"))
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN market_creation_tx VARCHAR(128)"))
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN total_volume NUMERIC(20, 8) DEFAULT 0"))
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN platform_fee_collected NUMERIC(20, 8) DEFAULT 0"))
                    conn.execute(text("ALTER TABLE prediction_markets ADD COLUMN creator_wallet VARCHAR(128)"))
                    conn.commit()
            
            # Check Submission table for BASE blockchain fields
            submission_columns = [col['name'] for col in inspector.get_columns('submissions')]
            
            logger.info("Checking submissions table for missing BASE blockchain fields...")
            with db.engine.connect() as conn:
                if 'base_tx_hash' not in submission_columns:
                    logger.info("Adding base_tx_hash to submissions...")
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN base_tx_hash VARCHAR(128)"))
                    
                if 'is_ai_agent' not in submission_columns:
                    logger.info("Adding is_ai_agent to submissions...")
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN is_ai_agent BOOLEAN DEFAULT FALSE"))
                    
                if 'ai_agent_id' not in submission_columns:
                    logger.info("Adding ai_agent_id to submissions...")
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN ai_agent_id VARCHAR(256)"))
                    
                if 'transparency_level' not in submission_columns:
                    logger.info("Adding transparency_level to submissions...")
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN transparency_level INTEGER DEFAULT 0"))
                    
                if 'total_reward_bonus' not in submission_columns:
                    logger.info("Adding total_reward_bonus to submissions...")
                    conn.execute(text("ALTER TABLE submissions ADD COLUMN total_reward_bonus NUMERIC(5, 4) DEFAULT 0"))
                    
                conn.commit()
            
            # Check OracleSubmission table for X.com fields
            oracle_columns = [col['name'] for col in inspector.get_columns('oracle_submissions')]
            
            if 'tweet_id' not in oracle_columns:
                logger.info("Adding X.com fields to oracle_submissions...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE oracle_submissions ADD COLUMN tweet_id VARCHAR(128)"))
                    conn.execute(text("ALTER TABLE oracle_submissions ADD COLUMN tweet_verification TEXT"))
                    conn.execute(text("ALTER TABLE oracle_submissions ADD COLUMN screenshot_proof TEXT"))
                    conn.execute(text("ALTER TABLE oracle_submissions ADD COLUMN screenshot_ipfs VARCHAR(256)"))
                    conn.execute(text("ALTER TABLE oracle_submissions ADD COLUMN screenshot_hash VARCHAR(128)"))
                    conn.execute(text("ALTER TABLE oracle_submissions ADD COLUMN tweet_timestamp TIMESTAMP"))
                    conn.commit()
                    
            # Update existing transactions to remove currency dependency
            logger.info("Updating existing transaction records...")
            with db.engine.connect() as conn:
                # Set default values for new columns
                conn.execute(text("UPDATE transactions SET gas_used = 21000 WHERE gas_used IS NULL"))
                conn.execute(text("UPDATE transactions SET gas_price = 1000000000 WHERE gas_price IS NULL"))
                conn.commit()
                
            logger.info("Database migration completed successfully!")
            
            # Create indexes for performance
            logger.info("Creating indexes for better performance...")
            with db.engine.connect() as conn:
                # Index for X.com tweet lookups
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oracle_tweet_id ON oracle_submissions(tweet_id)"))
                
                # Index for BASE transaction lookups
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transaction_block ON transactions(block_number)"))
                
                # Index for contract interactions
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transaction_contract ON transactions(contract_address)"))
                conn.commit()
                
            logger.info("Indexes created successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate_database()
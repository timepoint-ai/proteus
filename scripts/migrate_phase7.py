#!/usr/bin/env python3
"""
Phase 7 Database Migration Script
Adds consensus_percentage field to oracle_submissions and creates contract_events table
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from sqlalchemy import text, inspect
from app import app, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run Phase 7 database migrations"""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Check if consensus_percentage field exists in oracle_submissions
            oracle_columns = [col['name'] for col in inspector.get_columns('oracle_submissions')]
            
            if 'consensus_percentage' not in oracle_columns:
                logger.info("Adding consensus_percentage field to oracle_submissions...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE oracle_submissions ADD COLUMN consensus_percentage FLOAT DEFAULT 0.0"))
                    conn.commit()
                logger.info("✅ Added consensus_percentage field")
            else:
                logger.info("✅ consensus_percentage field already exists")
            
            # Check if contract_events table exists
            existing_tables = inspector.get_table_names()
            
            if 'contract_events' not in existing_tables:
                logger.info("Creating contract_events table...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE contract_events (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            event_type VARCHAR(100) NOT NULL,
                            contract_address VARCHAR(42) NOT NULL,
                            transaction_hash VARCHAR(66),
                            block_number INTEGER,
                            event_data JSON,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    conn.commit()
                logger.info("✅ Created contract_events table")
            else:
                logger.info("✅ contract_events table already exists")
            
            # Update existing oracle submissions to calculate consensus percentage
            logger.info("Updating consensus percentages for existing oracle submissions...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE oracle_submissions 
                    SET consensus_percentage = CASE 
                        WHEN (votes_for + votes_against) > 0 
                        THEN (votes_for::float / (votes_for + votes_against)) * 100
                        ELSE 0.0
                    END
                """))
                conn.commit()
            logger.info("✅ Updated consensus percentages")
            
            logger.info("Phase 7 migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    return True


if __name__ == "__main__":
    if run_migration():
        logger.info("Migration successful!")
    else:
        logger.error("Migration failed!")
        sys.exit(1)
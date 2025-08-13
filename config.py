import os
from datetime import timedelta

# ⚠️  DEPRECATED: This config file is being phased out
# Use config_chain.py for chain-only configuration

class Config:
    # ===== PHASE 4 CLEANUP: Database configs removed =====
    # The following database configurations have been removed:
    # - SQLALCHEMY_DATABASE_URI (no database)
    # - SQLALCHEMY_ENGINE_OPTIONS (no database)
    # - SQLALCHEMY_TRACK_MODIFICATIONS (no database)
    # - SECRET_KEY (no Flask sessions)
    
    # Keep minimal config for backward compatibility during transition
    # These will be removed in final cleanup
    
    # Celery configuration (kept for background blockchain monitoring)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Node configuration
    NODE_OPERATOR_ID = os.environ.get('NODE_OPERATOR_ID') or 'default-node-001'
    NODE_PRIVATE_KEY = os.environ.get('NODE_PRIVATE_KEY') or 'dev-private-key'
    NODE_PUBLIC_KEY = os.environ.get('NODE_PUBLIC_KEY') or 'dev-public-key'
    
    # BASE Blockchain configuration
    BASE_RPC_URL = os.environ.get('BASE_RPC_URL') or 'https://mainnet.base.org'
    BASE_SEPOLIA_RPC_URL = os.environ.get('BASE_SEPOLIA_RPC_URL') or 'https://sepolia.base.org'
    NETWORK = os.environ.get('NETWORK') or 'testnet'  # 'testnet' or 'mainnet'
    
    # Chain IDs
    BASE_MAINNET_CHAIN_ID = 8453
    BASE_SEPOLIA_CHAIN_ID = 84532
    
    # Network configuration
    KNOWN_NODES = os.environ.get('KNOWN_NODES', '').split(',') if os.environ.get('KNOWN_NODES') else []
    CONSENSUS_THRESHOLD = float(os.environ.get('CONSENSUS_THRESHOLD', '0.51'))  # 51% majority
    
    # Platform configuration
    PLATFORM_FEE = float(os.environ.get('PLATFORM_FEE', '7'))  # 7% platform fee
    
    # Node operator configuration
    NODE_OPERATOR_KEY = os.environ.get('NODE_OPERATOR_KEY')
    NODE_STAKE_AMOUNT = 100  # BASE tokens required for node staking
    P2P_PORT = int(os.environ.get('P2P_PORT', '8545'))
    NODE_ENDPOINT = os.environ.get('NODE_ENDPOINT', f'ws://0.0.0.0:{P2P_PORT}')
    
    # X.com Oracle configuration
    XCOM_API_URL = os.environ.get('XCOM_API_URL') or 'https://api.x.com/v2'
    XCOM_BEARER_TOKEN = os.environ.get('XCOM_BEARER_TOKEN')
    SCREENSHOT_SERVICE_URL = os.environ.get('SCREENSHOT_SERVICE_URL') or 'http://localhost:3000'
    IPFS_GATEWAY_URL = os.environ.get('IPFS_GATEWAY_URL') or 'https://ipfs.io/ipfs/'
    
    # Time configuration
    PACIFIC_TIMEZONE = 'America/Los_Angeles'
    
    # Oracle configuration
    ORACLE_VOTE_TIMEOUT = int(os.environ.get('ORACLE_VOTE_TIMEOUT', '3600'))  # 1 hour
    
    # Reconciliation configuration
    RECONCILIATION_INTERVAL = int(os.environ.get('RECONCILIATION_INTERVAL', '10'))  # 10 seconds
    
    # Text analysis configuration
    LEVENSHTEIN_THRESHOLD = float(os.environ.get('LEVENSHTEIN_THRESHOLD', '0.8'))  # 80% similarity

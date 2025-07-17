import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///clockchain.db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Node configuration
    NODE_OPERATOR_ID = os.environ.get('NODE_OPERATOR_ID') or 'default-node-001'
    NODE_PRIVATE_KEY = os.environ.get('NODE_PRIVATE_KEY') or 'dev-private-key'
    NODE_PUBLIC_KEY = os.environ.get('NODE_PUBLIC_KEY') or 'dev-public-key'
    
    # Blockchain configuration
    ETH_RPC_URL = os.environ.get('ETH_RPC_URL') or 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID'
    BTC_RPC_URL = os.environ.get('BTC_RPC_URL') or 'https://blockstream.info/api'
    
    # Network configuration
    KNOWN_NODES = os.environ.get('KNOWN_NODES', '').split(',') if os.environ.get('KNOWN_NODES') else []
    CONSENSUS_THRESHOLD = float(os.environ.get('CONSENSUS_THRESHOLD', '0.51'))  # 51% majority
    
    # Platform configuration
    PLATFORM_FEE_RATE = float(os.environ.get('PLATFORM_FEE_RATE', '0.01'))  # 1%
    
    # Time configuration
    PACIFIC_TIMEZONE = 'America/Los_Angeles'
    
    # Oracle configuration
    ORACLE_VOTE_TIMEOUT = int(os.environ.get('ORACLE_VOTE_TIMEOUT', '3600'))  # 1 hour
    
    # Reconciliation configuration
    RECONCILIATION_INTERVAL = int(os.environ.get('RECONCILIATION_INTERVAL', '10'))  # 10 seconds
    
    # Text analysis configuration
    LEVENSHTEIN_THRESHOLD = float(os.environ.get('LEVENSHTEIN_THRESHOLD', '0.8'))  # 80% similarity

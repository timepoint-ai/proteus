"""
Phase 4: Chain-only configuration
All database and session-related configurations removed
Only blockchain, caching, and necessary services remain
"""

import os

class ChainConfig:
    """
    Chain-only configuration for the decentralized platform
    No database, no sessions, pure blockchain
    """
    
    # ============== BLOCKCHAIN CONFIGURATION ==============
    # BASE Network settings
    # Production RPC (Alchemy/QuickNode) preferred, public RPC as fallback
    BASE_RPC_URL = os.environ.get('BASE_RPC_URL', 'https://sepolia.base.org')
    BASE_MAINNET_RPC_URL = os.environ.get('BASE_MAINNET_RPC_URL', 'https://mainnet.base.org')
    NETWORK = os.environ.get('NETWORK', 'testnet')  # 'testnet' or 'mainnet'

    # Production RPC providers (set these for mainnet deployment)
    ALCHEMY_API_KEY = os.environ.get('ALCHEMY_API_KEY')
    QUICKNODE_ENDPOINT = os.environ.get('QUICKNODE_ENDPOINT')

    @property
    def PRODUCTION_RPC_URL(self):
        """Get production RPC URL, preferring Alchemy > QuickNode > public."""
        if self.ALCHEMY_API_KEY:
            if self.NETWORK == 'mainnet':
                return f'https://base-mainnet.g.alchemy.com/v2/{self.ALCHEMY_API_KEY}'
            return f'https://base-sepolia.g.alchemy.com/v2/{self.ALCHEMY_API_KEY}'
        if self.QUICKNODE_ENDPOINT:
            return self.QUICKNODE_ENDPOINT
        return self.ACTIVE_RPC_URL
    
    # Chain IDs
    BASE_MAINNET_CHAIN_ID = 8453
    BASE_SEPOLIA_CHAIN_ID = 84532
    
    @property
    def ACTIVE_CHAIN_ID(self):
        """Get the active chain ID based on network setting"""
        return self.BASE_SEPOLIA_CHAIN_ID if self.NETWORK == 'testnet' else self.BASE_MAINNET_CHAIN_ID
    
    @property
    def ACTIVE_RPC_URL(self):
        """Get the active RPC URL based on network setting"""
        return self.BASE_RPC_URL if self.NETWORK == 'testnet' else self.BASE_MAINNET_RPC_URL
    
    # Contract deployment files
    DEPLOYMENT_FILE = 'deployment-base-sepolia.json' if NETWORK == 'testnet' else 'deployment-base-mainnet.json'
    
    # ============== REDIS CACHING (PERFORMANCE) ==============
    # Keep Redis for caching chain data and reducing RPC calls
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    REDIS_CACHE_TTL = int(os.environ.get('REDIS_CACHE_TTL', '300'))  # 5 minutes cache

    # ============== AUTH STORE CONFIGURATION ==============
    # TTLs for Redis-backed auth stores (in seconds)
    NONCE_TTL = int(os.environ.get('NONCE_TTL', '300'))  # 5 minutes
    OTP_TTL = int(os.environ.get('OTP_TTL', '300'))  # 5 minutes
    OTP_MAX_SEND_PER_WINDOW = int(os.environ.get('OTP_MAX_SEND_PER_WINDOW', '3'))  # Max OTP sends per window
    OTP_SEND_WINDOW = int(os.environ.get('OTP_SEND_WINDOW', '900'))  # 15 minute window
    OTP_MAX_VERIFY_ATTEMPTS = int(os.environ.get('OTP_MAX_VERIFY_ATTEMPTS', '5'))  # Max wrong attempts
    OTP_VERIFY_LOCKOUT = int(os.environ.get('OTP_VERIFY_LOCKOUT', '900'))  # 15 min lockout
    
    # ============== CELERY TASK QUEUE ==============
    # Keep Celery for background blockchain monitoring
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', REDIS_URL + '/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', REDIS_URL + '/0')
    
    # ============== NODE OPERATOR CONFIGURATION ==============
    # Node identity (chain-only, no database storage)
    NODE_OPERATOR_ADDRESS = os.environ.get('NODE_OPERATOR_ADDRESS')
    NODE_PRIVATE_KEY = os.environ.get('NODE_PRIVATE_KEY')  # For signing transactions only
    
    # P2P Network settings
    P2P_PORT = int(os.environ.get('P2P_PORT', '8545'))
    NODE_ENDPOINT = os.environ.get('NODE_ENDPOINT', f'ws://0.0.0.0:{P2P_PORT}')
    KNOWN_NODES = os.environ.get('KNOWN_NODES', '').split(',') if os.environ.get('KNOWN_NODES') else []
    
    # ============== ORACLE CONFIGURATION ==============
    # X.com Oracle settings
    XCOM_API_URL = os.environ.get('XCOM_API_URL', 'https://api.x.com/v2')
    XCOM_BEARER_TOKEN = os.environ.get('XCOM_BEARER_TOKEN')
    SCREENSHOT_SERVICE_URL = os.environ.get('SCREENSHOT_SERVICE_URL', 'http://localhost:3000')
    
    # IPFS for decentralized storage
    IPFS_GATEWAY_URL = os.environ.get('IPFS_GATEWAY_URL', 'https://ipfs.io/ipfs/')
    
    # Oracle consensus settings
    ORACLE_VOTE_TIMEOUT = int(os.environ.get('ORACLE_VOTE_TIMEOUT', '3600'))  # 1 hour
    CONSENSUS_THRESHOLD = float(os.environ.get('CONSENSUS_THRESHOLD', '0.66'))  # 66% majority
    
    # ============== PLATFORM CONFIGURATION ==============
    # Platform economics (on-chain enforced)
    PLATFORM_FEE = float(os.environ.get('PLATFORM_FEE', '7'))  # 7% platform fee
    NODE_STAKE_AMOUNT = int(os.environ.get('NODE_STAKE_AMOUNT', '100'))  # BASE tokens for staking
    
    # Text analysis settings
    LEVENSHTEIN_THRESHOLD = float(os.environ.get('LEVENSHTEIN_THRESHOLD', '0.8'))  # 80% similarity
    
    # Time configuration
    PACIFIC_TIMEZONE = 'America/Los_Angeles'
    
    # ============== JWT CONFIGURATION (WALLET AUTH) ==============
    # For wallet-based authentication (Phase 2)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '24'))
    
    # ============== MONITORING CONFIGURATION ==============
    # Chain monitoring intervals
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL', '60'))  # 60 seconds
    CONTRACT_SYNC_INTERVAL = int(os.environ.get('CONTRACT_SYNC_INTERVAL', '30'))  # 30 seconds
    GAS_PRICE_CHECK_INTERVAL = int(os.environ.get('GAS_PRICE_CHECK_INTERVAL', '300'))  # 5 minutes
    
    # ============== DEPRECATED CONFIGURATIONS ==============
    # These are explicitly NOT included in chain-only config:
    # - DATABASE_URL (no database)
    # - SQLALCHEMY_* (no ORM)
    # - FLASK_SECRET_KEY (no sessions)
    # - SESSION_* (no session management)
    # - Any user account related configs
    
    @classmethod
    def validate_config(cls):
        """Validate that required configurations are set"""
        errors = []
        
        # Check blockchain configs
        if not cls.BASE_RPC_URL and cls.NETWORK == 'testnet':
            errors.append("BASE_RPC_URL required for testnet")
        if not cls.BASE_MAINNET_RPC_URL and cls.NETWORK == 'mainnet':
            errors.append("BASE_MAINNET_RPC_URL required for mainnet")
            
        # Check if deployment file exists
        if not os.path.exists(cls.DEPLOYMENT_FILE):
            errors.append(f"Deployment file {cls.DEPLOYMENT_FILE} not found")
            
        # Warn about optional configs
        warnings = []
        if not cls.NODE_OPERATOR_ADDRESS:
            warnings.append("NODE_OPERATOR_ADDRESS not set - node features disabled")
        if not cls.XCOM_BEARER_TOKEN:
            warnings.append("XCOM_BEARER_TOKEN not set - oracle features limited")
            
        return errors, warnings
    
    @classmethod
    def get_config_summary(cls):
        """Get a summary of current configuration"""
        return {
            'network': cls.NETWORK,
            'chain_id': cls.ACTIVE_CHAIN_ID,
            'rpc_url': cls.ACTIVE_RPC_URL,
            'deployment_file': cls.DEPLOYMENT_FILE,
            'redis_enabled': bool(cls.REDIS_URL),
            'node_operator': bool(cls.NODE_OPERATOR_ADDRESS),
            'oracle_enabled': bool(cls.XCOM_BEARER_TOKEN),
            'jwt_auth_enabled': True,
            'database_enabled': False,  # Always false in chain-only mode
            'session_management': False  # Always false in chain-only mode
        }

# Create a singleton instance
chain_config = ChainConfig()
import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from celery import Celery
import redis

# Phase 7: All SQLAlchemy imports removed - chain-only mode

# Configure structured logging (must be done before any other imports that use logging)
from utils.logging_config import configure_structlog, get_logger

configure_structlog()

# Phase 7: Database classes removed - chain-only mode

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

# Initialize Redis — prefer REDIS_URL (Railway/production), fall back to host/port
_redis_url = os.environ.get('REDIS_URL')
if _redis_url:
    redis_client = redis.from_url(_redis_url, decode_responses=True)
else:
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
        decode_responses=True
    )

def create_app():
    logger = get_logger(__name__)
    app = Flask(__name__)
    # Chain-only mode: No sessions needed with JWT auth
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Set secret key for flash messages only (not for sessions)
    app.secret_key = os.environ.get("SESSION_SECRET", "phase7-blockchain-only-flash-messages")
    
    # Load configuration
    # Phase 4: Use chain-only configuration
    from config_chain import chain_config
    
    # Apply chain configuration to Flask app
    app.config['CELERY_BROKER_URL'] = chain_config.CELERY_BROKER_URL
    app.config['CELERY_RESULT_BACKEND'] = chain_config.CELERY_RESULT_BACKEND
    
    # Chain-only mode: No database needed
    # db.init_app(app) - REMOVED: No database in chain-only mode
    
    # Initialize Celery
    celery = make_celery(app)
    app.celery = celery
    
    # Register blueprints
    from routes.api import api_bp
    from routes.admin import admin_bp
    from routes.auth import auth_bp  # Phase 2: Wallet-only authentication
    from routes.api_chain import api_chain_bp  # Phase 3: Chain-only API routes
    from routes.embedded_auth import embedded_auth  # Coinbase Embedded Wallet authentication

    from routes.proteus import proteus_bp
    from routes.ai_agent_api import ai_agent_api_bp, init_limiter
    from routes.marketing import marketing_bp
    from routes.actors import actors_bp
    from routes.proteus_api import proteus_api_bp
    from routes.oracles import oracles_bp
    from routes.base_api import base_api_bp
    from routes.oracle_manual import oracle_manual_bp
    from routes.node_api import node_api_bp
    from routes.docs import docs_bp
    
    app.register_blueprint(marketing_bp)
    app.register_blueprint(auth_bp)  # Phase 2: Register auth routes
    app.register_blueprint(embedded_auth)  # Coinbase Embedded Wallet authentication
    app.register_blueprint(docs_bp)
    app.register_blueprint(api_chain_bp, url_prefix='/api/chain')  # Phase 3: Chain-only routes
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(base_api_bp, url_prefix='/api/base')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    app.register_blueprint(proteus_bp)
    app.register_blueprint(ai_agent_api_bp, url_prefix='/ai_agent')
    app.register_blueprint(actors_bp)
    app.register_blueprint(proteus_api_bp)
    app.register_blueprint(oracles_bp)
    app.register_blueprint(oracle_manual_bp)
    app.register_blueprint(node_api_bp)
    
    # Initialize rate limiter
    init_limiter(app)

    # Register standardized error handlers
    from routes.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Initialize request context middleware for structured logging
    from utils.request_context import init_request_context
    init_request_context(app)

    # Chain-only mode: All data stored on blockchain
    
    # Initialize chain-only services
    
    # Start production monitoring service
    try:
        from services.monitoring import monitoring_service
        monitoring_service.start_monitoring(app)
        logger.info("Production monitoring service started")
    except Exception as e:
        logger.error(f"Failed to start monitoring service: {e}")
    
    return app, celery

app, celery = create_app()

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from celery import Celery
import redis

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

# Initialize Redis
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    decode_responses=True
)

def create_app():
    logger = logging.getLogger(__name__)
    app = Flask(__name__)
    # Phase 4: No Flask sessions in chain-only mode
    # JWT-based wallet auth doesn't need Flask sessions
    app.secret_key = os.urandom(32).hex()  # Random key, not used for sessions
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Load configuration
    # Phase 4: Use chain-only configuration
    from config_chain import chain_config
    
    # Apply chain configuration to Flask app
    app.config['CELERY_BROKER_URL'] = chain_config.CELERY_BROKER_URL
    app.config['CELERY_RESULT_BACKEND'] = chain_config.CELERY_RESULT_BACKEND
    
    # Phase 4: Skip database initialization - chain-only mode
    # db.init_app(app) - REMOVED: No database in chain-only mode
    
    # Initialize Celery
    celery = make_celery(app)
    app.celery = celery
    
    # Register blueprints
    from routes.api import api_bp
    from routes.admin import admin_bp
    from routes.auth import auth_bp  # Phase 2: Wallet-only authentication
    from routes.api_chain import api_chain_bp  # Phase 3: Chain-only API routes

    from routes.test_transactions import test_transactions_bp
    from routes.clockchain import clockchain_bp
    from routes.ai_agent_api import ai_agent_api_bp, init_limiter
    from routes.marketing import marketing_bp
    from routes.actors import actors_bp
    from routes.clockchain_api import clockchain_api_bp
    from routes.oracles import oracles_bp
    from routes.generate_realistic_data import generate_data_bp
    from routes.base_api import base_api_bp
    from routes.oracle_manual import oracle_manual_bp
    from routes.node_api import node_api_bp
    
    app.register_blueprint(marketing_bp)
    app.register_blueprint(auth_bp)  # Phase 2: Register auth routes
    app.register_blueprint(api_chain_bp, url_prefix='/api/chain')  # Phase 3: Chain-only routes
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(base_api_bp, url_prefix='/api/base')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    app.register_blueprint(test_transactions_bp, url_prefix='/test_transactions')
    app.register_blueprint(clockchain_bp)
    app.register_blueprint(ai_agent_api_bp, url_prefix='/ai_agent')
    app.register_blueprint(actors_bp)
    app.register_blueprint(clockchain_api_bp)
    app.register_blueprint(oracles_bp)
    app.register_blueprint(oracle_manual_bp)
    app.register_blueprint(generate_data_bp)
    app.register_blueprint(node_api_bp)
    
    # Test Manager Routes (Protected)
    from routes.test_manager import test_manager_bp
    app.register_blueprint(test_manager_bp)
    
    # Initialize rate limiter
    init_limiter(app)
    
    # Phase 4: Database initialization removed - chain-only mode
    # with app.app_context():
    #     import models  # REMOVED: No database models
    #     db.create_all()  # REMOVED: No database tables
    
    # Phase 1: Consensus service deprecated - handled by DecentralizedOracle contract
    # Initialize node operator if not exists
    # from services.consensus import ConsensusService
    # ConsensusService.initialize_node()
    
    # Start production monitoring service
    try:
        from services.monitoring import monitoring_service
        monitoring_service.start_monitoring(app)
        logger.info("Production monitoring service started")
    except Exception as e:
        logger.error(f"Failed to start monitoring service: {e}")
    
    return app, celery

app, celery = create_app()

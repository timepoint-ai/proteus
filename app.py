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
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Load configuration
    from config import Config
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Celery
    celery = make_celery(app)
    app.celery = celery
    
    # Register blueprints
    from routes.api import api_bp
    from routes.admin import admin_bp
    from routes.test_data import test_data_bp
    from routes.test_data_v2 import test_data_v2_bp
    from routes.test_data_new import test_data_new_bp
    from routes.test_data_ai import test_data_ai_bp
    from routes.test_transactions import test_transactions_bp
    from routes.clockchain import clockchain_bp
    from routes.ai_agent_api import ai_agent_api_bp, init_limiter
    from routes.marketing import marketing_bp
    from routes.actors import actors_bp
    from routes.clockchain_api import clockchain_api_bp
    from routes.oracles import oracles_bp
    from routes.generate_realistic_data import generate_data_bp
    from routes.base_api import base_api_bp
    
    app.register_blueprint(marketing_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(base_api_bp, url_prefix='/api/base')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(test_data_bp, url_prefix='/test_data')
    app.register_blueprint(test_data_v2_bp, url_prefix='/test_data_v2')
    app.register_blueprint(test_data_new_bp, url_prefix='/test_data_new')
    app.register_blueprint(test_data_ai_bp, url_prefix='/test_data_ai')
    app.register_blueprint(test_transactions_bp, url_prefix='/test_transactions')
    app.register_blueprint(clockchain_bp)
    app.register_blueprint(ai_agent_api_bp, url_prefix='/ai_agent')
    app.register_blueprint(actors_bp)
    app.register_blueprint(clockchain_api_bp)
    app.register_blueprint(oracles_bp)
    app.register_blueprint(generate_data_bp)
    
    # Initialize rate limiter
    init_limiter(app)
    
    # Create database tables
    with app.app_context():
        import models
        db.create_all()
        
        # Initialize node operator if not exists
        from services.consensus import ConsensusService
        ConsensusService.initialize_node()
    
    return app, celery

app, celery = create_app()

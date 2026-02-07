import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
scheduler = BackgroundScheduler()


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.rumors import rumors_bp
    from app.blueprints.voting import voting_bp
    from app.blueprints.users import users_bp
    from app.blueprints.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(rumors_bp, url_prefix='/api/rumors')
    app.register_blueprint(voting_bp, url_prefix='/api/voting')
    app.register_blueprint(users_bp, url_prefix='/api/user')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Register middleware
    from app.middleware.nullifier import register_nullifier_middleware
    register_nullifier_middleware(app)
    
    # Error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Create tables and initialize blockchain
    with app.app_context():
        db.create_all()
        from app.services.blockchain import initialize_blockchain
        initialize_blockchain()
    
    # Start background scheduler
    if not scheduler.running:
        from app.services.scheduler import setup_jobs
        setup_jobs(app)
        scheduler.start()
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {'status': 'healthy', 'message': 'VeraNode API is running'}, 200
    
    return app

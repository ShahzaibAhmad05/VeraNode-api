import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/veranode')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_MODEL = os.getenv('AZURE_OPENAI_MODEL')
    
    # App Configuration
    PORT = int(os.getenv('PORT', 3008))
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Voting Configuration
    VOTING_DURATION_HOURS = 48
    VOTING_CHECK_INTERVAL_MINUTES = 5
    FINALIZATION_CHECK_INTERVAL_MINUTES = 10
    WITHIN_AREA_THRESHOLD = 0.3  # 30% of votes must be within area
    
    # Points Configuration
    INITIAL_USER_POINTS = 100
    CORRECT_VOTE_POINTS = 10
    INCORRECT_VOTE_PENALTY = -5
    LIE_RUMOR_PENALTY = -50
    BLOCKING_THRESHOLD = -100


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

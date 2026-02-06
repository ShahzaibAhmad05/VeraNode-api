from flask import jsonify
from werkzeug.exceptions import HTTPException
from flask_jwt_extended.exceptions import JWTExtendedException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class APIError(Exception):
    """Custom API error class"""
    def __init__(self, message, code, status_code=400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = {
            'message': error.message,
            'code': error.code
        }
        return jsonify(response), error.status_code
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = {
            'message': error.description,
            'code': 'HTTP_ERROR'
        }
        return jsonify(response), error.code
    
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(error):
        response = {
            'message': str(error),
            'code': 'JWT_ERROR'
        }
        return jsonify(response), 401
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        response = {
            'message': 'Database integrity error. This record may already exist.',
            'code': 'INTEGRITY_ERROR'
        }
        return jsonify(response), 400
    
    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        response = {
            'message': 'Database error occurred',
            'code': 'DATABASE_ERROR'
        }
        return jsonify(response), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        app.logger.error(f'Unhandled exception: {str(error)}', exc_info=True)
        response = {
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }
        return jsonify(response), 500

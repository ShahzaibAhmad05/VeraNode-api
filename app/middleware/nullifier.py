from functools import wraps
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import SecretKeyProfile
from app.utils.helpers import generate_nullifier
from app.utils.error_handlers import APIError


def nullifier_required(f):
    """
    Middleware decorator to validate nullifier for voting operations
    Ensures deterministic nullifier generation for privacy
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verify JWT first
        verify_jwt_in_request()
        secret_key = get_jwt_identity()
        
        # Get profile with secret key
        profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
        if not profile:
            raise APIError("Profile not found", "PROFILE_NOT_FOUND", 404)
        
        if profile.is_blocked:
            raise APIError(
                "Your account is blocked due to low reputation points",
                "ACCOUNT_BLOCKED",
                403
            )
        
        # Store profile and secret key in request context
        g.current_profile = profile
        g.secret_key = secret_key
        
        return f(*args, **kwargs)
    
    return decorated_function


def generate_vote_nullifier(secret_key: str, rumor_id: str) -> str:
    """
    Generate deterministic nullifier for a vote
    This ensures privacy while preventing double-voting
    """
    return generate_nullifier(secret_key, rumor_id)


def register_nullifier_middleware(app):
    """Register nullifier-related middleware with the app"""
    
    @app.before_request
    def check_profile_block_status():
        """Check if profile is blocked on protected routes"""
        # Only check on API routes that require authentication
        if request.path.startswith('/api/') and request.path not in [
            '/api/health',
            '/api/auth/register',
            '/api/auth/login'
        ]:
            # Check if there's a valid JWT
            try:
                verify_jwt_in_request(optional=True)
                secret_key = get_jwt_identity()
                if secret_key:
                    profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
                    if profile and profile.is_blocked:
                        # Allow read-only operations for blocked users
                        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
                            raise APIError(
                                "Your account is blocked due to low reputation points. You can view content but cannot post or vote.",
                                "ACCOUNT_BLOCKED",
                                403
                            )
            except:
                # If JWT verification fails, let the route handle it
                pass
    
    print("✓ Nullifier middleware registered")

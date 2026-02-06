from datetime import datetime
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import Admin, SecretKeyProfile
from app.utils.error_handlers import APIError

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to ensure only admins can access certain routes"""
    from functools import wraps
    
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        admin_key = get_jwt_identity()
        
        # Verify admin_key is actually an admin
        admin = Admin.query.filter_by(admin_key=admin_key).first()
        if not admin:
            raise APIError(
                "Admin access required",
                "ADMIN_ACCESS_REQUIRED",
                403
            )
        
        # Store admin in request context
        g.current_admin = admin
        
        return f(*args, **kwargs)
    
    return decorated_function


@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login with admin private key"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    admin_key = data.get('adminKey', '').strip()
    
    if not admin_key:
        raise APIError("Admin key is required", "INVALID_CREDENTIALS", 401)
    
    # Find admin by key
    admin = Admin.query.filter_by(admin_key=admin_key).first()
    
    if not admin:
        raise APIError("Invalid admin key", "INVALID_CREDENTIALS", 401)
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate JWT token using admin key as identity
    access_token = create_access_token(identity=admin_key)
    
    return jsonify({
        'success': True,
        'token': access_token,
        'admin': admin.to_dict()
    }), 200


@admin_bp.route('/dashboard/blocked-users', methods=['GET'])
@admin_required
def get_blocked_users():
    """Get all blocked user profiles"""
    blocked_profiles = SecretKeyProfile.query.filter_by(is_blocked=True).all()
    
    profiles_data = []
    for profile in blocked_profiles:
        profile_data = profile.to_dict()
        profile_data['secretKeyPreview'] = profile.secret_key[:16] + '...'  # Show preview only
        profiles_data.append(profile_data)
    
    return jsonify({
        'blockedProfiles': profiles_data,
        'count': len(profiles_data)
    }), 200


@admin_bp.route('/dashboard/unblock-user', methods=['POST'])
@admin_required
def unblock_user():
    """Unblock a user profile"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    secret_key = data.get('secretKey', '').strip()
    
    if not secret_key:
        raise APIError("Secret key is required", "INVALID_REQUEST", 400)
    
    # Find profile by secret key
    profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
    
    if not profile:
        raise APIError("Profile not found", "PROFILE_NOT_FOUND", 404)
    
    if not profile.is_blocked:
        raise APIError("Profile is not blocked", "PROFILE_NOT_BLOCKED", 400)
    
    # Unblock the profile
    profile.is_blocked = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile unblocked successfully',
        'profile': {
            'secretKeyPreview': profile.secret_key[:16] + '...',
            'area': profile.area.value,
            'points': profile.points,
            'isBlocked': profile.is_blocked
        }
    }), 200


@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Get overall platform statistics for admin dashboard"""
    from app.models import User, Rumor, Vote, BlockchainLedger
    
    total_users = User.query.count()
    total_profiles = SecretKeyProfile.query.count()
    blocked_profiles = SecretKeyProfile.query.filter_by(is_blocked=True).count()
    active_profiles = total_profiles - blocked_profiles
    
    total_rumors = Rumor.query.count()
    active_rumors = Rumor.query.filter_by(is_final=False).count()
    finalized_rumors = Rumor.query.filter_by(is_final=True).count()
    
    total_votes = Vote.query.count()  # Only active votes (deleted after finalization)
    
    blockchain_blocks = BlockchainLedger.query.count()
    
    return jsonify({
        'users': {
            'total': total_users,
            'totalProfiles': total_profiles,
            'active': active_profiles,
            'blocked': blocked_profiles
        },
        'rumors': {
            'total': total_rumors,
            'active': active_rumors,
            'finalized': finalized_rumors
        },
        'votes': {
            'active': total_votes  # Only unfinalized rumors
        },
        'blockchain': {
            'totalBlocks': blockchain_blocks
        }
    }), 200


@admin_bp.route('/verify', methods=['GET'])
@admin_required
def verify_admin():
    """Verify admin token is valid"""
    admin = g.current_admin
    
    return jsonify({
        'success': True,
        'admin': admin.to_dict()
    }), 200

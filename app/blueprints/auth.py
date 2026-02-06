from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, SecretKeyProfile, AreaEnum
from app.utils.validators import validate_area
from app.utils.helpers import generate_secret_key
from app.utils.error_handlers import APIError
from app.config import Config

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user - returns secret key ONCE (cannot be regenerated)"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    area = data.get('area', '')
    
    # Validate area
    valid, error = validate_area(area)
    if not valid:
        raise APIError(error, "INVALID_AREA", 400)
    
    # Generate secret key (unique identifier for the user)
    secret_key = generate_secret_key()
    
    # Ensure uniqueness (extremely rare collision)
    while User.query.filter_by(secret_key=secret_key).first() is not None:
        secret_key = generate_secret_key()
    
    # Create user account (registration record only)
    user = User(
        secret_key=secret_key
    )
    
    # Create profile (data stored against secret key)
    profile = SecretKeyProfile(
        secret_key=secret_key,
        area=AreaEnum(area),
        points=Config.INITIAL_USER_POINTS
    )
    
    db.session.add(user)
    db.session.add(profile)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Registration successful. SAVE YOUR SECRET KEY - it cannot be recovered or regenerated!',
        'secretKey': secret_key,
        'profile': profile.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with secret key"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    secret_key = data.get('secretKey', '').strip()
    
    if not secret_key:
        raise APIError("Secret key is required", "INVALID_CREDENTIALS", 401)
    
    # Find profile by secret key
    profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
    
    if not profile:
        raise APIError("Invalid secret key", "INVALID_CREDENTIALS", 401)
    
    if profile.is_blocked:
        raise APIError(
            "Your account is blocked due to low reputation points",
            "ACCOUNT_BLOCKED",
            403
        )
    
    # Generate JWT token using secret key as identity
    access_token = create_access_token(identity=secret_key)
    
    return jsonify({
        'success': True,
        'token': access_token,
        'profile': profile.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get profile info using JWT token"""
    secret_key = get_jwt_identity()
    
    profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
    if not profile:
        raise APIError("Profile not found", "PROFILE_NOT_FOUND", 404)
    
    return jsonify({
        'profile': profile.to_dict()
    }), 200

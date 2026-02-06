from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, SecretKeyProfile, AreaEnum
from app.utils.validators import validate_area, validate_edu_email, validate_password
from app.utils.helpers import generate_secret_key, hash_password, verify_password
from app.utils.error_handlers import APIError
from app.config import Config

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account with email and password, and generate a separate secret key"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    department = data.get('department', '')
    
    # Validate email
    valid, error = validate_edu_email(email)
    if not valid:
        raise APIError(error, "INVALID_EMAIL", 400)
    
    # Validate password
    valid, error = validate_password(password)
    if not valid:
        raise APIError(error, "INVALID_PASSWORD", 400)
    
    # Validate department (area) - General is not allowed as a department choice
    valid, error = validate_area(department)
    if not valid:
        raise APIError(error, "INVALID_DEPARTMENT", 400)
    
    if department == "General":
        raise APIError(
            "General is not a valid department. Please select your specific department.",
            "INVALID_DEPARTMENT",
            400
        )
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        raise APIError("Email already registered", "EMAIL_EXISTS", 409)
    
    # Create user account with email and password
    password_hashed = hash_password(password)
    user = User(
        email=email,
        password_hash=password_hashed
    )
    
    # Generate secret key (completely independent of user account)
    secret_key = generate_secret_key()
    
    # Ensure secret key uniqueness (extremely rare collision)
    while SecretKeyProfile.query.filter_by(secret_key=secret_key).first() is not None:
        secret_key = generate_secret_key()
    
    # Create secret key profile (NOT linked to user account - zero-knowledge design)
    profile = SecretKeyProfile(
        secret_key=secret_key,
        area=AreaEnum(department),
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


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout endpoint - JWT tokens are stateless, so logout is client-side.
    This endpoint exists for frontend convenience and to confirm logout action.
    """
    return jsonify({
        'success': True,
        'message': 'Logged out successfully. Please discard your JWT token.'
    }), 200

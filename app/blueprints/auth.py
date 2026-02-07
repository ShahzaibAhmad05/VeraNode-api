from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, SecretKeyProfile, Admin, AreaEnum
from app.utils.validators import validate_area, validate_edu_email, validate_password
from app.utils.helpers import generate_secret_key, hash_password, verify_password
from app.utils.error_handlers import APIError
from app.config import Config

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/check-key-status', methods=['POST'])
def check_key_status():
    """Check if a secret key exists and whether it has expired"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    secret_key = data.get('secretKey', '').strip()
    
    if not secret_key:
        raise APIError("Secret key is required", "MISSING_SECRET_KEY", 400)
    
    # Find the profile by secret key
    profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
    
    if not profile:
        return jsonify({
            'exists': False,
            'message': 'Secret key not found'
        }), 404
    
    # Check and update expiration status
    is_expired = profile.check_key_expiration()
    
    if is_expired:
        db.session.commit()
    
    return jsonify({
        'exists': True,
        'isExpired': profile.is_key_expired,
        'expiresAt': profile.key_expires_at.isoformat(),
        'canRecover': profile.is_key_expired,
        'message': 'Key has expired and can be recovered during registration' if profile.is_key_expired else 'Key is still valid'
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account with email and password, and generate a separate secret key"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    department = data.get('department', '')
    previous_secret_key = data.get('previousSecretKey', '').strip() if data.get('previousSecretKey') else None
    
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
    
    # Handle key recovery if previous key is provided
    if previous_secret_key:
        # Find the old profile by previous secret key
        old_profile = SecretKeyProfile.query.filter_by(secret_key=previous_secret_key).first()
        
        if not old_profile:
            raise APIError(
                "Previous secret key not found. Please register without a previous key.",
                "INVALID_PREVIOUS_KEY",
                404
            )
        
        # Check if the key has expired
        old_profile.check_key_expiration()
        
        if not old_profile.is_key_expired:
            raise APIError(
                "Previous secret key has not expired yet. You can still use it to login.",
                "KEY_NOT_EXPIRED",
                400
            )
        
        # Generate new secret key
        new_secret_key = generate_secret_key()
        
        # Ensure secret key uniqueness
        while SecretKeyProfile.query.filter_by(secret_key=new_secret_key).first() is not None:
            new_secret_key = generate_secret_key()
        
        # Store previous key and update to new key
        old_profile.previous_key = old_profile.secret_key
        old_profile.secret_key = new_secret_key
        old_profile.key_created_at = datetime.utcnow()
        old_profile.key_expires_at = datetime.utcnow() + timedelta(days=30)
        old_profile.is_key_expired = False
        
        # Create user account with email and password
        password_hashed = hash_password(password)
        user = User(
            email=email,
            password_hash=password_hashed
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Secret key recovered and renewed successfully! Your account data has been preserved. SAVE YOUR NEW SECRET KEY!',
            'secretKey': new_secret_key,
            'profile': old_profile.to_dict(),
            'recovered': True
        }), 200
    
    # Standard registration (no key recovery)
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
        'profile': profile.to_dict(),
        'recovered': False
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Unified login - accepts both admin and student secret keys"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    secret_key = data.get('secretKey', '').strip()
    
    if not secret_key:
        raise APIError("Secret key is required", "INVALID_CREDENTIALS", 401)
    
    # First, check if it's an admin key
    admin = Admin.query.filter_by(admin_key=secret_key).first()
    
    if admin:
        # Admin login
        admin.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token = create_access_token(identity=secret_key)
        
        return jsonify({
            'success': True,
            'token': access_token,
            'userType': 'admin',
            'admin': admin.to_dict()
        }), 200
    
    # If not admin, check if it's a student key
    profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
    
    if not profile:
        raise APIError("Invalid secret key", "INVALID_CREDENTIALS", 401)
    
    # Check if the key has expired
    is_expired = profile.check_key_expiration()
    if is_expired:
        db.session.commit()
        raise APIError(
            "Your secret key has expired (30 days). Please register again and use this expired key to recover your account data.",
            "KEY_EXPIRED",
            403
        )
    
    if profile.is_blocked:
        raise APIError(
            "Your account is blocked due to low reputation points",
            "ACCOUNT_BLOCKED",
            403
        )
    
    # Student login
    access_token = create_access_token(identity=secret_key)
    
    return jsonify({
        'success': True,
        'token': access_token,
        'userType': 'student',
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

from datetime import datetime
import uuid
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Rumor, SecretKeyProfile, AreaEnum
from app.utils.validators import validate_rumor_content, validate_area
from app.utils.helpers import generate_nullifier, hash_data
from app.utils.error_handlers import APIError
from app.services.ai_service import ai_service
from app.services.blockchain import blockchain_service
from app.middleware.nullifier import nullifier_required

rumors_bp = Blueprint('rumors', __name__)


@rumors_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_rumor():
    """Validate rumor content with AI before posting"""
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    content = data.get('content', '').strip()
    voting_ends_at = data.get('votingEndsAt', '')  # ISO string from frontend
    
    # Basic validation
    valid, error = validate_rumor_content(content)
    if not valid:
        raise APIError(error, "INVALID_CONTENT", 400)
    
    # AI validation with voting time
    validation = ai_service.validate_rumor(content, voting_ends_at)
    
    return jsonify(validation), 200


@rumors_bp.route('', methods=['POST'])
@nullifier_required
def create_rumor():
    """Create a new rumor"""
    profile = g.current_profile
    secret_key = g.secret_key
    
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    content = data.get('content', '').strip()
    area_of_vote = data.get('areaOfVote', '')
    voting_ends_at_str = data.get('votingEndsAt', '')  # ISO string from frontend
    
    # Validate content
    valid, error = validate_rumor_content(content)
    if not valid:
        raise APIError(error, "INVALID_CONTENT", 400)
    
    # Validate area
    valid, error = validate_area(area_of_vote)
    if not valid:
        raise APIError(error, "INVALID_AREA", 400)
    
    # Validate and parse voting end time
    if not voting_ends_at_str:
        raise APIError("votingEndsAt is required", "MISSING_FIELD", 400)
    
    try:
        # Parse ISO string and make it timezone-naive UTC
        voting_ends_at = datetime.fromisoformat(voting_ends_at_str.replace('Z', '+00:00'))
        # Convert to naive UTC for comparison
        if voting_ends_at.tzinfo is not None:
            voting_ends_at = voting_ends_at.replace(tzinfo=None)
    except (ValueError, AttributeError):
        raise APIError(
            "Invalid votingEndsAt format. Use ISO 8601 format (e.g., 2026-02-09T12:00:00Z)",
            "INVALID_DATE_FORMAT",
            400
        )
    
    # Ensure voting end time is in the future
    if voting_ends_at <= datetime.utcnow():
        raise APIError(
            "votingEndsAt must be in the future",
            "INVALID_VOTING_TIME",
            400
        )
    
    # AI validation with voting time
    validation = ai_service.validate_rumor(content, voting_ends_at_str)
    
    if not validation['isValid']:
        raise APIError(
            f"Rumor validation failed: {validation['reason']}",
            "INVALID_RUMOR",
            400
        )
    
    # Get previous hash from blockchain
    previous_hash = blockchain_service.get_last_block_hash()
    if previous_hash is None:
        previous_hash = blockchain_service.get_genesis_hash()
    
    # Generate ID for the rumor before creating it
    rumor_id = str(uuid.uuid4())
    
    # Generate nullifier for the rumor poster
    nullifier = generate_nullifier(secret_key, rumor_id)
    
    # Calculate initial hash
    voting_data = "0"  # Initial voting data
    current_hash = hash_data(
        f"{rumor_id}{content}{voting_data}{previous_hash}"
    )
    
    # Create rumor with all required fields
    rumor = Rumor(
        id=rumor_id,
        content=content,
        area_of_vote=AreaEnum(area_of_vote),
        profile_id=profile.id,
        previous_hash=previous_hash,
        nullifier=nullifier,
        current_hash=current_hash,
        voting_ends_at=voting_ends_at  # Use frontend-provided time
    )
    
    db.session.add(rumor)
    db.session.commit()
    
    return jsonify({
        'rumor': rumor.to_dict(include_stats=True),
        'validation': validation
    }), 201


@rumors_bp.route('', methods=['GET'])
def get_rumors():
    """
    Get list of rumors with optional filters
    
    Note: Users can see ALL rumors regardless of area.
    When voting, if rumor.area_of_vote matches user.area, it's "within area" (higher weight).
    Otherwise, it's "not within area" (lower weight).
    """
    # Query parameters
    status = request.args.get('status')  # 'active', 'locked', 'final'
    
    # Build query - show ALL rumors to everyone
    query = Rumor.query
    
    # Filter by status only
    if status == 'active':
        query = query.filter_by(is_locked=False, is_final=False)
    elif status == 'locked':
        query = query.filter_by(is_locked=True, is_final=False)
    elif status == 'final':
        query = query.filter_by(is_final=True)
    
    # Order by posted date (newest first)
    query = query.order_by(Rumor.posted_at.desc())
    
    rumors = query.all()
    
    return jsonify({
        'rumors': [rumor.to_dict(include_stats=True) for rumor in rumors]
    }), 200


@rumors_bp.route('/<rumor_id>', methods=['GET'])
def get_rumor(rumor_id):
    """Get a single rumor by ID"""
    rumor = Rumor.query.get(rumor_id)
    
    if not rumor:
        raise APIError("Rumor not found", "RUMOR_NOT_FOUND", 404)
    
    return jsonify({
        'rumor': rumor.to_dict(include_stats=True)
    }), 200


@rumors_bp.route('/<rumor_id>/stats', methods=['GET'])
def get_rumor_stats(rumor_id):
    """Get detailed statistics for a rumor (hidden until finalized)"""
    rumor = Rumor.query.get(rumor_id)
    
    if not rumor:
        raise APIError("Rumor not found", "RUMOR_NOT_FOUND", 404)
    
    # Only show stats when finalized to prevent psychological influence
    if rumor.is_final:
        stats = rumor.get_stats()
    else:
        stats = {
            'totalVotes': 'hidden',
            'factVotes': 'hidden',
            'lieVotes': 'hidden',
            'factWeight': 'hidden',
            'lieWeight': 'hidden',
            'underAreaVotes': 'hidden',
            'notUnderAreaVotes': 'hidden',
            'progress': 'hidden',
            'message': 'Statistics are hidden until voting is finalized to prevent bias'
        }
    
    return jsonify(stats), 200

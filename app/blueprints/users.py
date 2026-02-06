from flask import Blueprint, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import SecretKeyProfile, Rumor, Vote
from app.utils.error_handlers import APIError
from app.middleware.nullifier import nullifier_required

users_bp = Blueprint('users', __name__)


@users_bp.route('/stats', methods=['GET'])
@nullifier_required
def get_user_stats():
    """Get statistics for the current profile"""
    profile = g.current_profile
    
    # Count rumors posted
    rumors_posted = Rumor.query.filter_by(profile_id=profile.id).count()
    
    # Count active votes (votes only exist for unfinalized rumors)
    # Once rumor is finalized, votes are deleted for privacy
    active_votes = Vote.query.filter_by(profile_id=profile.id).all()
    rumors_voted = len(active_votes)
    
    # Note: Cannot calculate historical correct/incorrect votes since
    # votes are deleted after finalization (privacy requirement)
    # Points system already tracks accuracy through reputation score
    
    # Determine account status
    account_status = "BLOCKED" if profile.is_blocked else "ACTIVE"
    
    return jsonify({
        'rumorsPosted': rumors_posted,
        'activeVotes': rumors_voted,  # Only unfinalized rumors
        'accountStatus': account_status,
        'points': profile.points,  # Points reflect voting accuracy
        'area': profile.area.value
    }), 200


@users_bp.route('/rumors', methods=['GET'])
@nullifier_required
def get_user_rumors():
    """Get all rumors posted by the current profile"""
    profile = g.current_profile
    
    rumors = Rumor.query.filter_by(profile_id=profile.id).order_by(Rumor.posted_at.desc()).all()
    
    return jsonify({
        'rumors': [rumor.to_dict(include_stats=True) for rumor in rumors]
    }), 200


@users_bp.route('/profile', methods=['GET'])
@nullifier_required
def get_profile():
    """Get current profile"""
    profile = g.current_profile
    
    return jsonify({
        'profile': profile.to_dict()
    }), 200

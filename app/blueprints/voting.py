from datetime import datetime
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Rumor, Vote, SecretKeyProfile, VoteTypeEnum
from app.utils.helpers import calculate_vote_weight
from app.utils.error_handlers import APIError
from app.middleware.nullifier import nullifier_required, generate_vote_nullifier

voting_bp = Blueprint('voting', __name__)


@voting_bp.route('/rumors/<rumor_id>/vote', methods=['POST'])
@nullifier_required
def vote_on_rumor(rumor_id):
    """Vote on a rumor (FACT or LIE)"""
    profile = g.current_profile
    secret_key = g.secret_key
    
    data = request.get_json()
    
    if not data:
        raise APIError("Request body is required", "INVALID_REQUEST", 400)
    
    vote_type = data.get('voteType', '').upper()
    
    # Validate vote type
    if vote_type not in [VoteTypeEnum.FACT.value, VoteTypeEnum.LIE.value]:
        raise APIError(
            "Invalid vote type. Must be 'FACT' or 'LIE'",
            "INVALID_VOTE_TYPE",
            400
        )
    
    # Get rumor
    rumor = Rumor.query.get(rumor_id)
    if not rumor:
        raise APIError("Rumor not found", "RUMOR_NOT_FOUND", 404)
    
    # Check if voting is still open
    if rumor.is_locked:
        raise APIError(
            "Voting is closed for this rumor",
            "VOTING_CLOSED",
            400
        )
    
    if rumor.voting_ends_at < datetime.utcnow():
        raise APIError(
            "Voting period has ended for this rumor",
            "VOTING_CLOSED",
            400
        )
    
    # Generate nullifier for this vote
    nullifier = generate_vote_nullifier(secret_key, rumor_id)
    
    # Check if profile already voted (using nullifier)
    existing_vote = Vote.query.filter_by(
        rumor_id=rumor_id,
        nullifier=nullifier
    ).first()
    
    if existing_vote:
        raise APIError(
            "You have already voted on this rumor",
            "ALREADY_VOTED",
            400
        )
    
    # Calculate vote weight
    is_within_area = (profile.area == rumor.area_of_vote)
    weight = calculate_vote_weight(profile.points, is_within_area)
    
    # Create vote
    vote = Vote(
        rumor_id=rumor_id,
        profile_id=profile.id,
        nullifier=nullifier,
        vote_type=VoteTypeEnum(vote_type),
        weight=weight,
        is_within_area=is_within_area
    )
    
    db.session.add(vote)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'nullifier': nullifier,
        'weight': float(weight),
        'isWithinArea': is_within_area
    }), 201


@voting_bp.route('/rumors/<rumor_id>/vote-status', methods=['GET'])
@jwt_required()
@nullifier_required
def get_vote_status(rumor_id):
    """Check if user has voted on a rumor (doesn't reveal vote details)"""
    secret_key = g.secret_key
    
    # Get rumor
    rumor = Rumor.query.get(rumor_id)
    if not rumor:
        raise APIError("Rumor not found", "RUMOR_NOT_FOUND", 404)
    
    # Generate nullifier
    nullifier = generate_vote_nullifier(secret_key, rumor_id)
    
    # Check for existing vote
    vote = Vote.query.filter_by(
        rumor_id=rumor_id,
        nullifier=nullifier
    ).first()
    
    # Only return if user has voted, not what they voted for
    # This prevents users from second-guessing or being influenced by their own past vote
    return jsonify({
        'hasVoted': vote is not None
    }), 200


@voting_bp.route('/votes/my-votes', methods=['GET'])
@nullifier_required
def get_my_votes():
    """Get all active votes by the current profile (finalized votes are deleted for privacy)"""
    profile = g.current_profile
    
    if not profile:
        raise APIError("Profile not found", "PROFILE_NOT_FOUND", 404)
    
    # Only returns votes for unfinalized rumors (votes are deleted after finalization)
    votes = Vote.query.filter_by(profile_id=profile.id).order_by(Vote.timestamp.desc()).all()
    
    # Include rumor information with each vote
    votes_data = []
    for vote in votes:
        vote_dict = vote.to_dict()
        vote_dict['rumor'] = vote.rumor.to_dict() if vote.rumor else None
        votes_data.append(vote_dict)
    
    return jsonify({
        'votes': votes_data,
        'note': 'Only shows votes for active rumors. Votes are deleted after finalization for privacy.'
    }), 200

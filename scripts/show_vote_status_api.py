#!/usr/bin/env python3
"""
Show exact vote-status API responses for frontend
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
import json


def show_vote_status_api():
    """Show exact API responses"""
    app = create_app()
    
    with app.app_context():
        from app.models import SecretKeyProfile, Rumor
        from flask_jwt_extended import create_access_token
        
        profile = SecretKeyProfile.query.first()
        rumor_voted = Rumor.query.filter_by(is_final=False).first()
        
        if not profile or not rumor_voted:
            print("No data found!")
            return
        
        token = create_access_token(identity=profile.secret_key)
        client = app.test_client()
        
        print("\n" + "="*80)
        print("VOTE-STATUS API RESPONSE FORMAT")
        print("="*80)
        
        # Show response when voted
        print("\n📍 Scenario 1: User HAS voted on rumor")
        print("-" * 80)
        response = client.get(f'/api/rumors/{rumor_voted.id}/vote-status',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"\nGET /api/rumors/{rumor_voted.id}/vote-status")
        print(f"Status: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.get_json(), indent=2))
        
        print("\n\n📍 Scenario 2: User has NOT voted on rumor")
        print("-" * 80)
        
        # Find a rumor user hasn't voted on
        from app.models import Vote
        from app.utils.helpers import generate_nullifier
        
        unvoted_rumor = None
        for rumor in Rumor.query.filter_by(is_final=False).all():
            nullifier = generate_nullifier(profile.secret_key, rumor.id)
            vote = Vote.query.filter_by(rumor_id=rumor.id, nullifier=nullifier).first()
            if not vote:
                unvoted_rumor = rumor
                break
        
        if unvoted_rumor:
            response = client.get(f'/api/rumors/{unvoted_rumor.id}/vote-status',
                headers={'Authorization': f'Bearer {token}'}
            )
            print(f"\nGET /api/rumors/{unvoted_rumor.id}/vote-status")
            print(f"Status: {response.status_code}")
            print(f"\nResponse:")
            print(json.dumps(response.get_json(), indent=2))
        else:
            print("\n(No unvoted rumor found for demo)")
            print("Response would be: { \"hasVoted\": false }")
        
        print("\n" + "="*80)
        print("FRONTEND IMPLEMENTATION")
        print("="*80)
        
        print("""
JavaScript Example:
-------------------

const checkVoteStatus = async (rumorId) => {
  const response = await fetch(`/api/rumors/${rumorId}/vote-status`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const { hasVoted } = await response.json();
  
  // Only hasVoted field exists - boolean
  if (hasVoted) {
    // Disable vote buttons
    document.getElementById('vote-fact-btn').disabled = true;
    document.getElementById('vote-lie-btn').disabled = true;
    showMessage('You already voted');
  } else {
    // Enable vote buttons
    document.getElementById('vote-fact-btn').disabled = false;
    document.getElementById('vote-lie-btn').disabled = false;
  }
};

""")
        
        print("="*80 + "\n")


if __name__ == '__main__':
    show_vote_status_api()

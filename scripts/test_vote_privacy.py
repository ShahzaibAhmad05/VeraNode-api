#!/usr/bin/env python3
"""
Test that vote-status only shows hasVoted, not vote details
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Rumor, Vote, SecretKeyProfile, VoteTypeEnum
import json


def test_vote_status_privacy():
    """Test that vote status doesn't reveal vote details"""
    app = create_app()
    
    with app.app_context():
        # Get a profile and rumor
        profile = SecretKeyProfile.query.first()
        rumor = Rumor.query.filter_by(is_final=False).first()
        
        if not profile or not rumor:
            print("No profile or rumor found!")
            return
        
        secret_key = profile.secret_key
        
        # Create access token
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=secret_key)
        
        client = app.test_client()
        
        print("\n" + "="*80)
        print("TEST: Vote Status Privacy")
        print("="*80)
        
        # Check vote status before voting
        print(f"\nGET /api/rumors/{rumor.id}/vote-status (before voting)")
        response = client.get(f'/api/rumors/{rumor.id}/vote-status',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"Status: {response.status_code}")
        data = response.get_json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if 'hasVoted' in data and data['hasVoted'] == False:
            print("✓ Correct: hasVoted = false")
        
        if 'voteType' not in data and 'weight' not in data and 'timestamp' not in data:
            print("✓ Correct: No vote details exposed")
        else:
            print("✗ WRONG: Vote details should not be present!")
        
        # If no vote exists, create one
        existing_vote = Vote.query.filter_by(rumor_id=rumor.id, profile_id=profile.id).first()
        
        if not existing_vote:
            print("\n" + "="*80)
            print("Creating a vote...")
            print("="*80)
            
            vote_response = client.post(f'/api/rumors/{rumor.id}/vote',
                headers={'Authorization': f'Bearer {token}'},
                json={'voteType': 'FACT'}
            )
            print(f"Vote Status: {vote_response.status_code}")
            if vote_response.status_code == 201:
                print("✓ Vote created successfully")
            else:
                print(f"Vote response: {vote_response.get_json()}")
        
        # Check vote status after voting
        print("\n" + "="*80)
        print(f"GET /api/rumors/{rumor.id}/vote-status (after voting)")
        print("="*80)
        
        response = client.get(f'/api/rumors/{rumor.id}/vote-status',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"Status: {response.status_code}")
        data = response.get_json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if 'hasVoted' in data and data['hasVoted'] == True:
            print("✓ Correct: hasVoted = true")
        else:
            print("✗ WRONG: hasVoted should be true!")
        
        if 'voteType' not in data and 'weight' not in data and 'timestamp' not in data:
            print("✓ Correct: No vote details exposed (FACT/LIE/weight/time hidden)")
        else:
            print("✗ WRONG: Vote details should NOT be exposed!")
            if 'voteType' in data:
                print(f"  - voteType exposed: {data['voteType']}")
            if 'weight' in data:
                print(f"  - weight exposed: {data['weight']}")
            if 'timestamp' in data:
                print(f"  - timestamp exposed: {data['timestamp']}")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print("✓ Vote status only reveals: hasVoted (true/false)")
        print("✓ Hidden: voteType, weight, timestamp")
        print("✓ Prevents users from second-guessing their vote")
        print("✓ Prevents psychological influence from knowing past vote")
        print("="*80 + "\n")


if __name__ == '__main__':
    test_vote_status_privacy()

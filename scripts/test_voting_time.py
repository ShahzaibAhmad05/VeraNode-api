#!/usr/bin/env python3
"""
Test rumor creation with votingEndsAt from frontend
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import SecretKeyProfile
from datetime import datetime, timedelta
import json


def test_rumor_creation_with_voting_time():
    """Test creating rumor with frontend-provided votingEndsAt"""
    app = create_app()
    
    with app.app_context():
        # Get a profile and create JWT token
        profile = SecretKeyProfile.query.first()
        if not profile:
            print("No profile found! Run setup.py first")
            return
        
        secret_key = profile.secret_key
        
        # Create access token
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=secret_key)
        
        client = app.test_client()
        
        # Test 1: Create rumor WITHOUT votingEndsAt (should fail)
        print("\n" + "="*80)
        print("TEST 1: Create rumor WITHOUT votingEndsAt (should FAIL)")
        print("="*80)
        
        response = client.post('/api/rumors',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'content': 'TEST: This rumor has no voting end time',
                'areaOfVote': 'General'
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.get_json(), indent=2)}")
        
        # Test 2: Create rumor WITH votingEndsAt (should succeed)
        print("\n" + "="*80)
        print("TEST 2: Create rumor WITH votingEndsAt (should SUCCEED)")
        print("="*80)
        
        voting_ends_at = (datetime.utcnow() + timedelta(hours=48)).isoformat() + 'Z'
        
        response = client.post('/api/rumors',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'content': 'I heard the library will be closed next Friday for maintenance work',
                'areaOfVote': 'SEECS',
                'votingEndsAt': voting_ends_at
            }
        )
        print(f"Status: {response.status_code}")
        data = response.get_json()
        
        if response.status_code == 201:
            print("✓ Rumor created successfully!")
            rumor = data['rumor']
            print(f"\nRumor Details:")
            print(f"  ID: {rumor['id']}")
            print(f"  Content: {rumor['content']}")
            print(f"  Posted At: {rumor['postedAt']}")
            print(f"  Voting Ends At: {rumor['votingEndsAt']}")
            print(f"  Sent: {voting_ends_at}")
            print(f"  Match: {rumor['votingEndsAt'] == voting_ends_at or rumor['votingEndsAt'].startswith(voting_ends_at[:-1])}")
        else:
            print(f"✗ Failed: {json.dumps(data, indent=2)}")
        
        # Test 3: votingEndsAt in the past (should fail)
        print("\n" + "="*80)
        print("TEST 3: votingEndsAt in the PAST (should FAIL)")
        print("="*80)
        
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        
        response = client.post('/api/rumors',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'content': 'TEST: This rumor has voting time in the past',
                'areaOfVote': 'General',
                'votingEndsAt': past_time
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.get_json(), indent=2)}")


if __name__ == '__main__':
    test_rumor_creation_with_voting_time()

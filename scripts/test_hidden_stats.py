#!/usr/bin/env python3
"""
Test that voting stats are hidden during active voting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Rumor, Vote, SecretKeyProfile, VoteTypeEnum
from datetime import datetime, timedelta
import json


def test_hidden_stats():
    """Test that stats are hidden for active rumors"""
    app = create_app()
    
    with app.app_context():
        # Get active rumor
        active_rumor = Rumor.query.filter_by(is_final=False).first()
        
        if not active_rumor:
            print("No active rumors found!")
            return
        
        # Add a test vote if there are none
        if active_rumor.votes.count() == 0:
            profile = SecretKeyProfile.query.first()
            if profile:
                from app.utils.helpers import generate_nullifier, calculate_vote_weight
                nullifier = generate_nullifier(profile.secret_key, active_rumor.id)
                weight = calculate_vote_weight(profile.area, active_rumor.area_of_vote)
                
                vote = Vote(
                    rumor_id=active_rumor.id,
                    profile_id=profile.id,
                    nullifier=nullifier,
                    vote_type=VoteTypeEnum.FACT,
                    weight=weight,
                    is_within_area=(profile.area == active_rumor.area_of_vote)
                )
                db.session.add(vote)
                db.session.commit()
                print("Added test vote to rumor")
        
        client = app.test_client()
        
        print("\n" + "="*80)
        print("TEST: Active Rumor Stats Should Be HIDDEN")
        print("="*80)
        
        # Test GET /rumors (list)
        print("\nGET /api/rumors")
        response = client.get('/api/rumors')
        data = response.get_json()
        
        rumor_data = next((r for r in data['rumors'] if r['id'] == active_rumor.id), None)
        if rumor_data:
            print(f"\nRumor: {rumor_data['id'][:16]}...")
            print(f"Is Final: {rumor_data['isFinal']}")
            print(f"Is Locked: {rumor_data['isLocked']}")
            print(f"Stats: {json.dumps(rumor_data.get('stats', {}), indent=2)}")
            
            if rumor_data.get('stats', {}).get('totalVotes') == 'hidden':
                print("✓ Stats are HIDDEN (correct)")
            else:
                print("✗ Stats are VISIBLE (WRONG!)")
        
        # Test GET /rumors/:id
        print("\n" + "="*80)
        print(f"GET /api/rumors/{active_rumor.id}")
        response = client.get(f'/api/rumors/{active_rumor.id}')
        data = response.get_json()
        
        rumor_data = data['rumor']
        print(f"Is Final: {rumor_data['isFinal']}")
        print(f"Stats: {json.dumps(rumor_data.get('stats', {}), indent=2)}")
        
        if rumor_data.get('stats', {}).get('totalVotes') == 'hidden':
            print("✓ Stats are HIDDEN (correct)")
        else:
            print("✗ Stats are VISIBLE (WRONG!)")
        
        # Test GET /rumors/:id/stats
        print("\n" + "="*80)
        print(f"GET /api/rumors/{active_rumor.id}/stats")
        response = client.get(f'/api/rumors/{active_rumor.id}/stats')
        stats = response.get_json()
        
        print(f"Response: {json.dumps(stats, indent=2)}")
        
        if stats.get('totalVotes') == 'hidden':
            print("✓ Stats are HIDDEN (correct)")
        else:
            print("✗ Stats are VISIBLE (WRONG!)")
        
        # Test with finalized rumor
        print("\n" + "="*80)
        print("TEST: Finalized Rumor Stats Should Be VISIBLE")
        print("="*80)
        
        # Create a finalized test rumor
        from app.utils.helpers import generate_nullifier, hash_data
        from app.services.blockchain import blockchain_service
        import uuid
        
        profile = SecretKeyProfile.query.first()
        rumor_id = str(uuid.uuid4())
        content = "TEST: Finalized rumor for stats testing"
        
        nullifier = generate_nullifier(profile.secret_key, rumor_id)
        previous_hash = blockchain_service.get_last_block_hash()
        if not previous_hash:
            previous_hash = blockchain_service.get_genesis_hash()
        
        current_hash = hash_data(f"{rumor_id}{content}0{previous_hash}")
        
        from app.models import AreaEnum, DecisionEnum
        final_rumor = Rumor(
            id=rumor_id,
            content=content,
            area_of_vote=AreaEnum.GENERAL,
            profile_id=profile.id,
            previous_hash=previous_hash,
            nullifier=nullifier,
            current_hash=current_hash,
            voting_ends_at=datetime.utcnow() - timedelta(hours=1),
            is_locked=True,
            is_final=True,
            final_decision=DecisionEnum.FACT
        )
        
        db.session.add(final_rumor)
        db.session.commit()
        
        print(f"\nGET /api/rumors/{final_rumor.id}/stats")
        response = client.get(f'/api/rumors/{final_rumor.id}/stats')
        stats = response.get_json()
        
        print(f"Response: {json.dumps(stats, indent=2)}")
        
        if isinstance(stats.get('totalVotes'), int):
            print("✓ Stats are VISIBLE (correct for finalized rumor)")
        else:
            print("✗ Stats are HIDDEN (WRONG for finalized rumor!)")
        
        # Cleanup
        db.session.delete(final_rumor)
        db.session.commit()


if __name__ == '__main__':
    test_hidden_stats()

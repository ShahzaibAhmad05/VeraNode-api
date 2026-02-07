"""Quick script to create a test rumor"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Rumor, SecretKeyProfile, AreaEnum
from datetime import datetime
import hashlib

app = create_app()
with app.app_context():
    profile = SecretKeyProfile.query.first()
    if not profile:
        print("❌ No profiles found. Run fresh_setup.py first")
    else:
        # Generate unique nullifier and hash for the test rumor
        timestamp = datetime.utcnow().timestamp()
        nullifier = hashlib.sha256(f'{profile.secret_key}test{timestamp}'.encode()).hexdigest()
        current_hash = hashlib.sha256(f'rumor{timestamp}'.encode()).hexdigest()
        
        rumor = Rumor(
            content='Test rumor for expiration - This is a sample rumor to test the workflow',
            area_of_vote=AreaEnum.SEECS,
            profile_id=profile.id,
            nullifier=nullifier,
            current_hash=current_hash
        )
        
        db.session.add(rumor)
        db.session.commit()
        
        print(f'✅ Created test rumor: {rumor.id[:16]}...')
        print(f'   Content: {rumor.content}')
        print(f'   Posted: {rumor.posted_at.strftime("%Y-%m-%d %H:%M")}')
        print(f'   Voting ends: {rumor.voting_ends_at.strftime("%Y-%m-%d %H:%M")}')
        print(f'\nNow run: python scripts/expire_rumor.py')

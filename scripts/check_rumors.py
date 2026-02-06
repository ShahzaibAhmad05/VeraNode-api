#!/usr/bin/env python3
"""
Check rumors in database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Rumor


def check_rumors():
    """Check all rumors in database"""
    app = create_app()
    
    with app.app_context():
        rumors = Rumor.query.order_by(Rumor.posted_at.desc()).all()
        
        print(f"\n{'='*80}")
        print(f"RUMORS IN DATABASE: {len(rumors)}")
        print(f"{'='*80}\n")
        
        if not rumors:
            print("No rumors found in database!")
            return
        
        from datetime import datetime
        now = datetime.utcnow()
        
        for rumor in rumors:
            time_left = (rumor.voting_ends_at - now).total_seconds()
            print(f"ID: {rumor.id}")
            print(f"Content: {rumor.content[:50]}...")
            print(f"Area: {rumor.area_of_vote.value}")
            print(f"Posted At: {rumor.posted_at}")
            print(f"Voting Ends At: {rumor.voting_ends_at}")
            print(f"Time Left: {time_left} seconds ({time_left/3600:.1f} hours)")
            print(f"Is Locked: {rumor.is_locked}")
            print(f"Is Final: {rumor.is_final}")
            print(f"Profile ID: {rumor.profile_id}")
            print(f"Votes: {rumor.votes.count()}")
            print("-" * 80)


if __name__ == '__main__':
    check_rumors()

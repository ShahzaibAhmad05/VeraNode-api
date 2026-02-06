#!/usr/bin/env python3
"""Test admin endpoint by blocking a user"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import SecretKeyProfile

app = create_app()

with app.app_context():
    # Block first profile for testing
    profile = SecretKeyProfile.query.first()
    
    if profile:
        profile.is_blocked = True
        db.session.commit()
        
        print("✓ Blocked test profile for admin demo")
        print(f"\nBlocked User Info (Admin View):")
        print(f"  Secret Key: {profile.secret_key}")
        print(f"  Created At: {profile.created_at}")
        print(f"  Is Blocked: {profile.is_blocked}")
        print(f"\n✗ NOT visible to admin: Area ({profile.area.value}), Points ({profile.points})")
    else:
        print("No profiles found")

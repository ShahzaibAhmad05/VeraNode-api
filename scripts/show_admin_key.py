#!/usr/bin/env python3
"""Show the current admin key from database"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Admin

app = create_app()

with app.app_context():
    admins = Admin.query.all()
    
    if not admins:
        print("❌ No admin account found in database!")
        print("\nRun one of these to create admin:")
        print("  python setup.py")
        print("  python scripts/init_db.py")
    else:
        print("\n" + "="*70)
        print("CURRENT ADMIN KEY IN DATABASE:")
        print("="*70)
        for i, admin in enumerate(admins):
            print(f"\nAdmin #{i+1}")
            print(f"Key: {admin.admin_key}")
            print(f"Created: {admin.created_at}")
            print(f"Last Login: {admin.last_login or 'Never'}")
        print("\n" + "="*70)
        print("Use this key to login to admin dashboard")
        print("="*70)

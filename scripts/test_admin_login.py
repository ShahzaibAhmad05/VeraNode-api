#!/usr/bin/env python3
"""
Test admin login with the generated key
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Admin

def test_admin_login():
    app = create_app()
    
    with app.app_context():
        admin = Admin.query.first()
        if not admin:
            print("❌ No admin found in database")
            return
        
        print("="*70)
        print("ADMIN LOGIN CREDENTIALS")
        print("="*70)
        print(f"\nEndpoint: POST /admin/login")
        print(f"\nRequest body:")
        print(f'{{')
        print(f'  "adminKey": "{admin.admin_key}"')
        print(f'}}')
        print("\n" + "="*70)
        print("⚠️  Use /admin/login (NOT /auth/login)")
        print("⚠️  Use field 'adminKey' (NOT 'secretKey')")
        print("="*70)

if __name__ == '__main__':
    test_admin_login()

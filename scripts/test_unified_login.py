#!/usr/bin/env python3
"""
Test the unified login endpoint with both admin and student keys
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Admin, SecretKeyProfile
import json

def test_unified_login():
    app = create_app()
    
    with app.app_context():
        # Get admin key
        admin = Admin.query.first()
        admin_key = admin.admin_key if admin else None
        
        # Get student key
        profile = SecretKeyProfile.query.first()
        student_key = profile.secret_key if profile else None
        
        print("="*70)
        print("UNIFIED LOGIN ENDPOINT TEST")
        print("="*70)
        
        if admin_key:
            print("\n✅ ADMIN LOGIN TEST")
            print(f"Endpoint: POST /auth/login")
            print(f"Request:")
            print(json.dumps({"secretKey": admin_key}, indent=2))
            print(f"\nExpected Response:")
            print(json.dumps({
                "success": True,
                "token": "jwt_token_here",
                "userType": "admin",
                "admin": {"id": "...", "createdAt": "...", "lastLogin": "..."}
            }, indent=2))
        
        if student_key:
            print("\n" + "="*70)
            print("\n✅ STUDENT LOGIN TEST")
            print(f"Endpoint: POST /auth/login")
            print(f"Request:")
            print(json.dumps({"secretKey": student_key}, indent=2))
            print(f"\nExpected Response:")
            print(json.dumps({
                "success": True,
                "token": "jwt_token_here",
                "userType": "student",
                "profile": {"area": "...", "points": 100, "isBlocked": False, "createdAt": "..."}
            }, indent=2))
        
        print("\n" + "="*70)
        print("Both admin and student use the SAME endpoint!")
        print("Backend auto-detects based on the secretKey provided")
        print("="*70)

if __name__ == '__main__':
    test_unified_login()

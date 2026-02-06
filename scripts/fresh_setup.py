#!/usr/bin/env python3
"""
Fresh database setup - clears everything and creates new admin
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, SecretKeyProfile, Admin, AreaEnum
from app.utils.helpers import generate_secret_key
from app.config import Config

def fresh_setup():
    """Complete fresh setup"""
    print("\n" + "="*70)
    print("FRESH DATABASE SETUP - This will DELETE ALL DATA!")
    print("="*70)
    
    response = input("\nAre you sure? Type 'yes' to continue: ")
    
    if response.lower() != 'yes':
        print("\n❌ Setup cancelled")
        return
    
    app = create_app()
    
    with app.app_context():
        # Drop everything
        print("\n🗑️  Dropping all tables...")
        db.drop_all()
        
        # Create tables
        print("📦 Creating new tables...")
        db.create_all()
        
        # Create sample profiles
        print("👥 Creating sample profiles...")
        sample_areas = [AreaEnum.SEECS, AreaEnum.NBS, AreaEnum.ASAB]
        user_keys = []
        
        for area in sample_areas:
            secret_key = generate_secret_key()
            user = User(secret_key=secret_key)
            profile = SecretKeyProfile(
                secret_key=secret_key,
                area=area,
                points=Config.INITIAL_USER_POINTS
            )
            db.session.add(user)
            db.session.add(profile)
            user_keys.append((area.value, secret_key))
            print(f"   ✓ Created {area.value} profile")
        
        # Create admin (ONLY ONE)
        print("\n👮 Creating admin account...")
        admin_key = generate_secret_key()
        admin = Admin(admin_key=admin_key)
        db.session.add(admin)
        
        # Commit everything
        db.session.commit()
        
        # Display results
        print("\n" + "="*70)
        print("✅ SETUP COMPLETE!")
        print("="*70)
        
        print("\n📝 SAMPLE USER KEYS:")
        for area, key in user_keys:
            print(f"   {area}: {key}")
        
        print("\n" + "="*70)
        print("🔑 ADMIN KEY (SAVE THIS!):")
        print("="*70)
        print(f"\n{admin_key}\n")
        print("="*70)
        print("\n⚠️  This is the ONLY admin key. Save it now!")
        print("   Run 'python scripts/show_admin_key.py' to view it again")
        print("="*70)

if __name__ == '__main__':
    try:
        fresh_setup()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

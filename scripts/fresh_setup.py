#!/usr/bin/env python3
"""
Fresh database setup - clears everything and creates new admin
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, SecretKeyProfile, Admin, AreaEnum
from app.utils.helpers import generate_secret_key, hash_password
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
        
        # Create sample user accounts and profiles
        print("👥 Creating sample user accounts and profiles...")
        sample_data = [
            (AreaEnum.SEECS, "seecs.user@nust.edu.pk"),
            (AreaEnum.NBS, "nbs.user@nust.edu.pk"),
            (AreaEnum.ASAB, "asab.user@nust.edu.pk")
        ]
        user_info = []
        
        for area, email in sample_data:
            # Create user account (email + password)
            user = User(
                email=email,
                password_hash=hash_password("password123")
            )
            
            # Generate separate secret key (NOT linked to account)
            secret_key = generate_secret_key()
            profile = SecretKeyProfile(
                secret_key=secret_key,
                area=area,
                points=Config.INITIAL_USER_POINTS
            )
            
            db.session.add(user)
            db.session.add(profile)
            user_info.append((area.value, email, secret_key))
            print(f"   ✓ Created {area.value} account and profile")
        
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
        
        print("\n📝 SAMPLE USERS (password: password123):")
        for area, email, secret_key in user_info:
            print(f"\n   {area}:")
            print(f"      Email: {email}")
            print(f"      Secret Key: {secret_key}")
        
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

#!/usr/bin/env python3
"""
Fresh Start Script - Quick Database Reset
Drops all tables, recreates schema, and adds sample data
Run with: python fresh_start.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, SecretKeyProfile, Admin, AreaEnum
from app.utils.helpers import generate_secret_key, hash_password
from app.config import Config


def fresh_start():
    """Complete fresh database reset"""
    print("\n" + "="*70)
    print("FRESH START - RESETTING DATABASE")
    print("="*70)
    
    app = create_app()
    
    with app.app_context():
        # Drop everything
        print("\n🗑️  Dropping all tables...")
        db.drop_all()
        
        # Create tables
        print("📦 Creating new tables...")
        db.create_all()
        
        # Create sample user accounts and profiles
        print("👥 Creating sample users...")
        sample_data = [
            (AreaEnum.SEECS, "seecs.user@nust.edu.pk"),
            (AreaEnum.NBS, "nbs.user@nust.edu.pk"),
            (AreaEnum.ASAB, "asab.user@nust.edu.pk")
        ]
        
        user_info = []
        
        for area, email in sample_data:
            # Create user account
            user = User(
                email=email,
                password_hash=hash_password("password123")
            )
            
            # Generate secret key
            secret_key = generate_secret_key()
            profile = SecretKeyProfile(
                secret_key=secret_key,
                area=area,
                points=Config.INITIAL_USER_POINTS
            )
            
            db.session.add(user)
            db.session.add(profile)
            user_info.append((area.value, email, secret_key))
            print(f"   ✓ {area.value}")
        
        # Create admin
        print("\n👮 Creating admin...")
        admin_key = generate_secret_key()
        admin = Admin(admin_key=admin_key)
        db.session.add(admin)
        
        # Commit
        db.session.commit()
        
        # Display results
        print("\n" + "="*70)
        print("✅ FRESH START COMPLETE!")
        print("="*70)
        
        print("\n📝 SAMPLE USERS (password: password123):")
        for area, email, secret_key in user_info:
            print(f"\n   {area}:")
            print(f"      Email: {email}")
            print(f"      Secret Key: {secret_key}")
        
        print("\n" + "="*70)
        print("🔑 ADMIN KEY:")
        print("="*70)
        print(f"\n{admin_key}\n")
        print("="*70)
        print("\n✓ Database reset complete. Ready to use!")
        print("="*70 + "\n")


if __name__ == '__main__':
    try:
        fresh_start()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

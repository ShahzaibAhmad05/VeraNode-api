#!/usr/bin/env python3
"""
Database initialization script
Creates all tables and optionally adds sample data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, SecretKeyProfile, Admin, Rumor, Vote, BlockchainLedger, AreaEnum
from app.utils.helpers import generate_secret_key
from app.config import Config


def init_db():
    """Initialize database tables"""
    print("Initializing database...")
    app = create_app()
    
    with app.app_context():
        # Drop all tables (use with caution!)
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Check if we should create sample data
        user_count = User.query.count()
        if user_count == 0:
            print("\nNo users found. Creating sample data...")
            create_sample_data()
        else:
            print(f"\n✓ Database already contains {user_count} user(s)")
        
        print("\n✓ Database initialization complete!")


def create_sample_data():
    """Create sample users for testing"""
    sample_areas = [
        AreaEnum.SEECS,
        AreaEnum.NBS,
        AreaEnum.ASAB,
    ]
    
    created_keys = []
    
    for area in sample_areas:
        secret_key = generate_secret_key()
        
        # Create user record (registration only)
        user = User(
            secret_key=secret_key
        )
        
        # Create profile (data stored against secret key)
        profile = SecretKeyProfile(
            secret_key=secret_key,
            area=area,
            points=Config.INITIAL_USER_POINTS
        )
        
        db.session.add(user)
        db.session.add(profile)
        created_keys.append((secret_key, area.value))
        print(f"  - Created profile for area: {area.value}")
    
    db.session.commit()
    print("\n✓ Sample profiles created!")
    print("\nTest secret keys:")
    for key, area in created_keys:
        print(f"  Area {area}: {key}")


if __name__ == '__main__':
    init_db()

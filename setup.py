#!/usr/bin/env python3
"""
Setup script for VeraNode Backend API
Initializes database and creates sample data
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, SecretKeyProfile, Admin, AreaEnum
from app.utils.helpers import generate_secret_key
from app.config import Config


def setup_database():
    """Initialize database and create tables"""
    print("=" * 60)
    print("VeraNode Backend API - Database Setup")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        print("\n✓ Dropping existing tables...")
        db.drop_all()
        
        print("✓ Creating new database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        print("\n✓ Creating sample users and profiles...")
        create_sample_users()
        
        print("\n✓ Creating admin account...")
        create_admin()
        
        print("\n" + "=" * 60)
        print("Setup completed successfully!")
        print("=" * 60)
        print(f"\nAPI will run on: http://localhost:{app.config['PORT']}")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'configured'}")
        print("\nYou can now run the application with:")
        print("  python run.py")
        print("\nOr with Gunicorn (production):")
        print('  gunicorn --bind 0.0.0.0:3008 --workers 4 "app:create_app()"')
        print("\n" + "=" * 60)


def create_sample_users():
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
    print("\nTest secret keys (save these for login):")
    for key, area in created_keys:
        print(f"  Area {area}: {key}")


def create_admin():
    """Create default admin account"""
    admin_key = generate_secret_key()
    
    admin = Admin(
        admin_key=admin_key
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print("\n✓ Admin account created!")
    print("\n" + "=" * 70)
    print("ADMIN PRIVATE KEY (SAVE THIS - IT WILL NOT BE SHOWN AGAIN!):")
    print("=" * 70)
    print(f"\n{admin_key}\n")
    print("=" * 70)
    print("\nUse this key to login to the admin dashboard.")
    print("Keep it secure and do not share it with anyone!")
    print("=" * 70)


if __name__ == '__main__':
    try:
        setup_database()
    except Exception as e:
        print(f"\n✗ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

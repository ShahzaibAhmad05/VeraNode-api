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
from app.models import User, SecretKeyProfile, AreaEnum
import bcrypt
from app.utils.helpers import generate_secret_key


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
    sample_users = [
        {
            "university_id": "21i-1234",
            "password": "password123",
            "area": AreaEnum.SEECS
        },
        {
            "university_id": "21i-5678",
            "password": "password123",
            "area": AreaEnum.NBS
        },
        {
            "university_id": "22i-0001",
            "password": "password123",
            "area": AreaEnum.ASAB
        }
    ]
    
    for user_data in sample_users:
        password_hash = bcrypt.hashpw(
            user_data["password"].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        secret_key = generate_secret_key()
        
        # Create user account
        user = User(
            university_id=user_data["university_id"],
            password_hash=password_hash,
            secret_key=secret_key
        )
        
        # Create profile
        profile = SecretKeyProfile(
            secret_key=secret_key,
            area=user_data["area"],
            points=100
        )
        
        db.session.add(user)
        db.session.add(profile)
        print(f"  - Created user: {user_data['university_id']} ({user_data['area'].value})")
        print(f"    Secret Key: {secret_key}")
    
    db.session.commit()
    print("\n✓ Sample users created!")
    print("\nYou can login with:")
    print("  Secret Key: (see above)")
    print("  Or recover with: University ID: 21i-1234, Password: password123")


if __name__ == '__main__':
    try:
        setup_database()
    except Exception as e:
        print(f"\n✗ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

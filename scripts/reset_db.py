#!/usr/bin/env python3
"""
Database reset script
Drops all tables and recreates them
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db


def reset_db():
    """Reset database - drop and recreate all tables"""
    print("WARNING: This will delete all data in the database!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Database reset cancelled.")
        return
    
    print("\nResetting database...")
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        print("  - Dropping all tables...")
        db.drop_all()
        print("  ✓ All tables dropped")
        
        # Create all tables
        print("  - Creating all tables...")
        db.create_all()
        print("  ✓ All tables created")
        
        print("\n✓ Database reset complete!")
        print("\nTo add sample data, run: python scripts/init_db.py")


if __name__ == '__main__':
    reset_db()

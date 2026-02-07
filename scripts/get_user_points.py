#!/usr/bin/env python3
"""
Get User Points Script
Show points and profile details for all users or a specific secret key
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import SecretKeyProfile


def show_all_profiles():
    """Display all user profiles with points"""
    profiles = SecretKeyProfile.query.order_by(SecretKeyProfile.points.desc()).all()
    
    if not profiles:
        print("\n❌ No user profiles found in database")
        return
    
    print("\n" + "="*80)
    print("USER PROFILES & POINTS")
    print("="*80)
    
    for i, profile in enumerate(profiles, 1):
        blocked = " [BLOCKED]" if profile.is_blocked else ""
        
        print(f"\n[{i}] Secret Key: {profile.secret_key}")
        print(f"    Area: {profile.area.value}")
        print(f"    Points: {profile.points}{blocked}")
        print(f"    Created: {profile.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Key Expires: {profile.key_expires_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Show activity stats
        rumor_count = profile.rumors.count()
        vote_count = profile.votes.count()
        print(f"    Rumors Posted: {rumor_count}")
        print(f"    Votes Cast: {vote_count}")
    
    print("\n" + "="*80)
    print(f"Total Users: {len(profiles)}")
    print("="*80)


def show_profile_by_key(secret_key):
    """Display a specific profile by secret key"""
    profile = SecretKeyProfile.query.filter_by(secret_key=secret_key).first()
    
    if not profile:
        print(f"\n❌ No profile found for secret key: {secret_key[:20]}...")
        return
    
    print("\n" + "="*80)
    print("USER PROFILE DETAILS")
    print("="*80)
    
    print(f"\nSecret Key: {profile.secret_key}")
    print(f"Area: {profile.area.value}")
    print(f"Points: {profile.points}")
    print(f"Blocked: {'Yes' if profile.is_blocked else 'No'}")
    print(f"Created: {profile.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Key Created: {profile.key_created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Key Expires: {profile.key_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Key Expired: {'Yes' if profile.is_key_expired else 'No'}")
    
    # Activity details
    print(f"\n--- Activity ---")
    rumors = profile.rumors.all()
    votes = profile.votes.all()
    
    print(f"Rumors Posted: {len(rumors)}")
    if rumors:
        for rumor in rumors[:5]:  # Show last 5
            status = "FINAL" if rumor.is_final else "LOCKED" if rumor.is_locked else "ACTIVE"
            print(f"  - {rumor.content[:50]}... [{status}]")
    
    print(f"\nVotes Cast: {len(votes)}")
    if votes:
        for vote in votes[:5]:  # Show last 5
            print(f"  - {vote.vote_type.value} on {vote.rumor_id[:8]}... (weight: {vote.weight})")
    
    print("\n" + "="*80)


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("GET USER POINTS - INFO TOOL")
    print("="*80)
    
    app = create_app()
    
    with app.app_context():
        if len(sys.argv) > 1:
            # Specific secret key provided
            secret_key = sys.argv[1].strip()
            show_profile_by_key(secret_key)
        else:
            # Show all profiles
            show_all_profiles()
            
            # Option to check specific key
            print("\nTo check a specific key, run:")
            print("  python scripts/get_user_points.py <secret_key>")
            print()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

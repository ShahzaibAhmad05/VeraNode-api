"""
Trigger Lock Script
Set rumors to expire in 5 seconds to trigger the locking mechanism
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from app import create_app, db
from app.models import Rumor


def list_active_rumors():
    """List all active (not locked, not final) rumors"""
    now = datetime.utcnow()
    rumors = Rumor.query.filter(
        Rumor.is_locked == False,
        Rumor.is_final == False
    ).order_by(Rumor.posted_at.desc()).all()
    
    if not rumors:
        print("\n❌ No active rumors found in database")
        return []
    
    print("\n" + "="*80)
    print("ACTIVE RUMORS (Available for Lock Testing)")
    print("="*80)
    
    for i, rumor in enumerate(rumors, 1):
        time_remaining = rumor.voting_ends_at - now
        
        if time_remaining.total_seconds() > 0:
            hours_left = int(time_remaining.total_seconds() / 3600)
            status = f"ACTIVE ({hours_left}h left)"
        else:
            hours_expired = int(abs(time_remaining.total_seconds()) / 3600)
            status = f"ENDED ({hours_expired}h ago)"
        
        vote_count = rumor.votes.count()
        
        print(f"\n[{i}] {rumor.id[:8]}...")
        print(f"    Content: {rumor.content[:60]}...")
        print(f"    Area: {rumor.area_of_vote.value}")
        print(f"    Posted: {rumor.posted_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Voting Ends: {rumor.voting_ends_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Status: {status}")
        print(f"    Votes: {vote_count}")
    
    print("\n" + "="*80)
    return rumors


def trigger_lock(rumor, seconds=5):
    """Set rumor to expire in X seconds to trigger lock"""
    old_time = rumor.voting_ends_at
    rumor.voting_ends_at = datetime.utcnow() + timedelta(seconds=seconds)
    
    db.session.commit()
    
    print(f"\n✅ Rumor set to trigger lock!")
    print(f"   Old voting end time: {old_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   New voting end time: {rumor.voting_ends_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Time until expiration: {seconds} seconds")
    print(f"\n📌 What happens next:")
    print(f"   1. Wait {seconds} seconds for voting to expire")
    print(f"   2. Scheduler checks every 5 minutes and will lock the rumor")
    print(f"   3. After locking, another check (every 10 min) will finalize it")
    print(f"\n💡 TIP: Restart the server to trigger scheduler checks immediately")


def trigger_lock_all(rumors, seconds=5):
    """Set all rumors to expire in X seconds"""
    for rumor in rumors:
        rumor.voting_ends_at = datetime.utcnow() + timedelta(seconds=seconds)
    
    db.session.commit()
    
    print(f"\n✅ Set {len(rumors)} rumor(s) to expire in {seconds} seconds!")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("TRIGGER LOCK - TESTING TOOL")
    print("="*80)
    print("\nThis script sets rumors to expire in a few seconds,")
    print("triggering the automatic locking mechanism.\n")
    
    app = create_app()
    
    with app.app_context():
        # List all active rumors
        rumors = list_active_rumors()
        
        if not rumors:
            return
        
        # Get user selection
        try:
            print("\nOptions:")
            print("  [number] - Trigger lock for specific rumor")
            print("  [all]    - Trigger lock for all active rumors")
            print("  [Enter]  - Cancel")
            
            choice = input("\nSelect option: ").strip().lower()
            
            if not choice:
                print("\n❌ Cancelled")
                return
            
            # Ask for seconds
            seconds_input = input("\nExpire in how many seconds? (default: 5): ").strip()
            seconds = int(seconds_input) if seconds_input else 5
            
            if seconds < 1:
                print("\n❌ Seconds must be at least 1")
                return
            
            if choice == 'all':
                # Confirm all
                total = len(rumors)
                print(f"\n📋 CONFIRMATION")
                print(f"   Rumors to trigger: {total}")
                print(f"   Expiration time: {seconds} seconds from now")
                
                confirm = input("\nProceed? (yes/no): ").strip().lower()
                
                if confirm != 'yes':
                    print("\n❌ Cancelled")
                    return
                
                trigger_lock_all(rumors, seconds)
                
            else:
                # Trigger specific rumor
                index = int(choice) - 1
                
                if index < 0 or index >= len(rumors):
                    print("\n❌ Invalid selection")
                    return
                
                selected_rumor = rumors[index]
                
                # Confirm
                print(f"\n📋 CONFIRMATION")
                print(f"   Rumor: {selected_rumor.content[:50]}...")
                print(f"   Current end time: {selected_rumor.voting_ends_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   New end time: {seconds} seconds from now")
                print(f"   Votes: {selected_rumor.votes.count()}")
                
                confirm = input("\nProceed? (yes/no): ").strip().lower()
                
                if confirm != 'yes':
                    print("\n❌ Cancelled")
                    return
                
                trigger_lock(selected_rumor, seconds)
            
            print("\n" + "="*80)
            print("NEXT STEPS:")
            print("="*80)
            print(f"\n1. Wait {seconds} seconds for voting to expire")
            print("2. Wait for scheduler to run (or restart server)")
            print("3. Check status: python scripts/check_rumors.py")
            print("4. Rumor should be LOCKED, then FINALIZED")
            
        except ValueError:
            print("\n❌ Invalid input")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            db.session.rollback()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

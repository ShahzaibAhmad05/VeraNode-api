"""
End Voting Period Test Script
Manually set a rumor's voting period to end (for testing lock workflow)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from app import create_app, db
from app.models import Rumor


def list_rumors():
    """List all rumors with their status"""
    rumors = Rumor.query.order_by(Rumor.posted_at.desc()).all()
    
    if not rumors:
        print("\n❌ No rumors found in database")
        return []
    
    print("\n" + "="*80)
    print("AVAILABLE RUMORS")
    print("="*80)
    
    for i, rumor in enumerate(rumors, 1):
        time_remaining = rumor.voting_ends_at - datetime.utcnow()
        status = []
        
        if rumor.is_final:
            status.append(f"FINAL ({rumor.final_decision.value})")
        elif rumor.is_locked:
            status.append("LOCKED")
        elif time_remaining.total_seconds() <= 0:
            status.append("EXPIRED")
        else:
            status.append(f"ACTIVE ({int(time_remaining.total_seconds()/3600)}h left)")
        
        vote_count = rumor.votes.count()
        
        print(f"\n[{i}] {rumor.id[:8]}...")
        print(f"    Content: {rumor.content[:60]}...")
        print(f"    Area: {rumor.area_of_vote.value}")
        print(f"    Posted: {rumor.posted_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Voting Ends: {rumor.voting_ends_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Status: {', '.join(status)}")
        print(f"    Votes: {vote_count}")
    
    print("\n" + "="*80)
    return rumors


def end_voting(rumor, hours_ago=1):
    """Set a rumor's voting_ends_at to the past"""
    old_time = rumor.voting_ends_at
    rumor.voting_ends_at = datetime.utcnow() - timedelta(hours=hours_ago)
    
    db.session.commit()
    
    print(f"\n✅ Voting period ended successfully!")
    print(f"   Old voting end time: {old_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   New voting end time: {rumor.voting_ends_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"   (Set to {hours_ago} hour(s) ago)")
    print(f"\n📌 The scheduler will process this rumor in the next check cycle:")
    print(f"   - Lock voting check: every 5 minutes")
    print(f"   - Finalization check: every 10 minutes")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("END VOTING PERIOD - TESTING TOOL")
    print("="*80)
    print("\nThis script manually ends voting by setting voting_ends_at to the past.")
    print("Use this to test the automatic lock and finalization workflow.\n")
    
    app = create_app()
    
    with app.app_context():
        # List all rumors
        rumors = list_rumors()
        
        if not rumors:
            return
        
        # Get user selection
        try:
            choice = input("\nSelect rumor number to end voting (or Enter to cancel): ").strip()
            
            if not choice:
                print("\n❌ Cancelled")
                return
            
            index = int(choice) - 1
            
            if index < 0 or index >= len(rumors):
                print("\n❌ Invalid selection")
                return
            
            selected_rumor = rumors[index]
            
            # Check if already expired or final
            if selected_rumor.is_final:
                print(f"\n⚠️  Warning: This rumor is already finalized as {selected_rumor.final_decision.value}")
                confirm = input("   Expire anyway? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("\n❌ Cancelled")
                    return
            
            time_left = selected_rumor.voting_ends_at - datetime.utcnow()
            if time_left.total_seconds() <= 0:
                print("\n⚠️  Warning: Voting has already ended for this rumor")
                confirm = input("   Set to even earlier time? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("\n❌ Cancelled")
                    return
            
            # Ask how many hours ago to set
            hours = input("\nSet voting end time to how many hours ago? (default: 1): ").strip()
            hours_ago = int(hours) if hours else 1
            
            # Confirm
            print(f"\n📋 CONFIRMATION")
            print(f"   Rumor: {selected_rumor.content[:50]}...")
            print(f"   Current end time: {selected_rumor.voting_ends_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   New end time: {hours_ago} hour(s) ago")
            
            confirm = input("\nProceed? (yes/no): ").strip().lower()
            
            if confirm != 'yes':
                print("\n❌ Cancelled")
                return
            
            # Expire the rumor
            end_voting(selected_rumor, hours_ago)
            
            # Show next steps
            print("\n" + "="*80)
            print("NEXT STEPS:")
            print("="*80)
            print("\n1. Wait for scheduler to process (or restart server to trigger immediately)")
            print("2. Check rumor status with: python scripts/check_rumors.py")
            print("3. The rumor should be locked first, then finalized after AI analysis")
            print("4. Check blockchain ledger after finalization")
            
        except ValueError:
            print("\n❌ Invalid input")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

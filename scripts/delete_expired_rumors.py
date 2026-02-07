"""
Delete Completed Rumors Script
Remove finalized rumors from the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
from app import create_app, db
from app.models import Rumor


def list_completed_rumors():
    """List all rumors where voting has ended"""
    now = datetime.utcnow()
    rumors = Rumor.query.filter(Rumor.voting_ends_at <= now).order_by(Rumor.posted_at.desc()).all()
    
    if not rumors:
        print("\n❌ No completed rumors found in database")
        return []
    
    print("\n" + "="*80)
    print("COMPLETED RUMORS (Voting Ended)")
    print("="*80)
    
    for i, rumor in enumerate(rumors, 1):
        time_expired = now - rumor.voting_ends_at
        hours_expired = int(time_expired.total_seconds() / 3600)
        
        status = []
        if rumor.is_final:
            status.append(f"FINAL ({rumor.final_decision.value})")
        elif rumor.is_locked:
            status.append("LOCKED")
        else:
            status.append(f"ENDED ({hours_expired}h ago)")
        
        vote_count = rumor.votes.count()
        
        print(f"\n[{i}] {rumor.id[:8]}...")
        print(f"    Content: {rumor.content[:60]}...")
        print(f"    Area: {rumor.area_of_vote.value}")
        print(f"    Posted: {rumor.posted_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Ended: {rumor.voting_ends_at.strftime('%Y-%m-%d %H:%M')} ({hours_expired}h ago)")
        print(f"    Status: {', '.join(status)}")
        print(f"    Votes: {vote_count}")
    
    print("\n" + "="*80)
    return rumors


def delete_rumor(rumor):
    """Delete a rumor and all associated votes"""
    rumor_id = rumor.id
    content = rumor.content[:50]
    vote_count = rumor.votes.count()
    
    # Delete the rumor (cascades to votes due to relationship)
    db.session.delete(rumor)
    db.session.commit()
    
    print(f"\n✅ Rumor deleted successfully!")
    print(f"   ID: {rumor_id[:16]}...")
    print(f"   Content: {content}...")
    print(f"   {vote_count} vote(s) also deleted")


def delete_all_completed(rumors):
    """Delete all completed rumors"""
    total = len(rumors)
    vote_total = sum(r.votes.count() for r in rumors)
    
    for rumor in rumors:
        db.session.delete(rumor)
    
    db.session.commit()
    
    print(f"\n✅ Deleted {total} completed rumor(s) and {vote_total} vote(s)")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("DELETE COMPLETED RUMORS - CLEANUP TOOL")
    print("="*80)
    print("\nThis script removes rumors where voting has ended from the database.")
    print("⚠️  WARNING: This action cannot be undone!\n")
    
    app = create_app()
    
    with app.app_context():
        # List all completed rumors
        rumors = list_completed_rumors()
        
        if not rumors:
            return
        
        # Get user selection
        try:
            print("\nOptions:")
            print("  [number] - Delete specific rumor")
            print("  [all]    - Delete all completed rumors")
            print("  [Enter]  - Cancel")
            
            choice = input("\nSelect option: ").strip().lower()
            
            if not choice:
                print("\n❌ Cancelled")
                return
            
            if choice == 'all':
                # Confirm deletion of all
                total = len(rumors)
                print(f"\n⚠️  WARNING: This will delete {total} rumor(s) and all associated votes!")
                confirm = input("   Type 'DELETE ALL' to confirm: ").strip()
                
                if confirm != 'DELETE ALL':
                    print("\n❌ Cancelled")
                    return
                
                delete_all_completed(rumors)
                
            else:
                # Delete specific rumor
                index = int(choice) - 1
                
                if index < 0 or index >= len(rumors):
                    print("\n❌ Invalid selection")
                    return
                
                selected_rumor = rumors[index]
                
                # Confirm deletion
                print(f"\n📋 CONFIRMATION")
                print(f"   Rumor: {selected_rumor.content[:50]}...")
                print(f"   Votes: {selected_rumor.votes.count()}")
                print(f"   Status: {'FINAL' if selected_rumor.is_final else 'LOCKED' if selected_rumor.is_locked else 'EXPIRED'}")
                
                if selected_rumor.is_final:
                    print(f"\n⚠️  WARNING: This rumor is finalized and may be in the blockchain!")
                
                confirm = input("\nType 'DELETE' to confirm: ").strip()
                
                if confirm != 'DELETE':
                    print("\n❌ Cancelled")
                    return
                
                delete_rumor(selected_rumor)
            
            print("\n" + "="*80)
            print("✅ CLEANUP COMPLETE!")
            print("="*80)
            
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

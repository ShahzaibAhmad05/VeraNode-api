#!/usr/bin/env python3
"""
Show API responses with hidden vs visible stats
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
import json


def show_stats_behavior():
    """Show how stats behave for active vs finalized rumors"""
    app = create_app()
    
    with app.test_client() as client:
        print("\n" + "="*80)
        print("VOTING STATISTICS BEHAVIOR")
        print("="*80)
        
        response = client.get('/api/rumors')
        data = response.get_json()
        
        active_rumors = [r for r in data['rumors'] if not r['isFinal']]
        final_rumors = [r for r in data['rumors'] if r['isFinal']]
        
        print(f"\n📊 Total Rumors: {len(data['rumors'])}")
        print(f"   Active/Locked: {len(active_rumors)}")
        print(f"   Finalized: {len(final_rumors)}")
        
        if active_rumors:
            print("\n" + "="*80)
            print("ACTIVE/LOCKED RUMORS - STATS HIDDEN")
            print("="*80)
            
            rumor = active_rumors[0]
            print(f"\nRumor: {rumor['content'][:60]}...")
            print(f"Status: {'Locked' if rumor['isLocked'] else 'Active'}")
            print(f"Is Final: {rumor['isFinal']}")
            print(f"\nStats Object:")
            print(json.dumps(rumor['stats'], indent=2))
            
            print("\n🔒 Frontend should:")
            print("   - Check: stats.totalVotes === 'hidden'")
            print("   - Display: 'Results hidden until voting ends'")
            print("   - Hide: All vote counts, progress bars, percentages")
        
        if final_rumors:
            print("\n" + "="*80)
            print("FINALIZED RUMORS - STATS VISIBLE")
            print("="*80)
            
            rumor = final_rumors[0]
            print(f"\nRumor: {rumor['content'][:60]}...")
            print(f"Status: Finalized")
            print(f"Is Final: {rumor['isFinal']}")
            print(f"Final Decision: {rumor['finalDecision']}")
            print(f"\nStats Object:")
            print(json.dumps(rumor['stats'], indent=2))
            
            print("\n✅ Frontend should:")
            print("   - Check: typeof stats.totalVotes === 'number'")
            print("   - Display: All statistics and vote breakdown")
            print("   - Show: Final decision, progress bars, percentages")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print("\n✓ Active/Locked rumors: stats.totalVotes = 'hidden'")
        print("✓ Finalized rumors: stats.totalVotes = number")
        print("✓ This prevents bandwagon effect during voting")
        print("✓ Users vote based on knowledge, not crowd behavior")
        print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    show_stats_behavior()

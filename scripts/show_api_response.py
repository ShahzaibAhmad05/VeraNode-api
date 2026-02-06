#!/usr/bin/env python3
"""
Show exactly what frontend receives from API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
import json


def show_api_response():
    """Show actual API response for frontend"""
    app = create_app()
    
    with app.test_client() as client:
        print("\n" + "="*80)
        print("EXACT API RESPONSE FOR FRONTEND")
        print("="*80)
        
        # Get all rumors
        response = client.get('/api/rumors')
        data = response.get_json()
        
        print(f"\nGET /api/rumors")
        print(f"Status: {response.status_code}")
        print(f"\nResponse (pretty-printed JSON):")
        print(json.dumps(data, indent=2))
        
        if data.get('rumors'):
            first_rumor = data['rumors'][0]
            
            print("\n" + "="*80)
            print("TIME CALCULATION GUIDE FOR FRONTEND")
            print("="*80)
            
            print(f"\nRumor data from API:")
            print(f"  postedAt: {first_rumor['postedAt']}")
            print(f"  votingEndsAt: {first_rumor['votingEndsAt']}")
            
            print(f"\nJavaScript code to calculate time remaining:")
            print(f"""
const endTime = new Date("{first_rumor['votingEndsAt']}");
const now = new Date();
const secondsLeft = Math.floor((endTime - now) / 1000);

// Display as hours and minutes
const hoursLeft = Math.floor(secondsLeft / 3600);
const minutesLeft = Math.floor((secondsLeft % 3600) / 60);
console.log(`Ends in ${{hoursLeft}}h ${{minutesLeft}}m`);
""")
            
            print("\n" + "="*80)
            print("COMMON MISTAKES")
            print("="*80)
            print("\n❌ WRONG - Fetching with area filter:")
            print("   fetch('/api/rumors?area=SEECS')")
            print("\n✅ CORRECT - Fetch all rumors:")
            print("   fetch('/api/rumors')")
            print("\n❌ WRONG - Creating rumor with votingEndsAt:")
            print("   { content: '...', votingEndsAt: '2026-02-09...' }")
            print("\n✅ CORRECT - Let backend set voting time:")
            print("   { content: '...', areaOfVote: 'General' }")


if __name__ == '__main__':
    show_api_response()

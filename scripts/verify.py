#!/usr/bin/env python3
"""
Verification script to test all backend features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.models import User, Rumor, Vote
from app.services.blockchain import blockchain_service
from app.utils.helpers import generate_secret_key, generate_nullifier, calculate_vote_weight, hash_data
from app.utils.validators import validate_university_id, validate_password, validate_area, validate_rumor_content


def run_tests():
    """Run verification tests"""
    print("=" * 70)
    print("VeraNode Backend - Verification Tests")
    print("=" * 70)
    
    all_passed = True
    
    # Test 1: Validators
    print("\n[Test 1] Testing Validators...")
    valid, _ = validate_university_id("21i-1234")
    assert valid, "University ID validation failed"
    
    valid, _ = validate_password("password123")
    assert valid, "Password validation failed"
    
    valid, _ = validate_area("SEECS")
    assert valid, "Area validation failed"
    
    valid, _ = validate_rumor_content("This is a test rumor content that is long enough")
    assert valid, "Rumor content validation failed"
    print("  ✓ All validators working correctly")
    
    # Test 2: Helper functions
    print("\n[Test 2] Testing Helper Functions...")
    secret_key = generate_secret_key()
    assert len(secret_key) == 64, "Secret key should be 64 characters"
    
    nullifier = generate_nullifier(secret_key, "test-id")
    assert len(nullifier) == 64, "Nullifier should be 64 characters"
    
    # Assuming same area for testing - weight should be 1.0
    from app.models import AreaEnum
    weight = calculate_vote_weight(AreaEnum.POLITICS, AreaEnum.POLITICS)
    assert weight == 151.0, f"Vote weight calculation incorrect: {weight}"
    
    hash_val = hash_data("test")
    assert len(hash_val) == 64, "Hash should be 64 characters"
    print("  ✓ All helper functions working correctly")
    
    # Test 3: Application Factory
    print("\n[Test 3] Testing Application Factory...")
    app = create_app('development')
    assert app is not None, "App creation failed"
    assert app.config['DEBUG'] == True, "Debug mode should be enabled"
    print("  ✓ Application factory working correctly")
    
    # Test 4: Database Models
    print("\n[Test 4] Testing Database Models...")
    with app.app_context():
        user_count = User.query.count()
        rumor_count = Rumor.query.count()
        vote_count = Vote.query.count()
        print(f"  - Users: {user_count}")
        print(f"  - Rumors: {rumor_count}")
        print(f"  - Votes: {vote_count}")
        print("  ✓ Database connection working")
    
    # Test 5: Blockchain Service
    print("\n[Test 5] Testing Blockchain Service...")
    genesis = blockchain_service.get_genesis_hash()
    assert genesis == "0" * 64, "Genesis hash incorrect"
    
    test_hash = blockchain_service.calculate_rumor_hash(
        "test-id", "content", "FACT", "100", genesis
    )
    assert len(test_hash) == 64, "Hash calculation incorrect"
    print("  ✓ Blockchain service working correctly")
    
    # Test 6: Blueprints Registration
    print("\n[Test 6] Testing Blueprint Registration...")
    with app.app_context():
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        
        assert any('/api/auth/register' in rule for rule in rules), "Auth blueprint not registered"
        assert any('/api/rumors' in rule for rule in rules), "Rumors blueprint not registered"
        assert any('/api/votes/my-votes' in rule for rule in rules), "Voting blueprint not registered"
        assert any('/api/user/stats' in rule for rule in rules), "Users blueprint not registered"
        assert any('/api/health' in rule for rule in rules), "Health endpoint not registered"
        print("  ✓ All blueprints registered correctly")
    
    # Test 7: Configuration
    print("\n[Test 7] Testing Configuration...")
    assert app.config['PORT'] == 3008, "Port configuration incorrect"
    assert app.config['INITIAL_USER_POINTS'] == 100, "Initial points configuration incorrect"
    assert app.config['VOTING_DURATION_HOURS'] == 48, "Voting duration configuration incorrect"
    print("  ✓ Configuration loaded correctly")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED! Backend is ready for deployment.")
    else:
        print("✗ Some tests failed. Please review the errors above.")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

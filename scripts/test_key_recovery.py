"""
Test Script: Key Recovery System
Tests the new key recovery functionality
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/auth"

def test_registration():
    """Test normal registration"""
    print("\n=== Testing Normal Registration ===")
    response = requests.post(f"{BASE_URL}/register", json={
        "email": f"test_{int(datetime.now().timestamp())}@nust.edu.pk",
        "password": "TestPassword123!",
        "department": "SEECS"
    })
    
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Secret Key: {data.get('secretKey', 'N/A')}")
    print(f"Expires: {data.get('profile', {}).get('keyExpiresAt', 'N/A')}")
    print(f"Recovered: {data.get('recovered', False)}")
    return data.get('secretKey')

def test_check_key_status(key):
    """Test key status check"""
    print("\n=== Checking Key Status ===")
    response = requests.post(f"{BASE_URL}/check-key-status", json={"secretKey": key})
    data = response.json()
    print(f"Exists: {data.get('exists', False)}")
    print(f"Expired: {data.get('isExpired', False)}")
    print(f"Message: {data.get('message', 'N/A')}")

def test_login(key):
    """Test login"""
    print("\n=== Testing Login ===")
    response = requests.post(f"{BASE_URL}/login", json={"secretKey": key})
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Success: {data.get('success', False)}")
    if not data.get('success'):
        print(f"Error: {data.get('code', 'N/A')} - {data.get('error', 'N/A')}")

def test_recovery(expired_key):
    """Test key recovery"""
    print("\n=== Testing Key Recovery ===")
    response = requests.post(f"{BASE_URL}/register", json={
        "email": f"recovery_{int(datetime.now().timestamp())}@nust.edu.pk",
        "password": "TestPassword123!",
        "department": "SEECS",
        "previousSecretKey": expired_key
    })
    
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Recovered: {data.get('recovered', False)}")
    if data.get('recovered'):
        print(f"New Key: {data.get('secretKey', 'N/A')}")
        print(f"Points: {data.get('profile', {}).get('points', 'N/A')}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  KEY RECOVERY SYSTEM - TEST SCRIPT")
    print("="*60)
    
    # Test basic flow
    key = test_registration()
    if key:
        test_check_key_status(key)
        test_login(key)
    
    # Test with expired key (manual)
    print("\n" + "="*60)
    expired = input("\nEnter expired key to test recovery (or Enter to skip): ").strip()
    if expired:
        test_check_key_status(expired)
        test_login(expired)
        test_recovery(expired)
    
    print("\n" + "="*60)
    print("✅ Tests complete!")
    print("="*60)

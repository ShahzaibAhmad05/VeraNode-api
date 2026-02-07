import hashlib
import secrets
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Hash a password using werkzeug's secure hashing"""
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Verify a password against its hash"""
    return check_password_hash(password_hash, password)


def generate_secret_key():
    """Generate a 64-character hexadecimal secret key"""
    return secrets.token_hex(32)


def generate_nullifier(secret_key: str, identifier: str) -> str:
    """Generate a deterministic nullifier hash for privacy"""
    combined = secret_key + identifier
    return hashlib.sha256(combined.encode()).hexdigest()


def calculate_vote_weight(user_area, rumor_area) -> float:
    """Calculate vote weight based on area proximity"""
    # Within area: weight = 1.0, Outside area: weight = 0.3
    is_within_area = (user_area == rumor_area)
    return 1.0 if is_within_area else 0.3


def hash_data(data: str) -> str:
    """Generate SHA-256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()

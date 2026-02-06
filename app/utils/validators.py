import re
from app.models import AreaEnum


def validate_edu_email(email: str) -> tuple[bool, str]:
    """Validate .edu.pk email format"""
    if not email:
        return False, "Email is required"
    
    email = email.strip().lower()
    
    # Check basic email format (contains @ and at least one dot)
    if '@' not in email or '.' not in email:
        return False, "Invalid email format"
    
    # Check if email ends with .edu.pk
    if not email.endswith('.edu.pk'):
        return False, "Email must end with .edu.pk"
    
    # Basic email pattern validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.edu\.pk$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def validate_university_id(university_id: str) -> tuple[bool, str]:
    """Validate university ID format (e.g., 21i-1234)"""
    if not university_id:
        return False, "University ID is required"
    
    # Pattern: 2 digits, letter 'i', hyphen, 4 digits
    pattern = r'^\d{2}[a-zA-Z]-\d{4}$'
    if not re.match(pattern, university_id):
        return False, "Invalid university ID format. Expected format: 21i-1234"
    
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    return True, ""


def validate_area(area: str) -> tuple[bool, str]:
    """Validate area enum value"""
    if not area:
        return False, "Area is required"
    
    valid_areas = [e.value for e in AreaEnum]
    if area not in valid_areas:
        return False, f"Invalid area. Must be one of: {', '.join(valid_areas)}"
    
    return True, ""


def validate_rumor_content(content: str) -> tuple[bool, str]:
    """Validate rumor content"""
    if not content:
        return False, "Rumor content is required"
    
    content = content.strip()
    if len(content) < 10:
        return False, "Rumor content must be at least 10 characters"
    
    if len(content) > 5000:
        return False, "Rumor content must not exceed 5000 characters"
    
    return True, ""

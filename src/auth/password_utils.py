"""Password hashing and verification utilities."""
from passlib.context import CryptContext

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_password_hash(password: str) -> str:
    """Generate a secure hash from a password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)

def check_password_hash(hashed_password: str, password: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        hashed_password: The hashed password to verify against
        password: The plain text password to verify
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    return pwd_context.verify(password, hashed_password)

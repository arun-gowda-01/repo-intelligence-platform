import hashlib
from utils.db import get_user_by_email


def hash_password(password: str) -> str:
    """Hash a plaintext password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(email: str, password: str) -> bool:
    """
    Authenticate a user by checking their email and password
    against the stored, hashed password in the database.
    """
    user = get_user_by_email(email)
    if user is None:
        return False
    return user["password_hash"] == hash_password(password)


def generate_session_token(user_id: int) -> str:
    """Generate a simple session token for a logged-in user."""
    import uuid
    return f"{user_id}-{uuid.uuid4().hex}"

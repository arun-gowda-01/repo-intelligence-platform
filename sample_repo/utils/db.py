_FAKE_DB = {
    "arun@example.com": {"password_hash": "abc123", "id": 1},
}


def get_user_by_email(email: str):
    """Look up a user record by email address. Returns None if not found."""
    return _FAKE_DB.get(email)


def save_user(email: str, password_hash: str) -> None:
    """Save a new user record to the database."""
    _FAKE_DB[email] = {"password_hash": password_hash, "id": len(_FAKE_DB) + 1}

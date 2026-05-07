import secrets


def new_public_id() -> str:
    return secrets.token_urlsafe(16)

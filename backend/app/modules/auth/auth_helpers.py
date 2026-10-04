import bcrypt

# Max bytes bcrypt will hash; bcrypt>=5 raises ValueError beyond this.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


# Checked against when the email doesn't exist, so a login for an unknown
# email takes as long as one with a wrong password (no user enumeration by timing).
DUMMY_PASSWORD_HASH = hash_password("speakwise-dummy-password")

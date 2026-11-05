"""Password hashing with PBKDF2 (standard library, no extra packages)."""
import hashlib
import hmac
import secrets

ITERATIONS = 200_000


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS)
    return digest.hex(), salt


def verify_password(password, stored_hash, salt):
    digest, _ = hash_password(password, salt)
    return hmac.compare_digest(digest, stored_hash)

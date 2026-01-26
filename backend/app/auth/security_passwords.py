import os
import bcrypt

# Fix for passlib warning with bcrypt 4.x ("AttributeError: module 'bcrypt' has no attribute '__about__'")
# This monkey-patch ensures passlib find the version info it expects.
if not hasattr(bcrypt, "__about__"):
    class _BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "4.0.0")
    bcrypt.__about__ = _BcryptAbout

from passlib.context import CryptContext

# Allow configuring bcrypt rounds via env var BCRYPT_ROUNDS (default 12)
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
_pwd = CryptContext(schemes=["bcrypt"], bcrypt__rounds=BCRYPT_ROUNDS, deprecated="auto")


def hash_password(raw: str) -> str:
    return _pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd.verify(raw, hashed)

from passlib.context import CryptContext
import os

# Allow configuring bcrypt rounds via env var BCRYPT_ROUNDS (default 12)
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
_pwd = CryptContext(schemes=["bcrypt"], bcrypt__rounds=BCRYPT_ROUNDS, deprecated="auto")


def hash_password(raw: str) -> str:
    return _pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd.verify(raw, hashed)

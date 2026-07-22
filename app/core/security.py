"""
Auth primitives: password hashing, JWT access tokens, refresh token generation.

Two DIFFERENT hashing schemes are used deliberately here, for two different jobs:

1. Passwords -> bcrypt (via the `bcrypt` package directly, not passlib — passlib's
   bcrypt backend is broken against bcrypt>=4.1, since it reads a __about__.__version__
   attribute bcrypt removed; passlib hasn't shipped a fix since 2020).
   Bcrypt is deliberately SLOW and salted per-hash — that's the correct property
   for low-entropy, human-chosen secrets that need brute-force resistance.

2. Refresh tokens -> SHA-256, not bcrypt. A refresh token is 512 bits of
   os.urandom-backed entropy (via secrets.token_urlsafe), not a human secret —
   there's nothing to brute-force. More importantly, bcrypt is SALTED, which
   makes it unsuitable for this job: on every /auth/refresh call we need to look
   up a token by exact hash match in a single indexed query. A salted hash can't
   be looked up that way — you'd have to pull every stored token and run
   bcrypt.checkpw against each one. A fast, unsalted, deterministic hash (SHA-256)
   is the correct tool for "look this exact value up in a DB index."
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.models.user import UserRole


def utcnow() -> datetime:
    """
    Naive UTC datetime, matching the rest of the schema (organizations.created_at,
    users.created_at etc. use server_default=func.now() against a
    TIMESTAMP WITHOUT TIME ZONE column). datetime.utcnow() is deprecated as of
    Python 3.12, so we get an aware UTC time and strip the tzinfo instead.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------- Passwords ----------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


# ---------- Access tokens (JWT, stateless) ----------

def create_access_token(*, user_id, org_id, role: UserRole) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": role.value,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (or a subclass) on invalid/expired tokens — caller handles it."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


# ---------- Refresh tokens (opaque, DB-backed, revocable) ----------

def generate_refresh_token() -> str:
    """Raw token returned to the client exactly once, at issuance. Never stored raw."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
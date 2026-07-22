from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    utcnow,
    verify_password,
)
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token_pair(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(user_id=user.id, org_id=user.org_id, role=user.role)

    raw_refresh_token = generate_refresh_token()
    expires_at = utcnow() + timedelta(days=settings.refresh_token_expire_days)
    RefreshTokenRepository(db).create(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=expires_at,
    )

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh_token)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Creates a NEW organization + its first user (role=admin) in one transaction.
    There is no "join an existing org" flow — see SignupRequest docstring.
    """
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    org = Organization(name=payload.organization_name)
    db.add(org)
    db.flush()  # need org.id populated before creating the user row below

    user = User(
        org_id=org.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.flush()

    AuditLogRepository(db).create(
        org_id=org.id,
        action="user.signed_up",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        event_metadata={"organization_name": org.name, "email": user.email},
    )

    tokens = _issue_token_pair(db, user)
    db.commit()
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Deliberately identical error and status code whether the email doesn't
    # exist or the password is wrong. Distinguishing them lets an attacker
    # enumerate which emails are registered — a real, well-known anti-pattern.
    if user is None or not verify_password(payload.password, user.hashed_password):
        # Only logged when the user EXISTS — audit_log.org_id is NOT NULL, so
        # a failed attempt against a nonexistent email has no org to attribute
        # it to and can't be recorded here. A real gap for security
        # monitoring (can't detect email-enumeration probing this way), named
        # rather than silently accepted — see decisions log.
        if user is not None:
            AuditLogRepository(db).create(
                org_id=user.org_id,
                action="user.login_failed",
                resource_type="user",
                resource_id=user.id,
                user_id=user.id,
            )
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    AuditLogRepository(db).create(
        org_id=user.org_id,
        action="user.logged_in",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
    )

    tokens = _issue_token_pair(db, user)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """
    No rotation: the same refresh token is returned back to the client and
    stays valid until its natural expiry or an explicit /auth/logout. Token
    rotation + reuse detection was deliberately NOT built — see decisions log
    for why (real defense-in-depth technique, but disproportionate complexity
    for a solo portfolio project's actual threat model).

    Not audit-logged: this would fire every ~30 minutes per active user and
    add noise without much signal — login/logout are the meaningful session
    boundaries, a routine token refresh isn't.
    """
    repo = RefreshTokenRepository(db)
    token_row = repo.get_valid_by_hash(hash_refresh_token(payload.refresh_token))
    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == token_row.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token(user_id=user.id, org_id=user.org_id, role=user.role)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    """
    Revokes the refresh token so it can no longer be used at /auth/refresh.
    Does NOT invalidate the current access token (it's stateless JWT — there's
    nothing to revoke) — logout takes full effect once the access token expires
    naturally, up to access_token_expire_minutes later. This is the real
    trade-off of stateless access tokens; worth being able to say out loud.
    """
    repo = RefreshTokenRepository(db)
    token_hash = hash_refresh_token(payload.refresh_token)

    # Look the token up BEFORE revoking it, purely to get user_id/org_id for
    # the audit entry — revoke() alone doesn't return enough to log against.
    token_row = repo.get_valid_by_hash(token_hash)
    if token_row is not None:
        user = db.query(User).filter(User.id == token_row.user_id).first()
        if user is not None:
            AuditLogRepository(db).create(
                org_id=user.org_id,
                action="user.logged_out",
                resource_type="user",
                resource_id=user.id,
                user_id=user.id,
            )

    repo.revoke(token_hash)
    db.commit()
    return None
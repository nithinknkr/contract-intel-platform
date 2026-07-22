import uuid
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

# tokenUrl is just for the OpenAPI/Swagger "Authorize" button — doesn't affect
# actual token validation, which happens in get_current_user below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Re-queries the user row on every request rather than trusting the JWT's
    embedded org_id/role claims. This costs one extra indexed query per
    request, in exchange for: a role change or account deactivation takes
    effect immediately, not "whenever this user's 30-minute access token
    happens to expire." Worth logging as a deliberate consistency-over-latency
    trade-off — the alternative (trust the claims) is also defensible, just
    not what was chosen here.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_error

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_error

    if payload.get("type") != "access":
        raise credentials_error

    raw_user_id = payload.get("sub")
    if raw_user_id is None:
        raise credentials_error

    try:
        user_id = uuid.UUID(raw_user_id)
    except ValueError:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_error

    return user


def get_current_org_id(current_user: User = Depends(get_current_user)) -> uuid.UUID:
    """
    The single dependency every tenant-scoped route should use to get its
    org_id — never read org_id off a request body/query param, always off
    the authenticated token's resolved user.
    """
    return current_user.org_id


def require_role(*allowed_roles: UserRole) -> Callable[..., User]:
    """
    Usage: @router.delete(..., dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.REVIEWER))])
    Activates the role field that's existed on the users table since A2 but
    was never actually enforced anywhere until now.
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return dependency
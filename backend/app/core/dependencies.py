from typing import Annotated
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, hash_api_key
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.repositories.event import APIKeyRepository

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise AuthenticationError()
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        user_id: str = payload.get("sub")
        if not user_id:
            raise AuthenticationError()
    except JWTError:
        raise AuthenticationError()

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_org_from_api_key(
    api_key: Annotated[str | None, Depends(api_key_header)],
    db: AsyncSession = Depends(get_db),
) -> str:
    """Used for event ingestion — returns org_id from API key."""
    if not api_key:
        raise AuthenticationError("API key required")
    key_hash = hash_api_key(api_key)
    repo = APIKeyRepository(db)
    api_key_obj = await repo.get_by_hash(key_hash)
    if not api_key_obj or not api_key_obj.is_active or api_key_obj.revoked_at:
        raise AuthenticationError("Invalid or revoked API key")
    await repo.update_last_used(api_key_obj.id)
    return str(api_key_obj.organization_id)


def require_role(*roles: UserRole):
    """Factory for role-based permission guards."""
    async def guard(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise AuthorizationError(f"Required role: {[r.value for r in roles]}")
        return current_user
    return guard


def require_min_role(min_role: UserRole):
    """Require at least a minimum role in the hierarchy."""
    hierarchy = [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN, UserRole.OWNER]
    min_index = hierarchy.index(min_role)

    async def guard(current_user: CurrentUser) -> User:
        if hierarchy.index(current_user.role) < min_index:
            raise AuthorizationError(f"Minimum role required: {min_role.value}")
        return current_user
    return guard

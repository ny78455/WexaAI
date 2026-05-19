import uuid
from datetime import datetime, timedelta, timezone
from fastapi import Response

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, create_invite_token,
)
from app.core.exceptions import ConflictError, AuthenticationError, NotFoundError, ValidationError
from app.core.config import settings
from app.repositories.user import UserRepository, OrganizationRepository, InvitationRepository
from app.db.models.user import UserRole
from app.schemas.auth import UserCreate, UserLogin, InviteCreate, InviteAccept
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.invite_repo = InvitationRepository(db)

    async def signup(self, data: UserCreate):
        # Check email uniqueness
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already registered")

        # Create organization
        slug = data.organization_name.lower().replace(" ", "-").replace("_", "-")
        existing_org = await self.org_repo.get_by_slug(slug)
        if existing_org:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        org = await self.org_repo.create(name=data.organization_name, slug=slug)

        # Create user as Owner
        user = await self.user_repo.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            organization_id=org.id,
            role=UserRole.OWNER,
            is_verified=True,
        )

        logger.info("user.signup", user_id=str(user.id), org_id=str(org.id))
        return user

    async def login(self, data: UserLogin, response: Response):
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        access_token = create_access_token(str(user.id), {"org_id": str(user.organization_id), "role": user.role.value})
        refresh_token = create_refresh_token(str(user.id))

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            secure=not settings.DEBUG,
            samesite="lax",
        )

        return access_token, user

    async def refresh_access_token(self, refresh_token: str):
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")
            user_id = payload.get("sub")
        except Exception:
            raise AuthenticationError("Invalid refresh token")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError()

        access_token = create_access_token(str(user.id), {"org_id": str(user.organization_id), "role": user.role.value})
        return access_token, user

    async def create_invite(self, org_id: uuid.UUID, data: InviteCreate, inviter_id: uuid.UUID):
        token = create_invite_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invite = await self.invite_repo.create(
            org_id=org_id, email=data.email, token=token, role=data.role, expires_at=expires_at
        )
        invite_url = f"{settings.FRONTEND_URL}/invite/accept?token={token}"
        logger.info("invite.created", email=data.email, org_id=str(org_id), url=invite_url)
        # In production, send email. For now, log the URL.
        return invite, invite_url

    async def accept_invite(self, data: InviteAccept):
        invite = await self.invite_repo.get_by_token(data.token)
        if not invite:
            raise NotFoundError("Invalid invitation token")
        if invite.accepted_at:
            raise ConflictError("Invitation already accepted")
        if invite.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Invitation has expired")

        existing = await self.user_repo.get_by_email(invite.email)
        if existing:
            raise ConflictError("Email already registered")

        user = await self.user_repo.create(
            email=invite.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            organization_id=invite.organization_id,
            role=invite.role,
            is_verified=True,
        )

        await self.db.execute(
            __import__("sqlalchemy").update(__import__("app.db.models.user", fromlist=["Invitation"]).Invitation)
            .where(__import__("app.db.models.user", fromlist=["Invitation"]).Invitation.id == invite.id)
            .values(accepted_at=datetime.now(timezone.utc))
        )

        logger.info("invite.accepted", user_id=str(user.id), org_id=str(invite.organization_id))
        return user

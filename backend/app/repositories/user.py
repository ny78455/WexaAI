import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User, Organization, Invitation, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_org_users(self, org_id: uuid.UUID) -> list[User]:
        result = await self.db.execute(select(User).where(User.organization_id == org_id))
        return list(result.scalars().all())

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: uuid.UUID, **kwargs) -> User | None:
        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        return await self.get_by_id(user_id)


class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        result = await self.db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.db.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, name: str, slug: str) -> Organization:
        org = Organization(name=name, slug=slug)
        self.db.add(org)
        await self.db.flush()
        await self.db.refresh(org)
        return org


class InvitationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> Invitation | None:
        result = await self.db.execute(select(Invitation).where(Invitation.token == token))
        return result.scalar_one_or_none()

    async def create(self, org_id: uuid.UUID, email: str, token: str, role: UserRole, expires_at) -> Invitation:
        invite = Invitation(
            organization_id=org_id, email=email, token=token, role=role, expires_at=expires_at
        )
        self.db.add(invite)
        await self.db.flush()
        await self.db.refresh(invite)
        return invite

    async def get_org_invitations(self, org_id: uuid.UUID) -> list[Invitation]:
        result = await self.db.execute(
            select(Invitation).where(Invitation.organization_id == org_id)
        )
        return list(result.scalars().all())

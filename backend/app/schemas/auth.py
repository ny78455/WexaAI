import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from app.db.models.user import UserRole


# ── Organization ─────────────────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    name: str
    slug: str | None = None

    @field_validator("slug", mode="before")
    @classmethod
    def slugify(cls, v: str | None, info) -> str:
        if v:
            return v.lower().replace(" ", "-")
        name = info.data.get("name", "")
        return name.lower().replace(" ", "-").replace("_", "-")


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    organization_name: str  # Creates a new org on signup

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    organization_id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None


# ── Token ─────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Invitation ────────────────────────────────────────────────────────────────

class InviteCreate(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.ANALYST


class InviteAccept(BaseModel):
    token: str
    full_name: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class InviteOut(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    expires_at: datetime

    model_config = {"from_attributes": True}

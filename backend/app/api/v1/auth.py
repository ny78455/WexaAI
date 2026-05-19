from fastapi import APIRouter, Depends, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import CurrentUser, require_min_role
from app.db.models.user import UserRole
from app.services.auth import AuthService
from app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, RefreshRequest,
    UserOut, InviteCreate, InviteAccept, InviteOut,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(data: UserCreate, response: Response, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        user = await svc.signup(data)
    except IntegrityError:
        # Catch the duplicate email error gracefully
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    access_token, _ = await svc.login(UserLogin(email=data.email, password=data.password), response)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    access_token, user = await svc.login(data, response)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str | None = Cookie(default=None),
    body: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    token = refresh_token or (body.refresh_token if body else None)
    if not token:
        from app.core.exceptions import AuthenticationError
        raise AuthenticationError("Refresh token required")
    svc = AuthService(db)
    access_token, user = await svc.refresh_access_token(token)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser):
    return UserOut.model_validate(current_user)


@router.post("/invite", response_model=dict, status_code=201)
async def create_invite(
    data: InviteCreate,
    current_user = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    invite, invite_url = await svc.create_invite(current_user.organization_id, data, current_user.id)
    return {"id": str(invite.id), "invite_url": invite_url, "email": invite.email}


@router.post("/invite/accept", response_model=UserOut, status_code=201)
async def accept_invite(data: InviteAccept, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    user = await svc.accept_invite(data)
    return UserOut.model_validate(user)

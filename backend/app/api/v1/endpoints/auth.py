from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.security import decode_refresh_token, create_access_token, create_refresh_token
from app.models import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse, MeResponse, RefreshRequest
from app.services.auth import AuthService

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# In-memory token blacklist (Redis fallback)
_token_blacklist: set = set()


def _get_redis():
    """Get Redis connection for token blacklist. Returns None if unavailable."""
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None


def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    r = _get_redis()
    if r:
        return r.exists(f"blacklist:{token}") > 0
    return token in _token_blacklist


def blacklist_token(token: str, expire_seconds: int = 604800) -> None:
    """Add token to blacklist."""
    r = _get_redis()
    if r:
        r.setex(f"blacklist:{token}", expire_seconds, "1")
    else:
        _token_blacklist.add(token)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def signup(
    request: Request,
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    service = AuthService(db)
    try:
        user, access_token, refresh_token = await service.create_user(data)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SIGNUP_FAILED", "message": str(e)},
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return token."""
    service = AuthService(db)

    try:
        result = await service.authenticate(data.email, data.password)
    except ValueError as e:
        if str(e) == "ACCOUNT_SUSPENDED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ACCOUNT_SUSPENDED", "message": "Your account has been suspended due to repeated no-shows. Please contact support."},
            )
        raise

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    user, access_token, refresh_token = result
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    if is_token_blacklisted(data.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_BLACKLISTED", "message": "Token has been revoked"},
        )

    user_id = decode_refresh_token(data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"},
        )

    from sqlalchemy import select
    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User not found or inactive"},
        )

    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    # Blacklist old refresh token
    blacklist_token(data.refresh_token)

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    """Logout by blacklisting the current token."""
    # Get the token from the Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        blacklist_token(token)

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user info with profile names."""
    service = AuthService(db)
    profile_id = await service.get_user_profile_id(current_user)

    # Get profile names based on user role
    display_name = None
    business_name = None

    if current_user.role == "instructor":
        instructor_profile = await service.get_instructor_profile(current_user.id)
        if instructor_profile:
            display_name = instructor_profile.display_name
    elif current_user.role == "studio":
        studio_profile = await service.get_studio_profile(current_user.id)
        if studio_profile:
            business_name = studio_profile.business_name

    # Create UserResponse with profile names
    user_response = UserResponse.model_validate(current_user)
    user_response.display_name = display_name
    user_response.business_name = business_name

    return MeResponse(
        user=user_response,
        profile_id=profile_id,
    )

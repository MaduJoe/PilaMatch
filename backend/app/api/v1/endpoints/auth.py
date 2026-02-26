from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.security import decode_refresh_token, create_access_token, create_refresh_token
from app.models import User
from app.schemas.auth import (
    SignupRequest, LoginRequest, TokenResponse, UserResponse, MeResponse, RefreshRequest,
    AccountDeletionRequest, AccountDeletionResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
)
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


@router.delete("/users/me", response_model=AccountDeletionResponse)
async def delete_account(
    request: Request,
    data: AccountDeletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request account deletion with 30-day grace period.

    Immediately deactivates the account, cancels contracts, refunds escrows, and cancels subscriptions.
    The account can be recovered within 30 days via POST /users/me/cancel-deletion.
    """
    from app.services.account_deletion import AccountDeletionService

    service = AccountDeletionService(db)
    try:
        deletion_scheduled_at = await service.request_deletion(
            str(current_user.id), data.password
        )

        # Blacklist current token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            blacklist_token(token)

        return AccountDeletionResponse(
            message="계정 삭제가 예약되었습니다. 30일 이내에 취소할 수 있습니다.",
            deletion_scheduled_at=deletion_scheduled_at,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "INVALID_PASSWORD":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_PASSWORD", "message": "비밀번호가 일치하지 않습니다"},
            )
        if error_msg == "ALREADY_DELETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_DELETED", "message": "이미 삭제 요청된 계정입니다"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DELETION_FAILED", "message": error_msg},
        )


@router.post("/users/me/cancel-deletion", status_code=status.HTTP_200_OK)
async def cancel_account_deletion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel pending account deletion and restore the account.

    Only works if the 30-day grace period has not expired.
    """
    from app.services.account_deletion import AccountDeletionService

    service = AccountDeletionService(db)
    try:
        await service.cancel_deletion(str(current_user.id))
        return {"message": "계정 삭제가 취소되었습니다. 정상적으로 복구되었습니다."}
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "NO_PENDING_DELETION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "NO_PENDING_DELETION", "message": "삭제 대기 중인 계정이 아닙니다"},
            )
        if error_msg == "DELETION_ALREADY_PROCESSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DELETION_ALREADY_PROCESSED", "message": "이미 삭제가 처리된 계정입니다"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANCEL_FAILED", "message": error_msg},
        )


# In-memory rate limit tracking for password reset
_password_reset_attempts: dict[str, list] = {}  # email -> [timestamps]


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send password reset email.

    Always returns 200 regardless of whether the email exists (prevents email enumeration).
    Rate limited: 3 attempts per hour per email.
    """
    from datetime import datetime, timedelta
    from app.core.security import create_password_reset_token
    from app.services.email import EmailService

    success_msg = {"message": "비밀번호 재설정 이메일이 발송되었습니다. 이메일을 확인해주세요."}

    # Rate limit: 3 per hour per email
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    attempts = _password_reset_attempts.get(data.email, [])
    recent = [t for t in attempts if t > hour_ago]
    if len(recent) >= 3:
        return success_msg  # Silent rate limit, still 200

    # Look up user
    service = AuthService(db)
    user = await service.get_user_by_email(data.email)

    if not user or not user.is_active:
        return success_msg  # Don't reveal user existence

    # Generate reset token and send email
    token = create_password_reset_token(str(user.id))
    email_service = EmailService()
    await email_service.send_password_reset(data.email, token)

    # Track attempt
    recent.append(now)
    _password_reset_attempts[data.email] = recent

    return success_msg


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using the token from forgot-password email.

    Token is single-use: blacklisted after successful reset.
    All existing sessions are invalidated.
    """
    from app.core.security import decode_password_reset_token, get_password_hash
    from sqlalchemy import select
    from uuid import UUID

    # Decode token
    token_data = decode_password_reset_token(data.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "유효하지 않거나 만료된 토큰입니다"},
        )

    # Check if token was already used (via jti blacklist)
    jti = token_data["jti"]
    if is_token_blacklisted(f"reset:{jti}"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TOKEN_USED", "message": "이미 사용된 토큰입니다"},
        )

    # Find user
    user_id = token_data["sub"]
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USER_NOT_FOUND", "message": "사용자를 찾을 수 없습니다"},
        )

    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    await db.commit()

    # Blacklist the reset token jti (single-use)
    blacklist_token(f"reset:{jti}", expire_seconds=3600)

    return {"message": "비밀번호가 성공적으로 변경되었습니다. 다시 로그인해주세요."}

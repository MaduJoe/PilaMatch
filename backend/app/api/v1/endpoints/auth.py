from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse, MeResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    service = AuthService(db)
    try:
        user, token = await service.create_user(request)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SIGNUP_FAILED", "message": str(e)},
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return token."""
    service = AuthService(db)

    try:
        result = await service.authenticate(request.email, request.password)
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

    user, token = result
    return TokenResponse(access_token=token)


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

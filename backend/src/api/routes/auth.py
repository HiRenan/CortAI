"""
Authentication routes for user registration, login, and profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from src.database import get_db
from src.models.user import User
from src.schemas.auth import UserCreate, Token, UserResponse
from src.utils.security import verify_password, get_password_hash, create_access_token
from src.api.dependencies.auth import get_current_active_user
from src.core.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user

    Args:
        user_data: User registration data (email, password, name)
        db: Database session

    Returns:
        UserResponse with created user data

    Raises:
        HTTPException 400: If email is already registered
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )

    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        name=user_data.name
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password to get JWT token

    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session

    Returns:
        Token with access_token and token_type

    Raises:
        HTTPException 401: If credentials are invalid
    """
    # Read form or JSON body to support both content-types
    email = None
    password = None
    try:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")
    except Exception:
        pass
    if not email or not password:
        try:
            data = await request.json()
            email = data.get("email") or data.get("username")
            password = data.get("password")
        except Exception:
            email = None
            password = None
    if not email or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credenciais ausentes")

    # Find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        UserResponse with current user data
    """
    return current_user

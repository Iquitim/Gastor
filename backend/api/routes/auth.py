"""
Authentication Routes
=====================

Handles user registration, login, and profile management.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from email_validator import validate_email, EmailNotValidError
import re
from sqlalchemy.orm import Session

from core.database import get_db
from core import models
from core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_DAYS
)

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class UserRegister(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8, description="Must contain uppercase, lowercase, number and symbol")

    @field_validator("email")
    @classmethod
    def validate_email_deliverability(cls, v: str) -> str:
        try:
            # Check syntax and DNS deliverability
            email_info = validate_email(v, check_deliverability=True)
            return email_info.normalized
        except EmailNotValidError as e:
            # Translate common email validation errors
            msg = str(e)
            if "domain name" in msg and "does not accept email" in msg:
                 raise ValueError(f"O domínio {v.split('@')[1]} não aceita emails. Verifique se está correto.")
            if "does not appear to be deliverable" in msg:
                 raise ValueError("O email não parece ser entregável. Verifique o endereço.")
            if "The part after the @-sign is not valid" in msg:
                 raise ValueError("O domínio do email é inválido (falta o .com ou similar).")
            
            # Generic fallback for other validation errors
            raise ValueError("Email inválido. Verifique o endereço digitado.")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        import re
        errors = []
        if len(v) < 8:
            errors.append("A senha deve ter pelo menos 8 caracteres")
        if not re.search(r"[A-Z]", v):
            errors.append("A senha deve conter pelo menos uma letra maiúscula")
        if not re.search(r"[a-z]", v):
            errors.append("A senha deve conter pelo menos uma letra minúscula")
        if not re.search(r"\d", v):
            errors.append("A senha deve conter pelo menos um número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("A senha deve conter pelo menos um caractere especial")
        
        if errors:
            raise ValueError(". ".join(errors) + ".")
            
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: int
    username: str
    email: str
    telegram_chat_id: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    telegram_chat_id: Optional[str] = None
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None


# =============================================================================
# ROUTES
# =============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    """
    # Check if email already exists
    existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pw
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    Returns a JWT access token valid for 7 days.
    
    Note: Uses OAuth2PasswordRequestForm which expects 'username' field,
    but we use email as the identifier.
    """
    # Find user by email (form_data.username contains the email)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires a valid JWT token in the Authorization header.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    
    Can update:
    - username
    - telegram_chat_id
    - binance_api_key
    - binance_api_secret
    """
    # Check username uniqueness if being updated
    if user_update.username and user_update.username != current_user.username:
        existing = db.query(models.User).filter(models.User.username == user_update.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_update.username
    
    # Update optional fields
    if user_update.telegram_chat_id is not None:
        current_user.telegram_chat_id = user_update.telegram_chat_id
    
    if user_update.binance_api_key is not None:
        current_user.binance_api_key = user_update.binance_api_key
    
    if user_update.binance_api_secret is not None:
        current_user.binance_api_secret = user_update.binance_api_secret
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/logout")
async def logout(current_user: models.User = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: JWT tokens are stateless, so this endpoint is mainly for client-side
    cleanup confirmation. The client should discard the token.
    
    For true token invalidation, implement a token blacklist (future enhancement).
    """
    return {"message": "Successfully logged out", "detail": "Please discard your access token"}


# =============================================================================
# GOOGLE OAUTH
# =============================================================================

import os
import secrets
import httpx

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")


class GoogleTokenData(BaseModel):
    """Schema for Google OAuth token exchange."""
    code: str
    redirect_uri: Optional[str] = None


@router.get("/google/url")
async def get_google_auth_url():
    """
    Get the Google OAuth authorization URL.
    
    Frontend should redirect user to this URL to start OAuth flow.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
        "prompt": "select_account"
    }
    
    query = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    
    return {"url": auth_url, "state": state}


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(token_data: GoogleTokenData, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    
    Exchanges authorization code for tokens, fetches user info,
    and creates/links user account.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": token_data.code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": token_data.redirect_uri or GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code: {token_response.text}"
            )
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        
        # Get user info from Google
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        google_user = userinfo_response.json()
    
    google_id = google_user.get("id")
    email = google_user.get("email")
    name = google_user.get("name", email.split("@")[0])
    
    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google user data"
        )
    
    # Check if user exists by Google ID
    user = db.query(models.User).filter(models.User.google_id == google_id).first()
    
    if not user:
        # Check if user exists by email
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            db.commit()
        else:
            # Create new user
            # Generate unique username from name
            base_username = name.lower().replace(" ", "_")[:20]
            username = base_username
            counter = 1
            while db.query(models.User).filter(models.User.username == username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = models.User(
                email=email,
                username=username,
                google_id=google_id,
                hashed_password=None  # OAuth users don't have password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create JWT token
    jwt_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    )
    
    return TokenResponse(
        access_token=jwt_token,
        user=UserResponse.model_validate(user)
    )

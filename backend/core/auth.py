"""
Authentication Module
=====================

Handles password hashing, JWT token creation/verification, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from . import models

# =============================================================================
# CONFIGURATION
# =============================================================================

# Secret key for JWT - should be in .env in production
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "gastor-super-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# =============================================================================
# PASSWORD UTILITIES
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt has a 72-byte limit on passwords
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore'))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # bcrypt has a 72-byte limit on passwords
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes.decode('utf-8', errors='ignore'), hashed_password)


# =============================================================================
# JWT UTILITIES
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode (should include 'sub' with user identifier)
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Use this in route functions:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            ...
    
    Raises:
        HTTPException 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    Optional version - returns None instead of raising exception.
    Useful for routes that work with or without authentication.
    """
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

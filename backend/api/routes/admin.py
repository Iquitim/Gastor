"""
Admin Routes
============

Endpoints for system administration and user management.
Protected by `get_current_admin` dependency.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import psutil
import os

from core.database import get_db
from core import models
from core.auth import get_current_admin
from api.routes.live import active_engines

router = APIRouter()

# =============================================================================
# Schemas
# =============================================================================

class UserSummary(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: str
    active_sessions: int

    class Config:
        from_attributes = True

class SystemStats(BaseModel):
    cpu_usage: float
    ram_usage: float
    active_sessions: int
    active_users: int

class AdminConfigUpdate(BaseModel):
    max_users: int = Field(..., ge=1, description="Maximum allowed users")

# =============================================================================
# Routes
# =============================================================================

@router.get("/users", response_model=List[UserSummary])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """List all registered users with summary stats."""
    users = db.query(models.User).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # Count active sessions for this user
        # Note: This is a bit inefficient for large lists, but fine for admin view MVP
        active_sessions_count = db.query(models.PaperSession).filter(
            models.PaperSession.user_id == user.id,
            models.PaperSession.status == "running"
        ).count()
        
        result.append(UserSummary(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            active_sessions=active_sessions_count
        ))
        
    return result

@router.patch("/users/{user_id}/block")
async def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Block a user account."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.email} blocked successfully"}

@router.patch("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Unblock a user account."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = True
    db.commit()
    
    return {"message": f"User {user.email} unblocked successfully"}

@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Get real-time system resource usage."""
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # Active sessions from memory (most accurate for live load)
    # active_engines is imported from live.py
    active_sessions_count = len(active_engines)
    
    # Active users (users with at least one active session)
    active_user_ids = set()
    for session_id in active_engines:
        # We need to query DB to map session -> user if not in engine
        # But engine doesn't store user_id directly usually
        # Let's query DB for active sessions
        pass
    
    # Query DB for distinct users with running sessions
    active_users_count = db.query(models.PaperSession.user_id).filter(
        models.PaperSession.status == "running"
    ).distinct().count()
    
    return SystemStats(
        cpu_usage=cpu,
        ram_usage=ram,
        active_sessions=active_sessions_count,
        active_users=active_users_count
    )

@router.get("/system/config")
async def get_system_config(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Get global system configuration."""
    max_users_setting = db.query(models.SystemConfig).filter(
        models.SystemConfig.key == "MAX_USERS"
    ).first()
    
    max_users = int(max_users_setting.value) if max_users_setting else 12 # Default 12
    
    return {"max_users": max_users}

@router.post("/system/config")
async def update_system_config(
    config: AdminConfigUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """Update global system configuration."""
    max_users_setting = db.query(models.SystemConfig).filter(
        models.SystemConfig.key == "MAX_USERS"
    ).first()
    
    if not max_users_setting:
        max_users_setting = models.SystemConfig(
            key="MAX_USERS",
            value=str(config.max_users),
            description="Maximum number of registered users allowed"
        )
        db.add(max_users_setting)
    else:
        max_users_setting.value = str(config.max_users)
    
    db.commit()
    
    return {"message": "System configuration updated", "max_users": config.max_users}

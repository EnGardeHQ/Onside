from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import src.database as database_module
from src.auth.security import AuthService, get_current_user, create_access_token
from src.models.user import User, UserRole
from pydantic import BaseModel
from datetime import datetime

# Use the sync get_db from the parent database module
get_db = database_module.get_db

router = APIRouter(tags=["auth"])

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.email,  # Use email as username
        name=user_data.name,
        role=UserRole.USER
    )
    user.set_password(user_data.password)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role
    }

@router.post("/login", response_model=Dict[str, Any])
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return access token."""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not user.check_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }

@router.get("/me", response_model=Dict[str, Any])
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user's profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "created_at": current_user.created_at
    }

@router.post("/logout")
def logout_user(
    current_user: User = Depends(get_current_user)
):
    # In a stateless JWT system, client-side logout is sufficient
    # Server-side could implement token blacklisting if needed
    return {"message": "Successfully logged out"}

@router.get("/users/{user_id}", response_model=Dict[str, Any])
def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the requested user first
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Debug logging
    print(f"Current user ID: {current_user.id}, type: {type(current_user.id)}")
    print(f"Requested user ID: {user.id}, type: {type(user.id)}")
    print(f"Current user role: {current_user.role}")

    # Check if user has permission to view this profile
    if current_user.id != user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at
    }

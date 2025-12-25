"""API endpoints for User Preferences.

This module provides REST API endpoints for managing user preferences,
including language settings.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional

from src.database.config import get_db
from src.auth.security import get_current_user
from src.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users/me", tags=["user-preferences"])


class LanguagePreferenceResponse(BaseModel):
    """Schema for language preference response."""
    language: Optional[str]
    user_id: str

    class Config:
        orm_mode = True


class LanguagePreferenceUpdate(BaseModel):
    """Schema for updating language preference."""
    language: str = Field(..., min_length=2, max_length=5, description="Language code (e.g., 'en', 'es', 'fr')")


@router.get("/language", response_model=LanguagePreferenceResponse)
async def get_user_language(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's language preference.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        User's language preference
    """
    try:
        return {
            "language": current_user.language if hasattr(current_user, 'language') else None,
            "user_id": current_user.id
        }

    except Exception as e:
        logger.error(f"Error getting user language: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user language: {str(e)}"
        )


@router.put("/language", response_model=LanguagePreferenceResponse)
async def set_user_language(
    language_data: LanguagePreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set current user's language preference.

    Args:
        language_data: Language preference update
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated language preference
    """
    try:
        # Validate language code format
        language_code = language_data.language.lower()

        # Set language preference
        if hasattr(current_user, 'language'):
            current_user.language = language_code
            await db.commit()
            await db.refresh(current_user)

            logger.info(f"Updated language for user {current_user.id} to {language_code}")

            return {
                "language": current_user.language,
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language preference not supported in current user model"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting user language: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set user language: {str(e)}"
        )

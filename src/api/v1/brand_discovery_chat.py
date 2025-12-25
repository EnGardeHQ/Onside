"""API endpoints for Brand Discovery Chat interface.

This module provides REST API endpoints for the conversational AI brand
discovery process.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import logging

from src.database import get_db
from src.auth.security import get_current_user
from src.models.user import User
from src.services.ai.brand_discovery_chat import BrandDiscoveryChatService
from src.schemas.brand_discovery_chat import (
    ChatStartResponse,
    UserMessageRequest,
    ChatMessageResponse,
    ChatStatusResponse,
    FinalizeResponse,
    ExtractedData,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brand-discovery-chat", tags=["brand-discovery-chat"])


@router.post("/start", response_model=ChatStartResponse, status_code=status.HTTP_201_CREATED)
def start_chat_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new brand discovery chat session.

    Creates a new conversational session and returns the first AI message
    to begin the brand discovery process.

    Returns:
        ChatStartResponse with session_id and first AI message
    """
    try:
        service = BrandDiscoveryChatService(db)
        response = service.start_conversation(user_id=str(current_user.id))

        logger.info(f"User {current_user.id} started brand discovery chat: {response.session_id}")

        return response

    except Exception as e:
        logger.error(f"Error starting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start chat session: {str(e)}"
        )


@router.post("/{session_id}/message", response_model=ChatMessageResponse)
async def send_message(
    session_id: uuid.UUID,
    message_request: UserMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to the chat session.

    Processes the user's message, extracts relevant information,
    and generates a contextual AI response.

    Args:
        session_id: UUID of the chat session
        message_request: User's message

    Returns:
        ChatMessageResponse with AI response, progress, and extracted data

    Raises:
        HTTPException: If session not found or not active
    """
    try:
        service = BrandDiscoveryChatService(db)
        response = await service.send_message(
            session_id=session_id,
            user_message=message_request.message
        )

        logger.info(
            f"User {current_user.id} sent message to session {session_id}, "
            f"progress: {response.progress_pct}%"
        )

        return response

    except ValueError as e:
        logger.warning(f"Invalid session access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/{session_id}/status", response_model=ChatStatusResponse)
def get_session_status(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current status of a chat session.

    Returns the progress, extracted data, and missing fields
    for the specified session.

    Args:
        session_id: UUID of the chat session

    Returns:
        ChatStatusResponse with current state

    Raises:
        HTTPException: If session not found
    """
    try:
        service = BrandDiscoveryChatService(db)
        state = service.get_conversation_state(session_id=session_id)

        return ChatStatusResponse(
            session_id=state.session_id,
            progress_pct=state.progress_pct,
            extracted_data=state.extracted_data,
            missing_fields=state.missing_fields,
            is_complete=state.is_complete,
            status="active"  # Would come from session in real implementation
        )

    except ValueError as e:
        logger.warning(f"Session not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session status: {str(e)}"
        )


@router.post("/{session_id}/finalize", response_model=FinalizeResponse)
def finalize_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalize chat session and create brand analysis questionnaire.

    Validates that all required information has been collected and
    converts the conversation into a structured questionnaire ready
    for brand analysis.

    Args:
        session_id: UUID of the chat session

    Returns:
        FinalizeResponse with questionnaire and optional analysis job ID

    Raises:
        HTTPException: If required fields missing or session not found
    """
    try:
        service = BrandDiscoveryChatService(db)
        response = service.finalize_conversation(session_id=session_id)

        logger.info(
            f"User {current_user.id} finalized brand discovery chat: {session_id}, "
            f"brand: {response.questionnaire.brand_name}"
        )

        # TODO: Optionally auto-start brand analysis job here
        # from src.services.brand_analysis import BrandAnalysisService
        # analysis_service = BrandAnalysisService(db)
        # job = analysis_service.create_job(
        #     user_id=current_user.id,
        #     questionnaire=response.questionnaire.dict()
        # )
        # response.analysis_job_id = job.id

        return response

    except ValueError as e:
        logger.warning(f"Cannot finalize session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finalizing session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize session: {str(e)}"
        )


@router.get("/{session_id}/history")
def get_session_history(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full message history for a session.

    Useful for debugging or displaying conversation history in UI.

    Args:
        session_id: UUID of the chat session

    Returns:
        Dict with session info and message history

    Raises:
        HTTPException: If session not found
    """
    try:
        from src.models.brand_discovery_chat import BrandDiscoveryChatSession

        session = db.query(BrandDiscoveryChatSession).filter(
            BrandDiscoveryChatSession.session_id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return {
            "session_id": str(session.session_id),
            "user_id": session.user_id,
            "status": session.status,
            "messages": session.messages,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session history: {str(e)}"
        )

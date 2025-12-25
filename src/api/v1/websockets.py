"""
WebSocket Real-Time Progress Tracking for Brand Analysis

This module provides WebSocket endpoints for real-time progress updates
during brand analysis jobs. Features include:
- Real-time progress broadcasting to multiple clients
- Connection management and cleanup
- Heartbeat mechanism for connection health monitoring
- Structured progress messages with detailed status
- Automatic disconnection handling
- Job-specific progress channels
"""

import logging
import asyncio
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime
from collections import defaultdict
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.security import get_current_user_ws
from src.models.user import User
from src.models.brand_analysis import BrandAnalysisJob, AnalysisStatus
import src.database as database_module

logger = logging.getLogger(__name__)

# Use the sync get_db from the parent database module
get_db = database_module.get_db

router = APIRouter(prefix="/ws", tags=["websockets"])


class ConnectionManager:
    """
    Manages WebSocket connections for brand analysis progress updates.

    Features:
    - Multiple clients per job
    - Broadcast messages to all clients for a job
    - Automatic cleanup on disconnect
    - Heartbeat monitoring
    - Connection statistics
    """

    def __init__(self):
        """Initialize connection manager."""
        # job_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)

        # websocket -> job_id mapping for cleanup
        self.connection_jobs: Dict[WebSocket, str] = {}

        # websocket -> user_id mapping for auth
        self.connection_users: Dict[WebSocket, str] = {}

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        # Heartbeat tracking
        self.last_heartbeat: Dict[WebSocket, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        job_id: str,
        user_id: str
    ):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
            job_id: Brand analysis job ID
            user_id: User ID for authorization
        """
        await websocket.accept()

        self.active_connections[job_id].add(websocket)
        self.connection_jobs[websocket] = job_id
        self.connection_users[websocket] = user_id
        self.last_heartbeat[websocket] = datetime.utcnow()

        self.connection_metadata[websocket] = {
            "job_id": job_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "connection_id": str(uuid.uuid4())
        }

        logger.info(
            f"WebSocket connected: job_id={job_id}, user_id={user_id}, "
            f"total_connections={len(self.active_connections[job_id])}"
        )

    async def disconnect(self, websocket: WebSocket):
        """
        Remove and cleanup a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        job_id = self.connection_jobs.get(websocket)

        if job_id and websocket in self.active_connections[job_id]:
            self.active_connections[job_id].discard(websocket)

            # Cleanup empty job sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

        # Cleanup tracking dictionaries
        self.connection_jobs.pop(websocket, None)
        self.connection_users.pop(websocket, None)
        self.connection_metadata.pop(websocket, None)
        self.last_heartbeat.pop(websocket, None)

        logger.info(f"WebSocket disconnected: job_id={job_id}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            await self.disconnect(websocket)

    async def broadcast_to_job(self, job_id: str, message: Dict[str, Any]):
        """
        Broadcast a message to all connections for a specific job.

        Args:
            job_id: Brand analysis job ID
            message: Message dictionary to broadcast
        """
        if job_id not in self.active_connections:
            logger.debug(f"No active connections for job {job_id}")
            return

        disconnected = []

        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {str(e)}")
                disconnected.append(websocket)

        # Cleanup disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def send_heartbeat(self, websocket: WebSocket):
        """
        Send heartbeat to a specific connection.

        Args:
            websocket: Target WebSocket connection
        """
        await self.send_personal_message(
            {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
        self.last_heartbeat[websocket] = datetime.utcnow()

    def get_connection_count(self, job_id: str) -> int:
        """
        Get number of active connections for a job.

        Args:
            job_id: Brand analysis job ID

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(job_id, set()))

    def get_total_connections(self) -> int:
        """
        Get total number of active connections across all jobs.

        Returns:
            Total connection count
        """
        return sum(len(connections) for connections in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/brand-analysis/{job_id}")
async def websocket_brand_analysis_progress(
    websocket: WebSocket,
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time brand analysis progress updates.

    Clients connect to this endpoint to receive live updates about the
    progress of their brand analysis job.

    **Connection URL:** `/ws/brand-analysis/{job_id}`

    **Message Format (Server -> Client):**
    ```json
    {
        "type": "progress",
        "job_id": "uuid",
        "status": "crawling|analyzing|processing|completed|failed",
        "progress": 45,
        "current_step": "Analyzing SERP results...",
        "total_steps": 7,
        "completed_steps": 3,
        "estimated_time_remaining": 180,
        "timestamp": "2025-12-24T12:00:00Z"
    }
    ```

    **Message Types:**
    - `progress`: Regular progress update
    - `status_change`: Job status changed
    - `error`: Error occurred
    - `completed`: Job completed successfully
    - `heartbeat`: Connection health check

    Args:
        websocket: WebSocket connection
        job_id: Brand analysis job UUID
        db: Database session
    """
    # Note: In a production system, you would verify the user has access to this job
    # For now, we'll accept the connection and verify the job exists

    # Verify job exists
    job = db.query(BrandAnalysisJob).filter(BrandAnalysisJob.id == job_id).first()

    if not job:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Job not found")
        return

    # For now, use the job's user_id. In production, extract from JWT token
    user_id = job.user_id

    await manager.connect(websocket, job_id, user_id)

    # Send initial connection confirmation
    await manager.send_personal_message(
        {
            "type": "connected",
            "job_id": job_id,
            "status": job.status.value,
            "progress": job.progress,
            "message": "Connected to brand analysis progress stream",
            "timestamp": datetime.utcnow().isoformat()
        },
        websocket
    )

    try:
        # Heartbeat task
        async def heartbeat_loop():
            """Send periodic heartbeats to detect disconnected clients."""
            while True:
                try:
                    await asyncio.sleep(30)  # Heartbeat every 30 seconds
                    await manager.send_heartbeat(websocket)
                except Exception as e:
                    logger.error(f"Heartbeat error: {str(e)}")
                    break

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat_loop())

        # Listen for client messages (for potential client-initiated actions)
        while True:
            try:
                data = await websocket.receive_text()

                # Parse client message
                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    if message_type == "ping":
                        # Respond to ping with pong
                        await manager.send_personal_message(
                            {
                                "type": "pong",
                                "timestamp": datetime.utcnow().isoformat()
                            },
                            websocket
                        )
                    elif message_type == "get_status":
                        # Send current job status
                        db.refresh(job)
                        await manager.send_personal_message(
                            {
                                "type": "status",
                                "job_id": job_id,
                                "status": job.status.value,
                                "progress": job.progress,
                                "timestamp": datetime.utcnow().isoformat()
                            },
                            websocket
                        )
                    else:
                        logger.warning(f"Unknown message type: {message_type}")

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {data}")

            except WebSocketDisconnect:
                logger.info(f"Client disconnected from job {job_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break

    finally:
        # Cleanup
        heartbeat_task.cancel()
        await manager.disconnect(websocket)


# Helper functions for broadcasting progress updates

async def broadcast_progress(
    job_id: str,
    status: str,
    progress: int,
    current_step: str,
    total_steps: int = 7,
    completed_steps: int = 0,
    estimated_time_remaining: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Broadcast progress update to all clients listening to a job.

    Args:
        job_id: Brand analysis job UUID
        status: Current job status (crawling, analyzing, etc.)
        progress: Progress percentage (0-100)
        current_step: Description of current step
        total_steps: Total number of steps in the process
        completed_steps: Number of steps completed
        estimated_time_remaining: Estimated seconds until completion
        metadata: Additional metadata to include
    """
    message = {
        "type": "progress",
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "current_step": current_step,
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "estimated_time_remaining": estimated_time_remaining,
        "timestamp": datetime.utcnow().isoformat()
    }

    if metadata:
        message["metadata"] = metadata

    await manager.broadcast_to_job(job_id, message)


async def broadcast_status_change(
    job_id: str,
    old_status: str,
    new_status: str,
    message_text: Optional[str] = None
):
    """
    Broadcast status change notification.

    Args:
        job_id: Brand analysis job UUID
        old_status: Previous status
        new_status: New status
        message_text: Optional descriptive message
    """
    message = {
        "type": "status_change",
        "job_id": job_id,
        "old_status": old_status,
        "new_status": new_status,
        "message": message_text or f"Status changed from {old_status} to {new_status}",
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.broadcast_to_job(job_id, message)


async def broadcast_completion(
    job_id: str,
    success: bool,
    summary: Dict[str, Any]
):
    """
    Broadcast job completion notification.

    Args:
        job_id: Brand analysis job UUID
        success: Whether job completed successfully
        summary: Summary data (keywords found, competitors identified, etc.)
    """
    message = {
        "type": "completed" if success else "failed",
        "job_id": job_id,
        "success": success,
        "summary": summary,
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.broadcast_to_job(job_id, message)


async def broadcast_error(
    job_id: str,
    error_message: str,
    error_code: Optional[str] = None,
    recoverable: bool = False
):
    """
    Broadcast error notification.

    Args:
        job_id: Brand analysis job UUID
        error_message: Human-readable error message
        error_code: Optional error code
        recoverable: Whether the error is recoverable
    """
    message = {
        "type": "error",
        "job_id": job_id,
        "error": error_message,
        "error_code": error_code,
        "recoverable": recoverable,
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.broadcast_to_job(job_id, message)


async def broadcast_step_complete(
    job_id: str,
    step_name: str,
    step_number: int,
    total_steps: int,
    step_results: Optional[Dict[str, Any]] = None
):
    """
    Broadcast individual step completion.

    Args:
        job_id: Brand analysis job UUID
        step_name: Name of the completed step
        step_number: Step number (1-indexed)
        total_steps: Total number of steps
        step_results: Optional results from the step
    """
    message = {
        "type": "step_complete",
        "job_id": job_id,
        "step_name": step_name,
        "step_number": step_number,
        "total_steps": total_steps,
        "progress": int((step_number / total_steps) * 100),
        "step_results": step_results,
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.broadcast_to_job(job_id, message)


# Health check endpoint for WebSocket service
@router.get("/health")
async def websocket_health():
    """
    Health check endpoint for WebSocket service.

    Returns:
        Service health status and connection statistics
    """
    return {
        "status": "healthy",
        "active_jobs": len(manager.active_connections),
        "total_connections": manager.get_total_connections(),
        "timestamp": datetime.utcnow().isoformat()
    }

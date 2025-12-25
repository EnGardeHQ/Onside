"""
Job Manager Service for handling asynchronous background tasks
"""
from typing import Dict, Any, Optional, List, Callable
import asyncio
import uuid
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Enum for job status values"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Job:
    """Job class for tracking background tasks"""
    def __init__(self, job_id: str, job_type: str, params: Dict[str, Any] = None):
        self.id = job_id
        self.type = job_type
        self.params = params or {}
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.progress = 0
        self.task = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary representation"""
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "result": self.result,
            "error": self.error
        }

class JobManager:
    """Manager for handling background jobs"""
    _instance = None
    _jobs = {}
    _job_types = {}
    
    def __new__(cls):
        """Singleton pattern to ensure only one JobManager exists"""
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance.jobs = cls._jobs
            cls._instance.job_types = cls._job_types
        return cls._instance
    
    def register_job_type(self, job_type: str, handler: Callable):
        """Register a job type with its handler function"""
        self.job_types[job_type] = handler
    
    @classmethod
    def register_job_type_cls(cls, job_type: str, handler: Callable):
        """Static method to register a job type with its handler function"""
        cls._job_types[job_type] = handler
    
    async def create_job(self, job_type: str, params: Dict[str, Any] = None) -> str:
        """Create a new job and schedule it for execution"""
        if job_type not in self.job_types:
            raise ValueError(f"Unknown job type: {job_type}")
            
        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, job_type=job_type, params=params)
        self.jobs[job_id] = job
        
        # Schedule the job to run asynchronously
        job.task = asyncio.create_task(self._run_job(job))
        
        return job_id
        
    @classmethod
    async def create_job(cls, job_type: str, params: Dict[str, Any] = None) -> str:
        """Static method to create a new job and schedule it for execution"""
        instance = cls()
        return await instance.create_job(job_type, params)
    
    async def _run_job(self, job: Job):
        """Execute the job and handle its lifecycle"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            # Get the handler for this job type
            handler = self.job_types[job.type]
            
            # Execute the handler
            job.result = await handler(job)
            
            job.status = JobStatus.COMPLETED
            job.progress = 100
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            job.completed_at = datetime.now()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by its ID"""
        return self.jobs.get(job_id)
    
    @classmethod
    def get_job_cls(cls, job_id: str) -> Optional[Job]:
        """Static method to get a job by its ID"""
        return cls._jobs.get(job_id)
    
    def list_jobs(self, job_type: str = None, status: str = None) -> List[Job]:
        """List jobs with optional filtering by type and status"""
        jobs = list(self.jobs.values())
        
        if job_type:
            jobs = [job for job in jobs if job.type == job_type]
            
        if status:
            jobs = [job for job in jobs if job.status == status]
            
        return jobs
    
    @classmethod
    def list_jobs_cls(cls, job_type: str = None, status: str = None) -> List[Job]:
        """Static method to list jobs with optional filtering by type and status"""
        jobs = list(cls._jobs.values())
        
        if job_type:
            jobs = [job for job in jobs if job.type == job_type]
            
        if status:
            jobs = [job for job in jobs if job.status == status]
            
        return jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        if job.status == JobStatus.RUNNING and job.task:
            job.task.cancel()
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            return True
        
        return False
    
    @classmethod
    def cancel_job_cls(cls, job_id: str) -> bool:
        """Static method to cancel a running job"""
        instance = cls()
        return instance.cancel_job(job_id)

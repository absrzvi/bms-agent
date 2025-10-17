"""
Background Task Queue for Async Document Processing
Implements unlimited concurrent upload handling with queue-based processing
"""

import asyncio
import uuid
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from collections import OrderedDict

from .models.upload_status import UploadStatus, UploadJobStatus
from .processor_wrapper import get_processor

logger = logging.getLogger(__name__)


class UploadQueue:
    """
    Singleton upload queue manager
    Handles async document processing with status tracking
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.jobs: Dict[str, UploadJobStatus] = OrderedDict()
        self.max_jobs_history = 1000  # Keep last 1000 jobs in memory
        self.processing_lock = asyncio.Lock()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        
        logger.info("✅ Upload queue initialized")
    
    def start_worker(self):
        """Start the background worker task"""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("🚀 Background worker started")
    
    async def _worker(self):
        """Background worker that processes queued uploads"""
        logger.info("👷 Worker thread started")
        
        while True:
            try:
                # Get next job from queue
                job_id = await self.queue.get()
                
                if job_id not in self.jobs:
                    logger.warning(f"Job {job_id} not found in jobs dict")
                    self.queue.task_done()
                    continue
                
                job = self.jobs[job_id]
                
                # Update status to processing
                job.status = UploadStatus.PROCESSING
                job.started_at = datetime.now().isoformat()
                job.progress_percent = 10
                
                logger.info(f"🔄 Processing job {job_id}: {job.filename}")
                
                try:
                    # Get file path from job metadata
                    file_path = job.error_details.get("file_path") if job.error_details else None
                    profile = job.error_details.get("profile", "general") if job.error_details else "general"
                    
                    if not file_path:
                        raise ValueError("File path not found in job metadata")
                    
                    job.progress_percent = 30
                    
                    # Process document
                    processor = get_processor()
                    result = processor.process_document(str(file_path), profile)
                    
                    job.progress_percent = 90
                    
                    if result.status == "success":
                        # Update job with success result
                        job.status = UploadStatus.COMPLETED
                        job.document_id = result.document_id
                        job.chunks_created = result.chunks_created
                        job.quality_score = result.quality_score
                        job.processing_time_ms = result.processing_time_ms
                        job.replaced_existing = result.replaced_existing
                        job.deleted_chunks = result.deleted_chunks
                        job.completed_at = datetime.now().isoformat()
                        job.progress_percent = 100
                        
                        logger.info(f"✅ Job {job_id} completed successfully")
                    else:
                        # Processing failed
                        job.status = UploadStatus.FAILED
                        job.error = result.error or "Processing failed"
                        job.completed_at = datetime.now().isoformat()
                        job.progress_percent = 100
                        
                        logger.error(f"❌ Job {job_id} failed: {job.error}")
                
                except Exception as e:
                    # Handle processing errors
                    job.status = UploadStatus.FAILED
                    job.error = str(e)
                    job.error_details = {"exception": type(e).__name__, "message": str(e)}
                    job.completed_at = datetime.now().isoformat()
                    job.progress_percent = 100
                    
                    logger.error(f"❌ Job {job_id} failed with exception: {e}")
                
                finally:
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info("Worker task cancelled")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop
    
    async def submit_job(
        self,
        filename: str,
        file_path: Path,
        profile: str = "general"
    ) -> str:
        """
        Submit a new upload job to the queue
        
        Args:
            filename: Original filename
            file_path: Path to uploaded file
            profile: Processing profile
            
        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())
        
        # Create job status
        job = UploadJobStatus(
            job_id=job_id,
            filename=filename,
            status=UploadStatus.QUEUED,
            created_at=datetime.now().isoformat(),
            progress_percent=0,
            error_details={
                "file_path": str(file_path),
                "profile": profile
            }
        )
        
        # Add to jobs dict
        self.jobs[job_id] = job
        
        # Cleanup old jobs if needed
        if len(self.jobs) > self.max_jobs_history:
            # Remove oldest completed/failed jobs
            to_remove = []
            for jid, j in list(self.jobs.items()):
                if j.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                    to_remove.append(jid)
                    if len(to_remove) >= 100:  # Remove 100 at a time
                        break
            
            for jid in to_remove:
                del self.jobs[jid]
            
            logger.info(f"🧹 Cleaned up {len(to_remove)} old jobs")
        
        # Add to queue
        await self.queue.put(job_id)
        
        logger.info(f"📥 Job {job_id} queued: {filename}")
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[UploadJobStatus]:
        """Get status of a job by ID"""
        return self.jobs.get(job_id)
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        stats = {
            "total_jobs": len(self.jobs),
            "queued": sum(1 for j in self.jobs.values() if j.status == UploadStatus.QUEUED),
            "processing": sum(1 for j in self.jobs.values() if j.status == UploadStatus.PROCESSING),
            "completed": sum(1 for j in self.jobs.values() if j.status == UploadStatus.COMPLETED),
            "failed": sum(1 for j in self.jobs.values() if j.status == UploadStatus.FAILED),
            "queue_size": self.queue.qsize()
        }
        return stats


# Global queue instance
_queue = None


def get_upload_queue() -> UploadQueue:
    """Get the global upload queue instance"""
    global _queue
    if _queue is None:
        _queue = UploadQueue()
        _queue.start_worker()
    return _queue

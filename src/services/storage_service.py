"""
MinIO Object Storage Service

This service provides object storage functionality using MinIO:
- File upload/download
- Bucket management
- Presigned URL generation
- File versioning
"""
import logging
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import timedelta
from pathlib import Path
import io

from minio import Minio
from minio.error import S3Error
from minio.commonconfig import CopySource

from src.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO storage service for handling file operations."""

    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        """Ensure required buckets exist."""
        required_buckets = [
            "onside-screenshots",
            "onside-reports",
            "onside-scraped-content",
            "onside-exports",
            "onside-uploads"
        ]

        for bucket_name in required_buckets:
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created bucket: {bucket_name}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket_name}: {e}")

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: Optional[str] = None,
        file_data: Optional[BinaryIO] = None,
        length: Optional[int] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to MinIO.

        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object in the bucket
            file_path: Path to the file (if uploading from filesystem)
            file_data: File-like object (if uploading from memory)
            length: Length of the file data (required if file_data is provided)
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the object

        Returns:
            Dict containing upload metadata

        Raises:
            ValueError: If neither file_path nor file_data is provided
            S3Error: If upload fails
        """
        try:
            if file_path:
                # Upload from file path
                file_stat = Path(file_path).stat()
                with open(file_path, 'rb') as file_obj:
                    result = self.client.put_object(
                        bucket_name,
                        object_name,
                        file_obj,
                        file_stat.st_size,
                        content_type=content_type,
                        metadata=metadata
                    )
            elif file_data and length is not None:
                # Upload from file-like object
                result = self.client.put_object(
                    bucket_name,
                    object_name,
                    file_data,
                    length,
                    content_type=content_type,
                    metadata=metadata
                )
            else:
                raise ValueError("Either file_path or (file_data and length) must be provided")

            logger.info(f"Uploaded {object_name} to {bucket_name}")

            return {
                "bucket": bucket_name,
                "object_name": object_name,
                "etag": result.etag,
                "version_id": result.version_id,
                "size": length or file_stat.st_size if file_path else length,
                "content_type": content_type,
                "url": self.get_object_url(bucket_name, object_name)
            }

        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Download a file from MinIO.

        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object in the bucket
            file_path: Optional path to save the file

        Returns:
            File content as bytes if file_path is not provided, None otherwise

        Raises:
            S3Error: If download fails
        """
        try:
            if file_path:
                # Download to file
                self.client.fget_object(bucket_name, object_name, file_path)
                logger.info(f"Downloaded {object_name} to {file_path}")
                return None
            else:
                # Download to memory
                response = self.client.get_object(bucket_name, object_name)
                data = response.read()
                response.close()
                response.release_conn()
                logger.info(f"Downloaded {object_name} to memory")
                return data

        except S3Error as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            raise

    def delete_file(
        self,
        bucket_name: str,
        object_name: str,
        version_id: Optional[str] = None
    ) -> bool:
        """
        Delete a file from MinIO.

        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object to delete
            version_id: Optional version ID to delete specific version

        Returns:
            True if deletion was successful

        Raises:
            S3Error: If deletion fails
        """
        try:
            self.client.remove_object(bucket_name, object_name, version_id=version_id)
            logger.info(f"Deleted {object_name} from {bucket_name}")
            return True

        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {e}")
            raise

    def list_files(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List files in a bucket.

        Args:
            bucket_name: Name of the bucket
            prefix: Optional prefix to filter objects
            recursive: Whether to list recursively

        Returns:
            List of file metadata dictionaries

        Raises:
            S3Error: If listing fails
        """
        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=recursive
            )

            files = []
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "etag": obj.etag,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "content_type": obj.content_type,
                    "version_id": obj.version_id
                })

            logger.info(f"Listed {len(files)} files from {bucket_name}")
            return files

        except S3Error as e:
            logger.error(f"Error listing files from MinIO: {e}")
            raise

    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate a presigned URL for temporary access to an object.

        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            expires: Expiration time for the URL

        Returns:
            Presigned URL string

        Raises:
            S3Error: If URL generation fails
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=expires
            )
            logger.info(f"Generated presigned URL for {object_name}")
            return url

        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise

    def get_object_url(
        self,
        bucket_name: str,
        object_name: str
    ) -> str:
        """
        Get the URL for an object (public or internal).

        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object

        Returns:
            Object URL string
        """
        endpoint = settings.MINIO_ENDPOINT
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{endpoint}/{bucket_name}/{object_name}"

    def copy_file(
        self,
        source_bucket: str,
        source_object: str,
        dest_bucket: str,
        dest_object: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Copy a file within MinIO.

        Args:
            source_bucket: Source bucket name
            source_object: Source object name
            dest_bucket: Destination bucket name
            dest_object: Destination object name
            metadata: Optional metadata for the destination object

        Returns:
            Dict containing copy result metadata

        Raises:
            S3Error: If copy fails
        """
        try:
            copy_source = CopySource(source_bucket, source_object)
            result = self.client.copy_object(
                dest_bucket,
                dest_object,
                copy_source,
                metadata=metadata
            )

            logger.info(f"Copied {source_bucket}/{source_object} to {dest_bucket}/{dest_object}")

            return {
                "source_bucket": source_bucket,
                "source_object": source_object,
                "dest_bucket": dest_bucket,
                "dest_object": dest_object,
                "etag": result.etag,
                "version_id": result.version_id
            }

        except S3Error as e:
            logger.error(f"Error copying file in MinIO: {e}")
            raise

    def file_exists(
        self,
        bucket_name: str,
        object_name: str
    ) -> bool:
        """
        Check if a file exists in MinIO.

        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False

    def get_file_metadata(
        self,
        bucket_name: str,
        object_name: str
    ) -> Dict[str, Any]:
        """
        Get metadata for a file.

        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object

        Returns:
            Dict containing file metadata

        Raises:
            S3Error: If file doesn't exist or operation fails
        """
        try:
            stat = self.client.stat_object(bucket_name, object_name)

            return {
                "name": object_name,
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "content_type": stat.content_type,
                "version_id": stat.version_id,
                "metadata": stat.metadata
            }

        except S3Error as e:
            logger.error(f"Error getting file metadata from MinIO: {e}")
            raise


# Lazy-load singleton instance to avoid connecting to MinIO at import time
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    Get or create the singleton StorageService instance.
    
    This lazy-loads the service to avoid connecting to MinIO during module import,
    which would cause startup failures if MinIO is not available.
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


# For backward compatibility
def __getattr__(name):
    """Allow module-level access to storage_service for backward compatibility."""
    if name == "storage_service":
        return get_storage_service()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

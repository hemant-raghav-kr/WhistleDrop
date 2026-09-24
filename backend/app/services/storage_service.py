"""Object storage service abstraction supporting Supabase Storage with local dev fallback.

Design & Security Guarantees:
- Decoupled provider abstraction: rest of app calls `get_storage_service()`.
- Uploaded evidence is stored in a PRIVATE bucket; never publicly readable.
- Generates unpredictable, non-sequential storage keys:
    `reports/{report_id}/evidence/{uuid4_hex}_{clean_filename}`
- Short-lived signed URLs (default 300s) generated exclusively for authenticated moderators.
- Automatic cleanup of storage objects upon failed database transactions.
"""

import os
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("whistledrop.storage")


class StorageException(Exception):
    """Raised when an object storage operation fails."""
    pass


class BaseStorageProvider(ABC):
    """Abstract storage interface."""

    @abstractmethod
    def upload_file(self, storage_key: str, file_bytes: bytes, mime_type: str) -> None:
        pass

    @abstractmethod
    def generate_signed_url(self, storage_key: str, expires_in: int = 300) -> str:
        pass

    @abstractmethod
    def get_file_bytes(self, storage_key: str) -> bytes:
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        pass


class SupabaseStorageProvider(BaseStorageProvider):
    """Production storage provider communicating with Supabase Storage REST API."""

    def __init__(self, supabase_url: str, service_role_key: str, bucket: str):
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket = bucket
        self.headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apiKey": self.service_role_key,
        }

    def _object_url(self, storage_key: str) -> str:
        return f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_key}"

    def upload_file(self, storage_key: str, file_bytes: bytes, mime_type: str) -> None:
        url = self._object_url(storage_key)
        headers = {
            **self.headers,
            "Content-Type": mime_type,
            "x-upsert": "false",
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, content=file_bytes, headers=headers)
                if res.status_code not in (200, 201):
                    logger.error("Supabase Storage upload error: %s - %s", res.status_code, res.text)
                    raise StorageException(f"Failed to upload evidence to storage: {res.text}")
        except httpx.RequestError as e:
            logger.error("Network error communicating with Supabase Storage: %s", e)
            raise StorageException("Storage provider connection error.")

    def generate_signed_url(self, storage_key: str, expires_in: int = 300) -> str:
        url = f"{self.supabase_url}/storage/v1/object/sign/{self.bucket}/{storage_key}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json={"expiresIn": expires_in}, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    signed_path = data.get("signedURL")
                    if signed_path:
                        return f"{self.supabase_url}/storage/v1{signed_path}"
                raise StorageException(f"Failed to generate signed URL: {res.text}")
        except httpx.RequestError as e:
            logger.error("Network error signing URL with Supabase Storage: %s", e)
            raise StorageException("Storage provider signing error.")

    def get_file_bytes(self, storage_key: str) -> bytes:
        url = f"{self.supabase_url}/storage/v1/object/authenticated/{self.bucket}/{storage_key}"
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.get(url, headers=self.headers)
                if res.status_code == 200:
                    return res.content
                raise StorageException(f"Failed to fetch evidence from storage: {res.status_code}")
        except httpx.RequestError as e:
            logger.error("Network error downloading from Supabase Storage: %s", e)
            raise StorageException("Storage provider download error.")

    def delete_file(self, storage_key: str) -> bool:
        url = self._object_url(storage_key)
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.delete(url, headers=self.headers)
                return res.status_code in (200, 204, 404)
        except Exception as e:
            logger.warning("Error deleting object from Supabase Storage: %s", e)
            return False


class LocalStorageProvider(BaseStorageProvider):
    """Local fallback storage provider for development and automated testing environments."""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, storage_key: str) -> str:
        safe_key = storage_key.replace("/", os.sep)
        full_path = os.path.abspath(os.path.join(self.base_dir, safe_key))
        if not full_path.startswith(self.base_dir):
            raise StorageException("Path traversal detected.")
        return full_path

    def upload_file(self, storage_key: str, file_bytes: bytes, mime_type: str) -> None:
        target_path = self._resolve_path(storage_key)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(file_bytes)

    def generate_signed_url(self, storage_key: str, expires_in: int = 300) -> str:
        # In local fallback mode, points to the authenticated stream endpoint
        return f"/api/v1/moderator/evidence/stream/{storage_key}?expires={expires_in}"

    def get_file_bytes(self, storage_key: str) -> bytes:
        target_path = self._resolve_path(storage_key)
        if not os.path.exists(target_path):
            raise StorageException("File not found in local storage.")
        with open(target_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_key: str) -> bool:
        try:
            target_path = self._resolve_path(storage_key)
            if os.path.exists(target_path):
                os.remove(target_path)
            return True
        except Exception:
            return False


class StorageService:
    """Unified service providing storage operations with unpredictable key generation."""

    def __init__(self, provider: BaseStorageProvider):
        self.provider = provider

    @staticmethod
    def generate_storage_key(report_id: uuid.UUID, clean_filename: str) -> str:
        """Generate an unpredictable, non-sequential storage key with no path traversal."""
        random_prefix = uuid.uuid4().hex[:16]
        return f"reports/{report_id}/evidence/{random_prefix}_{clean_filename}"

    def upload_file(self, storage_key: str, file_bytes: bytes, mime_type: str) -> None:
        self.provider.upload_file(storage_key=storage_key, file_bytes=file_bytes, mime_type=mime_type)

    def generate_signed_url(self, storage_key: str, expires_in: int = 300) -> str:
        return self.provider.generate_signed_url(storage_key=storage_key, expires_in=expires_in)

    def get_file_bytes(self, storage_key: str) -> bytes:
        return self.provider.get_file_bytes(storage_key=storage_key)

    def delete_file(self, storage_key: str) -> bool:
        return self.provider.delete_file(storage_key=storage_key)


_storage_service_instance: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Factory creating or returning the configured StorageService singleton."""
    global _storage_service_instance
    if _storage_service_instance is None:
        target_provider = settings.STORAGE_PROVIDER.lower().strip()
        use_supabase = False

        if target_provider == "supabase":
            use_supabase = True
        elif target_provider == "local":
            use_supabase = False
        else:  # "auto"
            use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)

        if use_supabase:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
                raise StorageException(
                    "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required when using Supabase storage."
                )
            provider = SupabaseStorageProvider(
                supabase_url=settings.SUPABASE_URL,
                service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY,
                bucket=settings.SUPABASE_STORAGE_BUCKET,
            )
            logger.info("Configured SupabaseStorageProvider for private bucket: %s", settings.SUPABASE_STORAGE_BUCKET)
        else:
            provider = LocalStorageProvider(base_dir=settings.STORAGE_LOCAL_FALLBACK_DIR)
            logger.info("Configured LocalStorageProvider in: %s", settings.STORAGE_LOCAL_FALLBACK_DIR)
        _storage_service_instance = StorageService(provider=provider)
    return _storage_service_instance

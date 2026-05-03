from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import logging, uuid
from datetime import timedelta

logger = logging.getLogger(__name__)

_client: Minio = None


def get_minio() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,
        )
    return _client


def upload_file(file_data: bytes, filename: str, content_type: str) -> str:
    """Upload file to MinIO, return object key."""
    client = get_minio()
    object_key = f"{uuid.uuid4()}/{filename}"
    import io
    client.put_object(
        settings.MINIO_BUCKET_ATTACHMENTS,
        object_key,
        io.BytesIO(file_data),
        len(file_data),
        content_type=content_type,
    )
    logger.info(f"[STORAGE] Uploaded {object_key}")
    return object_key


def get_presigned_url(object_key: str, expires_hours: int = 1) -> str:
    """Generate a presigned download URL."""
    client = get_minio()
    url = client.presigned_get_object(
        settings.MINIO_BUCKET_ATTACHMENTS,
        object_key,
        expires=timedelta(hours=expires_hours),
    )
    return url

"""
Creates MinIO buckets.
Usage: make init-minio
"""
from minio import Minio
from app.core.config import settings


def init_buckets():
    client = Minio(
        f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=False,
    )
    for bucket in [settings.MINIO_BUCKET_ATTACHMENTS, "ml-models", "exports"]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"✅ Created bucket: {bucket}")
        else:
            print(f"ℹ️  Bucket exists: {bucket}")


if __name__ == "__main__":
    init_buckets()

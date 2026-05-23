"""S3-compatible storage service for image uploads."""

import uuid
from typing import Optional

import boto3
from botocore.config import Config

from app.config import settings

_s3_client = None


def get_s3_client():
    """Get or create the S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
        )
    return _s3_client


async def upload_file(
    content: bytes,
    filename: str,
    content_type: str,
    user_id: str,
) -> tuple[str, str]:
    """
    Upload a file to S3 storage.
    Returns (full_url, thumbnail_url).
    For simplicity, the thumbnail is the same as the full image
    (a production system would generate actual thumbnails).
    """
    # Generate unique key
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "png"
    key = f"uploads/{user_id}/{uuid.uuid4().hex}.{ext}"

    client = get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=content,
        ContentType=content_type,
    )

    # Construct public URL
    if settings.s3_public_url:
        base_url = settings.s3_public_url.rstrip("/")
    else:
        base_url = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}"

    full_url = f"{base_url}/{key}"
    thumbnail_url = full_url  # Same URL for now; production would use resized version

    return full_url, thumbnail_url


async def generate_presigned_upload_url(
    filename: str, content_type: str, user_id: str
) -> dict[str, str]:
    """
    Generate a presigned URL for direct browser upload to S3.
    Returns the upload URL and the eventual public URL.
    """
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "png"
    key = f"uploads/{user_id}/{uuid.uuid4().hex}.{ext}"

    client = get_s3_client()
    presigned_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=3600,
    )

    if settings.s3_public_url:
        public_url = f"{settings.s3_public_url.rstrip('/')}/{key}"
    else:
        public_url = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{key}"

    return {"upload_url": presigned_url, "public_url": public_url, "key": key}

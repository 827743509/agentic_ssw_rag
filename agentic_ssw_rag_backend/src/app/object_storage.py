from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from app.config import get_settings


@lru_cache(maxsize=1)
def get_minio_client() -> Minio:
    settings = get_settings()
    parsed = urlparse(settings.minio_endpoint)
    if parsed.scheme:
        endpoint = parsed.netloc
        secure = parsed.scheme == "https"
    else:
        endpoint = settings.minio_endpoint
        secure = False

    if settings.minio_secure is not None:
        secure = settings.minio_secure

    return Minio(
        endpoint=endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )


def ensure_bucket() -> None:
    settings = get_settings()
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_file_object(
    file_path: Path,
    object_name: str,
    content_type: str | None = None,
) -> None:
    settings = get_settings()
    ensure_bucket()
    get_minio_client().fput_object(
        bucket_name=settings.minio_bucket,
        object_name=object_name,
        file_path=str(file_path),
        content_type=content_type or "application/octet-stream",
    )


def delete_file_object(object_name: str) -> bool:
    settings = get_settings()
    client = get_minio_client()
    try:
        client.remove_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        if exc.code in {"NoSuchBucket", "NoSuchKey", "NoSuchObject"}:
            return False
        raise
    return True


def file_object_exists(object_name: str) -> bool:
    settings = get_settings()
    client = get_minio_client()
    try:
        client.stat_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        if exc.code in {"NoSuchBucket", "NoSuchKey", "NoSuchObject"}:
            return False
        raise
    return True


def stream_file_object(object_name: str, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    settings = get_settings()
    response = get_minio_client().get_object(settings.minio_bucket, object_name)
    try:
        yield from response.stream(chunk_size)
    finally:
        response.close()
        response.release_conn()

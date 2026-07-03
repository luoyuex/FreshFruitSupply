from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp'}
UPLOAD_PREFIX = '/uploads/'


def to_storage_path(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith(UPLOAD_PREFIX):
        return url
    marker = UPLOAD_PREFIX
    if marker in url:
        return marker + url.split(marker, 1)[1]
    return url


def to_storage_paths(urls: list[str] | None) -> list[str]:
    return [path for url in (urls or []) if (path := to_storage_path(url))]


def to_public_url(path: str | None) -> str | None:
    if not path:
        return None
    storage_path = to_storage_path(path)
    if not storage_path:
        return None
    if not storage_path.startswith(UPLOAD_PREFIX):
        return storage_path
    return f'{settings.public_base_url.rstrip("/")}{storage_path}'


def to_public_urls(paths: list[str] | None) -> list[str]:
    return [url for path in (paths or []) if (url := to_public_url(path))]


async def save_upload(file: UploadFile, subdir: str) -> str:
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        suffix = '.jpg'

    target_dir = settings.upload_root / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f'{uuid4().hex}{suffix}'
    target = target_dir / filename

    with target.open('wb') as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    return f'/uploads/{subdir}/{filename}'

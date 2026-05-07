from pathlib import Path

from fastapi import HTTPException, UploadFile, status

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
UPLOAD_READ_CHUNK_BYTES = 1024 * 1024


async def save_upload_file(file: UploadFile, target_path: Path) -> int:
    total = 0
    with target_path.open("wb") as handle:
        while True:
            chunk = await file.read(UPLOAD_READ_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Upload is too large. Maximum size is 50MB.",
                )
            handle.write(chunk)
    return total


def matches_declared_type(path: Path, mime_type: str) -> bool:
    with path.open("rb") as handle:
        header = handle.read(8)
    if mime_type == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if mime_type == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")
    if mime_type == "application/pdf":
        return header.startswith(b"%PDF-")
    return False


def discard_upload(path: Path) -> None:
    path.unlink(missing_ok=True)

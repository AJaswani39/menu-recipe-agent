import logging

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status

from app.auth import AuthUser, enforce_rate_limit, get_upload_rate_limit_per_minute, require_user
from app.history import create_history_record, get_user_stored_bytes, stored_upload_path
from app.upload_extractor import SUPPORTED_MIME_TYPES, extract_menu_from_upload
from app.uploads import discard_upload, matches_declared_type, save_upload_file

logger = logging.getLogger(__name__)


def register(api: FastAPI) -> None:
    @api.post("/uploads/menu")
    async def upload_menu(
        file: UploadFile = File(...),
        restaurant_name: str | None = Form(default=None),
        user: AuthUser = Depends(require_user),
    ):
        enforce_rate_limit(user, "upload", get_upload_rate_limit_per_minute())
        mime_type = file.content_type or "application/octet-stream"
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Upload a PNG, JPEG, or PDF menu.",
            )

        target_path = stored_upload_path(file.filename or "menu-upload")
        try:
            stored_bytes = await save_upload_file(file, target_path)
            if not matches_declared_type(target_path, mime_type):
                raise ValueError("Uploaded file contents do not match the declared file type")
            if get_user_stored_bytes(user.id) + stored_bytes > user.storage_quota_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Upload storage quota exceeded. Delete older history before uploading.",
                )
            menu_response = await extract_menu_from_upload(
                file_path=target_path,
                mime_type=mime_type,
                restaurant_name=restaurant_name,
            )
            history = create_history_record(
                owner_user_id=user.id,
                source_type="upload",
                restaurant=menu_response.restaurant,
                source_label=file.filename or target_path.name,
                file_name=file.filename,
                mime_type=mime_type,
                file_path=str(target_path),
                stored_bytes=stored_bytes,
                menu=menu_response,
            )
            return {"history": history, "menu": menu_response}
        except HTTPException:
            discard_upload(target_path)
            raise
        except Exception as exc:  # pragma: no cover
            discard_upload(target_path)
            logger.exception("Upload extraction failed")
            raise HTTPException(status_code=400, detail="Upload extraction failed") from exc

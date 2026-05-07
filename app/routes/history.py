from fastapi import Depends, FastAPI, HTTPException

from app.auth import AuthUser, require_user
from app.history import delete_history_record, get_history_record, list_history


def register(api: FastAPI) -> None:
    @api.get("/history")
    async def history_list(user: AuthUser = Depends(require_user)):
        return {"items": list_history(user.id)}

    @api.get("/history/{history_id}")
    async def history_detail(history_id: str, user: AuthUser = Depends(require_user)):
        record = get_history_record(user.id, history_id)
        if not record:
            raise HTTPException(status_code=404, detail="History record not found")
        return record

    @api.delete("/history/{history_id}")
    async def history_delete(history_id: str, user: AuthUser = Depends(require_user)):
        if not delete_history_record(user.id, history_id):
            raise HTTPException(status_code=404, detail="History record not found")
        return {"deleted": True}

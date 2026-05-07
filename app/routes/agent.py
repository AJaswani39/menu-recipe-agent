import logging

from fastapi import Depends, FastAPI, HTTPException, Query

from app.agent import fetch_menu_then_recipe, run_agent_request
from app.auth import AuthUser, enforce_rate_limit, get_recipe_rate_limit_per_minute, require_user
from app.models import AgentRunRequest

logger = logging.getLogger(__name__)


def register(api: FastAPI) -> None:
    @api.get("/agent/run")
    async def run_agent(
        restaurant_url: str = Query(..., description="Restaurant menu URL"),
        dish_name: str = Query(..., min_length=1, max_length=120),
        user: AuthUser = Depends(require_user),
    ):
        enforce_rate_limit(user, "recipe", get_recipe_rate_limit_per_minute())
        try:
            menu_response, recipe_response = await fetch_menu_then_recipe(restaurant_url, dish_name)
            return {"menu": menu_response, "recipe": recipe_response}
        except Exception as exc:  # pragma: no cover
            logger.exception("Agent run failed")
            raise HTTPException(status_code=400, detail="Agent run failed") from exc

    @api.post("/agent/run")
    async def run_agent_post(request: AgentRunRequest, user: AuthUser = Depends(require_user)):
        enforce_rate_limit(user, "recipe", get_recipe_rate_limit_per_minute())
        try:
            menu_response, recipe_response = await run_agent_request(request, user.id)
            return {"menu": menu_response, "recipe": recipe_response}
        except Exception as exc:  # pragma: no cover
            logger.exception("Agent run failed")
            raise HTTPException(status_code=400, detail="Agent run failed") from exc

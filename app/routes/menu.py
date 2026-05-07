import logging

from fastapi import Depends, FastAPI, HTTPException, Query

from app.auth import AuthUser, enforce_rate_limit, get_recipe_rate_limit_per_minute, require_user
from app.models import DishSelectionRequest
from app.recipe import get_recipe
from app.scraper import scrape_menu

logger = logging.getLogger(__name__)


def register(api: FastAPI) -> None:
    @api.get("/menu")
    async def menu(
        restaurant_url: str = Query(..., description="Restaurant menu URL"),
        user: AuthUser = Depends(require_user),
    ):
        enforce_rate_limit(user, "recipe", get_recipe_rate_limit_per_minute())
        try:
            return await scrape_menu(restaurant_url)
        except Exception as exc:  # pragma: no cover
            logger.exception("Menu scrape failed")
            raise HTTPException(status_code=400, detail="Menu scrape failed") from exc

    @api.post("/recipe")
    async def recipe(selection: DishSelectionRequest, user: AuthUser = Depends(require_user)):
        enforce_rate_limit(user, "recipe", get_recipe_rate_limit_per_minute())
        return await get_recipe(selection)

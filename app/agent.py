from app.models import AgentRunRequest, DishSelectionRequest, MenuScrapeResponse, RecipeResponse
from app.history import get_history_record, update_history_recipe
from app.recipe import get_recipe
from app.scraper import scrape_menu


async def fetch_menu_then_recipe(
    restaurant_url: str, dish_name: str
) -> tuple[MenuScrapeResponse, RecipeResponse]:
    menu = await scrape_menu(restaurant_url)
    matched = _find_menu_item(menu, dish_name)
    recipe = await get_recipe(
        DishSelectionRequest(
            dish_name=matched.name if matched else dish_name,
            restaurant_name=menu.restaurant,
            menu_description=matched.description if matched else None,
            category=matched.category if matched else None,
            price=matched.price if matched else None,
            source_url=matched.url if matched else restaurant_url,
        )
    )
    return menu, recipe


async def run_agent_request(
    request: AgentRunRequest, owner_user_id: int
) -> tuple[MenuScrapeResponse, RecipeResponse]:
    history_record = (
        get_history_record(owner_user_id, request.history_id)
        if request.history_id
        else None
    )
    menu = await _resolve_menu(request, history_record)
    selected = request.selected_item or _find_menu_item(menu, request.dish_name)
    recipe = await get_recipe(
        DishSelectionRequest(
            dish_name=selected.name if selected else request.dish_name,
            restaurant_name=menu.restaurant,
            menu_description=(
                selected.description if selected else request.menu_description
            ),
            category=selected.category if selected else request.category,
            price=selected.price if selected else request.price,
            source_url=selected.url if selected else request.restaurant_url,
            servings=request.servings,
            dietary_preference=request.dietary_preference,
            spice_level=request.spice_level,
            equipment=request.equipment,
            time_limit_minutes=request.time_limit_minutes,
        )
    )
    if request.history_id:
        update_history_recipe(owner_user_id, request.history_id, recipe)
    return menu, recipe


async def _resolve_menu(request: AgentRunRequest, history_record) -> MenuScrapeResponse:
    if history_record and history_record.menu:
        return history_record.menu
    if request.menu:
        return request.menu
    if request.selected_item:
        return MenuScrapeResponse(
            restaurant="Selected menu item",
            source_url=request.restaurant_url,
            menu_items=[request.selected_item],
        )
    return await scrape_menu(request.restaurant_url)


def _find_menu_item(menu: MenuScrapeResponse, dish_name: str):
    target = dish_name.strip().lower()
    for item in menu.menu_items:
        if item.name.strip().lower() == target:
            return item
    for item in menu.menu_items:
        if target in item.name.strip().lower():
            return item
    return None

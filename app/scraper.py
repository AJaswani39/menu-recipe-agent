from app.menu_parser import (
    clean_text as _clean_text,
    extract_item_from_node as _extract_item_from_node,
    extract_menu_items as _extract_menu_items,
    extract_price as _extract_price,
    first_matching_text as _first_matching_text,
    menu_item_id as _menu_item_id,
    remove_price as _remove_price,
    looks_like_menu_item as _looks_like_menu_item,
    category_for_node as _category_for_node,
)
from app.models import MenuScrapeResponse
from app.scrape_fetcher import fetch_menu_page, timeout_from_env as _timeout_from_env
from app.scrape_security import (
    reject_private_destination as _reject_private_destination,
    validate_scrape_url as _validate_scrape_url,
)


async def scrape_menu(restaurant_url: str) -> MenuScrapeResponse:
    page = await fetch_menu_page(restaurant_url)
    from app.menu_parser import parse_menu_html

    return parse_menu_html(page.html, page.requested_url, page.host)

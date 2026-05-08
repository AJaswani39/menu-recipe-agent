from app.menu_parser import parse_menu_html
from app.models import MenuScrapeResponse
from app.scrape_fetcher import fetch_menu_page


async def scrape_menu(restaurant_url: str) -> MenuScrapeResponse:
    page = await fetch_menu_page(restaurant_url)
    return parse_menu_html(page.html, page.requested_url, page.host)

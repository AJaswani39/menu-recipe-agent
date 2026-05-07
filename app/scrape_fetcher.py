import os
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx

from app.scrape_security import validate_scrape_url

DEFAULT_SCRAPER_TIMEOUT_SECONDS = 8.0
MAX_REDIRECTS = 5


@dataclass(frozen=True)
class FetchedMenuPage:
    requested_url: str
    final_url: str
    html: str
    host: str


async def fetch_menu_page(restaurant_url: str) -> FetchedMenuPage:
    parsed = validate_scrape_url(restaurant_url)
    current_url = restaurant_url

    async with httpx.AsyncClient(
        timeout=timeout_from_env("SCRAPER_TIMEOUT_SECONDS", DEFAULT_SCRAPER_TIMEOUT_SECONDS),
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            validate_scrape_url(current_url)
            response = await client.get(current_url, follow_redirects=False)
            if not response.is_redirect:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    raise ValueError("URL did not return an HTML page")
                break
            location = response.headers.get("location")
            if not location:
                raise ValueError("Redirect response did not include a Location header")
            current_url = urljoin(current_url, location)
        else:
            raise ValueError("URL redirected too many times")

    return FetchedMenuPage(
        requested_url=restaurant_url,
        final_url=current_url,
        html=response.text,
        host=parsed.netloc or "unknown-host",
    )


def timeout_from_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default

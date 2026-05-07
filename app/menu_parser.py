import hashlib
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.models import MenuItem, MenuScrapeResponse

PRICE_RE = re.compile(r"(?:^|\s)(\$ ?\d{1,3}(?:[.,]\d{2})?)(?:\s|$)")
NOISE_LABELS = {
    "about",
    "add to cart",
    "all",
    "book now",
    "cart",
    "contact",
    "delivery",
    "home",
    "hours",
    "locations",
    "menu",
    "menus",
    "order",
    "order now",
    "privacy policy",
    "reservations",
    "sign in",
}
ITEM_SELECTORS = [
    ".menu-item",
    ".dish",
    ".product",
    ".product-item",
    ".item",
    "[class*='menu-item']",
    "[class*='dish']",
    "[class*='product-title']",
    "li",
]
NAME_SELECTORS = [
    ".name",
    ".title",
    ".dish-name",
    ".product-title",
    "h2",
    "h3",
    "h4",
    "strong",
]
DESCRIPTION_SELECTORS = [
    ".description",
    ".desc",
    ".details",
    ".summary",
    ".body",
    "p",
]


def parse_menu_html(html: str, restaurant_url: str, host: str) -> MenuScrapeResponse:
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(strip=True) if soup.title else "Unknown Restaurant"
    menu_items = extract_menu_items(soup, restaurant_url)

    if not menu_items:
        raise ValueError(
            "No likely menu items were found. Try a direct menu page URL."
        )

    return MenuScrapeResponse(
        restaurant=f"{page_title} ({host})",
        source_url=restaurant_url,
        menu_items=menu_items,
    )


def menu_item_id(name: str, url: str, category: str | None = None) -> str:
    raw = f"{name}:{category or ''}:{url}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:10]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_price(text: str) -> str | None:
    match = PRICE_RE.search(text)
    if not match:
        return None
    return match.group(1).replace(" ", "")


def remove_price(text: str) -> str:
    return clean_text(PRICE_RE.sub(" ", text))


def looks_like_menu_item(text: str) -> bool:
    text = clean_text(text)
    lowered = text.lower()
    if lowered in NOISE_LABELS:
        return False
    if len(text) < 3 or len(text) > 90:
        return False
    if text.count(" ") > 10:
        return False
    alnum = [ch for ch in text if ch.isalnum()]
    if not alnum:
        return False
    digits = sum(ch.isdigit() for ch in alnum)
    return (digits / len(alnum)) < 0.35


def category_for_node(node: Tag) -> str | None:
    current = node
    while current:
        previous = current.find_previous(["h1", "h2", "h3"])
        if not previous:
            return None
        parent_class = " ".join(previous.find_parent().get("class", [])) if previous.find_parent() else ""
        if any(token in parent_class.lower() for token in ("menu-item", "dish", "product")):
            current = previous
            continue
        text = clean_text(previous.get_text(" ", strip=True))
        if text and looks_like_menu_item(text):
            return text
        current = previous
    return None


def first_matching_text(node: Tag, selectors: list[str]) -> str | None:
    for selector in selectors:
        child = node.select_one(selector)
        if not child:
            continue
        text = clean_text(child.get_text(" ", strip=True))
        if text:
            return text
    return None


def extract_item_from_node(node: Tag, restaurant_url: str) -> MenuItem | None:
    raw_text = clean_text(node.get_text(" ", strip=True))
    if not raw_text:
        return None

    name = first_matching_text(node, NAME_SELECTORS)
    if not name:
        name = raw_text.split(" - ", 1)[0].split(" | ", 1)[0]
    name = remove_price(name)

    if not looks_like_menu_item(name):
        return None

    price = extract_price(raw_text)
    description = first_matching_text(node, DESCRIPTION_SELECTORS)
    if description:
        description = remove_price(description)
        if description.lower() == name.lower() or len(description) < 6:
            description = None
    elif len(raw_text) > len(name) + 8:
        description = remove_price(raw_text.replace(name, "", 1))
        if not description or description.lower() == name.lower():
            description = None

    link = node if node.name == "a" else node.find("a", href=True)
    item_url = urljoin(restaurant_url, link["href"]) if link and link.get("href") else restaurant_url
    category = category_for_node(node)

    return MenuItem(
        id=menu_item_id(name=name, url=item_url, category=category),
        name=name,
        description=description,
        price=price,
        category=category,
        url=item_url,
    )


def extract_menu_items(soup: BeautifulSoup, restaurant_url: str) -> list[MenuItem]:
    candidates: list[MenuItem] = []
    for node in soup.select(", ".join(ITEM_SELECTORS)):
        if not isinstance(node, Tag):
            continue
        item = extract_item_from_node(node, restaurant_url)
        if item:
            candidates.append(item)

    deduped: list[MenuItem] = []
    seen = set()
    for item in candidates:
        key = (
            item.name.lower(),
            (item.category or "").lower(),
            (item.price or "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:40]

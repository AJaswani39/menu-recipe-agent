import base64
import hashlib
import re
from pathlib import Path

from app.gemini import (
    configured_api_key,
    extract_model_text,
    gemini_model,
    generate_content,
    parse_json_response,
    upload_file_to_gemini,
)
from app.models import MenuItem, MenuScrapeResponse

SUPPORTED_MIME_TYPES = {"image/png", "image/jpeg", "application/pdf"}
INLINE_LIMIT_BYTES = 20 * 1024 * 1024


async def extract_menu_from_upload(
    *,
    file_path: Path,
    mime_type: str,
    restaurant_name: str | None = None,
) -> MenuScrapeResponse:
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError("Unsupported file type. Upload a PNG, JPEG, or PDF menu.")

    api_key = configured_api_key()

    model = gemini_model()
    size = file_path.stat().st_size
    if size <= INLINE_LIMIT_BYTES:
        payload = _inline_payload(file_path, mime_type, restaurant_name)
    else:
        file_uri = await upload_file_to_gemini(file_path, mime_type, api_key)
        payload = _file_uri_payload(file_uri, mime_type, restaurant_name)

    data = await generate_content(payload, api_key=api_key, model=model, timeout=90.0)

    text = extract_model_text(data)
    if not text:
        raise ValueError("Gemini did not return menu text")

    parsed = parse_json_response(text)
    if not parsed:
        raise ValueError("Gemini did not return valid menu JSON")

    return _menu_from_parsed(parsed, file_path.name, restaurant_name)


def _inline_payload(
    file_path: Path, mime_type: str, restaurant_name: str | None
) -> dict:
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return {
        "contents": [
            {
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": encoded}},
                    {"text": _menu_prompt(restaurant_name)},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.1},
    }


def _file_uri_payload(
    file_uri: str, mime_type: str, restaurant_name: str | None
) -> dict:
    return {
        "contents": [
            {
                "parts": [
                    {"file_data": {"mime_type": mime_type, "file_uri": file_uri}},
                    {"text": _menu_prompt(restaurant_name)},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.1},
    }


def _menu_prompt(restaurant_name: str | None) -> str:
    return (
        "Extract restaurant menu items from this uploaded menu.\n"
        "Return strictly valid JSON with keys: restaurant (string), "
        "menu_items (array). Each menu item must include name (string), "
        "description (string or null), price (string or null), category "
        "(string or null).\n"
        "Do not include markdown or extra text.\n"
        f"Restaurant hint: {restaurant_name or 'unknown'}"
    )


def _menu_from_parsed(
    parsed: dict, source_label: str, restaurant_name: str | None
) -> MenuScrapeResponse:
    restaurant = _clean_text(
        str(parsed.get("restaurant") or restaurant_name or "Uploaded Menu")
    )
    raw_items = parsed.get("menu_items", [])
    if not isinstance(raw_items, list):
        raw_items = []

    items: list[MenuItem] = []
    seen = set()
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        name = _clean_text(str(raw_item.get("name") or ""))
        if not name:
            continue
        description = _optional_text(raw_item.get("description"))
        price = _optional_text(raw_item.get("price"))
        category = _optional_text(raw_item.get("category"))
        key = (name.lower(), (category or "").lower(), (price or "").lower())
        if key in seen:
            continue
        seen.add(key)
        items.append(
            MenuItem(
                id=_upload_item_id(name, source_label, category),
                name=name,
                description=description,
                price=price,
                category=category,
                url=f"upload://{source_label}",
            )
        )

    if not items:
        raise ValueError("No menu items were found in the upload")

    return MenuScrapeResponse(
        restaurant=restaurant,
        source_url=f"upload://{source_label}",
        menu_items=items[:80],
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = _clean_text(str(value))
    return cleaned or None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _upload_item_id(name: str, source_label: str, category: str | None) -> str:
    raw = f"{source_label}:{category or ''}:{name}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:10]

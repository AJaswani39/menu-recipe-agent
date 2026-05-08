from app.gemini import (
    GeminiConfigError,
    configured_api_key,
    extract_model_text,
    generate_content,
    gemini_model,
    parse_json_response,
    timeout_from_env,
)
from app.models import MenuItemExplanationRequest, MenuItemExplanationResponse

DEFAULT_GEMINI_EXPLANATION_TIMEOUT_SECONDS = 6.0


async def explain_menu_item(
    request: MenuItemExplanationRequest,
) -> MenuItemExplanationResponse:
    gemini_explanation = await _explain_with_gemini(request)
    if gemini_explanation:
        return gemini_explanation
    return _fallback_explanation(request)


async def _explain_with_gemini(
    request: MenuItemExplanationRequest,
) -> MenuItemExplanationResponse | None:
    try:
        api_key = configured_api_key()
    except GeminiConfigError:
        return None

    model = gemini_model()
    item = request.item
    prompt = (
        "Explain a restaurant menu item for a diner.\n"
        "Return strictly valid JSON with keys: summary (string), "
        "flavor_profile (array of short strings), likely_allergens (array of short strings), "
        "substitutions (array of short strings), confidence (similar|estimated).\n"
        "Do not include markdown. Avoid claiming certainty about allergens.\n"
        f"Restaurant: {request.restaurant_name or 'unknown'}\n"
        f"Dish: {item.name}\n"
        f"Description: {item.description or 'not provided'}\n"
        f"Category: {item.category or 'not provided'}\n"
        f"Price: {item.price or 'not provided'}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3},
    }

    try:
        data = await generate_content(
            payload,
            api_key=api_key,
            model=model,
            timeout=timeout_from_env(
                "GEMINI_EXPLANATION_TIMEOUT_SECONDS",
                DEFAULT_GEMINI_EXPLANATION_TIMEOUT_SECONDS,
            ),
        )
    except Exception:
        return None

    parsed = parse_json_response(extract_model_text(data) or "")
    if not parsed:
        return None

    summary = parsed.get("summary")
    flavor_profile = _normalize_text_list(parsed.get("flavor_profile"))
    likely_allergens = _normalize_text_list(parsed.get("likely_allergens"))
    substitutions = _normalize_text_list(parsed.get("substitutions"))
    confidence = parsed.get("confidence", "estimated")

    if not isinstance(summary, str) or not summary.strip():
        return None
    if confidence not in {"similar", "estimated"}:
        confidence = "estimated"

    return MenuItemExplanationResponse(
        summary=summary.strip(),
        flavor_profile=flavor_profile,
        likely_allergens=likely_allergens,
        substitutions=substitutions,
        confidence=confidence,
        source=f"Google Gemini ({model})",
    )


def _fallback_explanation(
    request: MenuItemExplanationRequest,
) -> MenuItemExplanationResponse:
    item = request.item
    description = item.description or "No menu description was provided."
    flavor_profile = _infer_flavors(f"{item.name} {description} {item.category or ''}")
    likely_allergens = _infer_allergens(f"{item.name} {description}")
    substitutions = [
        "Ask for sauce or dressing on the side.",
        "Ask whether dairy, gluten, nuts, or shellfish can be removed.",
        "Swap the main protein or base if the kitchen offers alternatives.",
    ]
    return MenuItemExplanationResponse(
        summary=(
            f"{item.name} appears to be a {item.category.lower()} item. "
            f"Menu context: {description}"
            if item.category
            else f"{item.name} appears to be a restaurant dish. Menu context: {description}"
        ),
        flavor_profile=flavor_profile,
        likely_allergens=likely_allergens,
        substitutions=substitutions,
        confidence="estimated",
        source="Heuristic menu explanation",
    )


def _infer_flavors(text: str) -> list[str]:
    lowered = text.lower()
    flavors: list[str] = []
    flavor_keywords = [
        ("spicy", "spicy"),
        ("chili", "spicy"),
        ("cream", "creamy"),
        ("cheese", "rich"),
        ("lemon", "bright"),
        ("lime", "bright"),
        ("garlic", "savory"),
        ("smoked", "smoky"),
        ("fried", "crispy"),
        ("honey", "sweet"),
    ]
    for keyword, flavor in flavor_keywords:
        if keyword in lowered and flavor not in flavors:
            flavors.append(flavor)
    return flavors or ["savory", "balanced"]


def _infer_allergens(text: str) -> list[str]:
    lowered = text.lower()
    allergens: list[str] = []
    allergen_keywords = [
        ("cheese", "dairy"),
        ("cream", "dairy"),
        ("butter", "dairy"),
        ("pasta", "gluten"),
        ("bread", "gluten"),
        ("bun", "gluten"),
        ("shrimp", "shellfish"),
        ("crab", "shellfish"),
        ("peanut", "peanuts"),
        ("almond", "tree nuts"),
        ("egg", "egg"),
        ("soy", "soy"),
    ]
    for keyword, allergen in allergen_keywords:
        if keyword in lowered and allergen not in allergens:
            allergens.append(allergen)
    return allergens or ["unknown from menu text"]


def _normalize_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]

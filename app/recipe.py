from app.gemini import (
    GeminiConfigError,
    check_config_status,
    configured_api_key,
    extract_model_text,
    generate_content,
    gemini_model,
    parse_json_response,
    timeout_from_env,
)
from app.models import DishSelectionRequest, RecipeResponse

DEFAULT_GEMINI_RECIPE_TIMEOUT_SECONDS = 8.0


_COMMON_RECIPES = {
    "chicken alfredo": {
        "ingredients": [
            "12 oz fettuccine",
            "2 chicken breasts, sliced",
            "2 tbsp olive oil",
            "3 cloves garlic, minced",
            "1 cup heavy cream",
            "1 cup grated parmesan",
            "Salt and black pepper",
            "Fresh parsley",
        ],
        "steps": [
            "Cook pasta in salted water until al dente and reserve some pasta water.",
            "Season chicken, then saute in oil over medium-high heat until cooked through.",
            "Add garlic and cook briefly until fragrant.",
            "Pour in cream and simmer gently for 2-3 minutes.",
            "Stir in parmesan until smooth; thin with pasta water as needed.",
            "Toss pasta and chicken with sauce, then top with parsley and pepper.",
        ],
    },
    "margherita pizza": {
        "ingredients": [
            "1 pizza dough ball",
            "1/2 cup crushed tomatoes",
            "6 oz fresh mozzarella",
            "Fresh basil leaves",
            "1 tbsp olive oil",
            "Salt",
        ],
        "steps": [
            "Preheat oven with a pizza stone to its highest temperature.",
            "Stretch dough and spread a thin layer of crushed tomatoes.",
            "Add mozzarella pieces and a pinch of salt.",
            "Bake until crust is puffed and charred in spots.",
            "Finish with basil and olive oil before serving.",
        ],
    },
}


async def get_recipe(selection: DishSelectionRequest) -> RecipeResponse:
    gemini_recipe = await _get_recipe_from_gemini(selection)
    if gemini_recipe:
        return gemini_recipe

    key = selection.dish_name.strip().lower()
    recipe = _COMMON_RECIPES.get(key)

    if recipe:
        return RecipeResponse(
            dish=selection.dish_name,
            ingredients=recipe["ingredients"],
            steps=recipe["steps"],
            source="Curated internal starter dataset",
            confidence="similar",
            servings=selection.servings,
            notes=(
                "This is a high-confidence base recipe and may differ from "
                "the exact restaurant version."
            ),
        )

    return RecipeResponse(
        dish=selection.dish_name,
        ingredients=[
            "Primary protein or vegetable for the dish",
            "Aromatics such as garlic/onion/ginger",
            "Acid or seasoning component",
            "Cooking fat",
            "Fresh herbs or garnish",
        ],
        steps=[
            "Prepare and season the main ingredients.",
            "Cook aromatics in fat until fragrant.",
            "Add core ingredients and cook until nearly done.",
            "Balance flavor with seasoning and acid, then finish cooking.",
            "Plate and garnish.",
        ],
        source="Heuristic fallback template",
        confidence="estimated",
        servings=selection.servings,
        notes=(
            "Gemini response unavailable and recipe not found in starter dataset."
        ),
    )


async def get_gemini_config_status() -> dict:
    return await check_config_status()


async def _get_recipe_from_gemini(selection: DishSelectionRequest) -> RecipeResponse | None:
    try:
        api_key = configured_api_key()
    except GeminiConfigError:
        return None

    model = gemini_model()

    prompt = (
        "You generate realistic cooking recipes.\n"
        "Use restaurant menu context when provided, but do not claim this is "
        "the exact proprietary restaurant recipe.\n"
        "Return strictly valid JSON with keys: ingredients (array of strings), "
        "steps (array of strings), confidence (exact|similar|estimated), notes (string).\n"
        "Do not include markdown.\n"
        f"Dish name: {selection.dish_name}\n"
        f"Restaurant: {selection.restaurant_name or 'unknown'}\n"
        f"Menu description: {selection.menu_description or 'not provided'}\n"
        f"Menu category: {selection.category or 'not provided'}\n"
        f"Listed price: {selection.price or 'not provided'}\n"
        f"Source URL: {selection.source_url or 'not provided'}\n"
        f"Servings: {selection.servings or 'not specified'}\n"
        f"Dietary preference: {selection.dietary_preference or 'none'}\n"
        f"Spice level: {selection.spice_level or 'not specified'}\n"
        f"Available equipment: {selection.equipment or 'not specified'}\n"
        f"Time limit minutes: {selection.time_limit_minutes or 'not specified'}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4},
    }

    try:
        data = await generate_content(
            payload,
            api_key=api_key,
            model=model,
            timeout=_timeout_from_env(
                "GEMINI_RECIPE_TIMEOUT_SECONDS",
                DEFAULT_GEMINI_RECIPE_TIMEOUT_SECONDS,
            ),
        )
    except Exception:
        return None

    text = extract_model_text(data)
    if not text:
        return None

    parsed = parse_json_response(text)
    if not parsed:
        return None

    ingredients = _normalize_text_list(parsed.get("ingredients"))
    steps = _normalize_text_list(parsed.get("steps"))
    confidence = parsed.get("confidence", "estimated")
    notes = parsed.get("notes", "Generated by Gemini.")

    if not ingredients:
        return None
    if not steps:
        return None
    if confidence not in {"exact", "similar", "estimated"}:
        confidence = "estimated"

    return RecipeResponse(
        dish=selection.dish_name,
        ingredients=ingredients,
        steps=steps,
        source=f"Google Gemini ({model})",
        confidence=confidence,
        servings=selection.servings,
        notes=notes,
    )


def _normalize_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _timeout_from_env(name: str, default: float) -> float:
    return timeout_from_env(name, default)

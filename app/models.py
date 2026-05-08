from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class MenuItem(BaseModel):
    id: str = Field(..., description="Stable ID for dish selection")
    name: str
    description: Optional[str] = None
    price: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None


class MenuScrapeResponse(BaseModel):
    restaurant: str
    source_url: str
    menu_items: List[MenuItem]


class MenuItemExplanationRequest(BaseModel):
    item: MenuItem
    restaurant_name: Optional[str] = None

    @field_validator("restaurant_name")
    @classmethod
    def normalize_restaurant_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class MenuItemExplanationResponse(BaseModel):
    summary: str
    flavor_profile: List[str]
    likely_allergens: List[str]
    substitutions: List[str]
    confidence: str
    source: str


class RecipeResponse(BaseModel):
    dish: str
    ingredients: List[str]
    steps: List[str]
    source: str
    confidence: str
    servings: Optional[int] = Field(default=None, ge=1, le=24)
    notes: Optional[str] = None


class HistorySummary(BaseModel):
    id: str
    source_type: str
    restaurant: str
    source_label: str
    created_at: str
    menu_item_count: int
    recipe_dish: Optional[str] = None


class HistoryRecord(HistorySummary):
    source_url: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    menu: Optional[MenuScrapeResponse] = None
    recipe: Optional[RecipeResponse] = None


class DishSelectionRequest(BaseModel):
    dish_name: str = Field(..., min_length=1, max_length=120)
    restaurant_name: Optional[str] = None
    menu_description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    source_url: Optional[str] = None
    servings: Optional[int] = Field(default=None, ge=1, le=24)
    dietary_preference: Optional[str] = Field(default=None, max_length=80)
    spice_level: Optional[str] = Field(default=None, max_length=40)
    equipment: Optional[str] = Field(default=None, max_length=120)
    time_limit_minutes: Optional[int] = Field(default=None, ge=5, le=480)

    @field_validator("dish_name")
    @classmethod
    def validate_dish_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("dish_name cannot be blank")
        return cleaned

    @field_validator("dietary_preference", "spice_level", "equipment")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AgentRunRequest(BaseModel):
    restaurant_url: str = Field(..., min_length=1)
    dish_name: str = Field(..., min_length=1, max_length=120)
    menu: Optional[MenuScrapeResponse] = None
    selected_item: Optional[MenuItem] = None
    menu_description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    history_id: Optional[str] = None
    servings: Optional[int] = Field(default=None, ge=1, le=24)
    dietary_preference: Optional[str] = Field(default=None, max_length=80)
    spice_level: Optional[str] = Field(default=None, max_length=40)
    equipment: Optional[str] = Field(default=None, max_length=120)
    time_limit_minutes: Optional[int] = Field(default=None, ge=5, le=480)

    @field_validator("restaurant_url", "dish_name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned

    @field_validator("dietary_preference", "spice_level", "equipment")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

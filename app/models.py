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


class RecipeResponse(BaseModel):
    dish: str
    ingredients: List[str]
    steps: List[str]
    source: str
    confidence: str
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

    @field_validator("dish_name")
    @classmethod
    def validate_dish_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("dish_name cannot be blank")
        return cleaned


class AgentRunRequest(BaseModel):
    restaurant_url: str = Field(..., min_length=1)
    dish_name: str = Field(..., min_length=1, max_length=120)
    menu: Optional[MenuScrapeResponse] = None
    selected_item: Optional[MenuItem] = None
    menu_description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    history_id: Optional[str] = None

    @field_validator("restaurant_url", "dish_name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned

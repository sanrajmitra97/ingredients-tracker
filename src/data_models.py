from pydantic import BaseModel, Field
from enum import Enum

class Category(str, Enum):
    staple = "staple"
    dairy = "dairy"
    protein = "protein"
    condiment = "condiment"
    produce = "produce"
    others = "others"

class MeasurementUnit(str, Enum):
    grams = "grams"
    millilitres = "millilitres"
    piecces = "pieces"

class IngredientInsertion(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Category
    unit_type: MeasurementUnit

class InventoryInsertion(BaseModel):
    quantity: float = Field(..., ge=0)
    minimum_threshold: float = Field(..., ge=0)
    expiration_date: str | None = None # e.g."2023-10-01"

class Ingredient(IngredientInsertion, InventoryInsertion):
    """Represents an ingredient in the inventory + ingredeint table."""
    pass

class IngredientInsertionResponse(IngredientInsertion, InventoryInsertion):
    ingredient_id: int
    inventory_id: int
    user_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

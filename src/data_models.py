from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import date, datetime

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
    pieces = "pieces"

class IngredientInsertion(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Category
    unit_type: MeasurementUnit

class InventoryInsertion(BaseModel):
    quantity: float = Field(..., ge=0)
    minimum_threshold: float = Field(..., ge=0)
    expiration_date: date | None = None # e.g."2023-10-01"

class InventoryUpdate(BaseModel):
    quantity: float | None = Field(default=None, ge=0)
    minimum_threshold: float | None = Field(default=None, ge=0)
    expiration_date: date | None = None # e.g."2023-10-01"

    class Config:
        # This validates that at least one field is provided for update
        @field_validator('__root__')
        def at_least_one_field(cls, values):
            if not any(v is not None for v in values.values()):
                raise ValueError('At least one field must be provided for update')
            return values        

class Ingredient(IngredientInsertion, InventoryInsertion):
    """Represents an ingredient in the inventory + ingredeint table."""
    pass

class IngredientFullResponse(IngredientInsertion, InventoryInsertion):
    ingredient_id: int
    inventory_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

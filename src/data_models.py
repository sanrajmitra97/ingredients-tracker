from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

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
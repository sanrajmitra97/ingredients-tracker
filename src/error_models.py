class IngredientAlreadyExistsInIngredientsError(Exception):
    """Raised when an ingredient already exists in the ingredients table."""
    pass

class IngredientInsertionError(Exception):
    """Raised when there is an error inserting an ingredient into the database."""
    pass

class IngredientAlreadyExistsInInventoryError(Exception):
    """Raised when an ingredient already exists in the inventory table for a user."""
    pass

class InventoryDeletionError(Exception):
    """Raised when there is an error deleting an ingredient from the inventory table."""
    pass

class InventoryUpdateError(Exception):
    """Raised when there is an error updating an ingredient in the inventory table."""
    pass

class IngredientNotFoundError(Exception):
    """Raised when an ingredient is not found in the ingredients or inventory table."""
    pass
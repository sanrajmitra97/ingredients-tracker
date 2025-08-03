class IngredientAlreadyExistsInIngredientsError(Exception):
    """Raised when an ingredient already exists in the ingredients table."""
    pass

class IngredientInsertionError(Exception):
    """Raised when there is an error inserting an ingredient into the database."""
    pass

class IngredientAlreadyExistsInInventoryError(Exception):
    """Raised when an ingredient already exists in the inventory table for a user."""
    pass
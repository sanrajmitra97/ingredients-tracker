from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import os
import logging

from src.asqlite_class import SqliteManager
from src.data_models import (
    IngredientInsertion,
    InventoryInsertion,
    Ingredient,
    IngredientFullResponse,
    InventoryUpdate
)

# Constants
DB_NAME = os.environ["DB_NAME"]
asqlite_manager = None

# Set up logger
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global asqlite_manager
    asqlite_manager = SqliteManager(db_name=DB_NAME)
    await asqlite_manager.connect()

    # Create test user for development
    test_user_id = await asqlite_manager.create_test_user()
    logger.info(f"Created test user with id {test_user_id} for development")

    yield
    await asqlite_manager.close()


app = FastAPI(lifespan=lifespan)


async def get_current_user_id() -> int:
    return 1


@app.get("/v1/health_check")
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/v1/inventory/by_name/{ingredient_name}/quantity")
async def get_ingredient_quantity_by_name(ingredient_name: str, user_id: int = Depends(get_current_user_id)) -> float:
    """
    Get the quantity of an ingredient name from the user's inventory as a float.

    If the ingredient is not present in the user's inventory, function will return 0.0.
    
    Args:
        ingredient_name (str) - The name of the ingredient.
    Returns:
        float - The quantity of ingredient.
    """
    return await asqlite_manager.get_ingredient_quantity_by_name(ingredient_name=ingredient_name, user_id=user_id)


@app.get("/v1/inventory/by_id/{ingredient_id}/quantity")
async def get_ingredient_quantity_by_id(ingredient_id: int, user_id: int = Depends(get_current_user_id)) -> float:
    """
    Get the quantity of an ingredient id from the user's inventory as a float.

    If the ingredient is not present in the user's inventory, function will return 0.0.
    
    Args:
        ingredient_id (int) - The id of the ingredient.
    Returns:
        float - The quantity of ingredient.
    """
    return await asqlite_manager.get_ingredient_quantity_by_id(ingredient_id=ingredient_id, user_id=user_id)


@app.get("/v1/ingredients/by_name/{ingredient_name}/measurement_unit")
async def get_ingredient_measurement_unit_by_name(ingredient_name: str, user_id: int = Depends(get_current_user_id)) -> str:
    """
    Get the measurement unit of the ingredient name provided.

    If the ingredient is not found in the `ingredients` table, it will raise an error.

    Args:
        ingredient_name (str) - The name of the ingredient.
    Returns:
        str - The measurement unit of the ingredient.
    """
    try:
        measurement_unit: str = await asqlite_manager.get_ingredient_measurement_unit_by_name(ingredient_name=ingredient_name)
    except Exception as e:
        error_msg = f"Got an error: {e}. {ingredient_name} not found in ingredients table. Please add it into the ingredients table."
        raise HTTPException(status_code=404, detail=error_msg)
    return measurement_unit


@app.get("/v1/ingredients/by_id/{ingredient_id}/measurement_unit")
async def get_ingredient_measurement_unit_by_id(ingredient_id: int, user_id: int = Depends(get_current_user_id)) -> str:
    """
    Get the measurement unit of the ingredient name provided.

    If the ingredient is not found in the `ingredients` table, it will raise an error.

    Args:
        ingredient_id (int) - The id of the ingredient.
    Returns:
        str - The measurement unit of the ingredient.
    """
    try:
        measurement_unit: str = await asqlite_manager.get_ingredient_measurement_unit_by_id(ingredient_id=ingredient_id)
    except Exception as e:
        error_msg = f"Got an error: {e}. Ingredient ID {ingredient_id} not found in ingredients table. Please add it into the ingredients table."
        raise HTTPException(status_code=404, detail=error_msg)
    return measurement_unit


@app.get("/v1/inventory/by_name/{ingredient_name}/info")
async def get_ingredient_info_by_name(ingredient_name: str, user_id: int = Depends(get_current_user_id)) -> dict:
    """
    Get the following information about the ingredient name of user id:
        - ingredient_id
        - name
        - category
        - unit_type
        - quantity
        - minimum_threshold
        - expiration_date
    Args:
        ingredient_name (str) - The name of the ingredient.
        user_id (int) - The user's id in the database.
    Returns:
        dict - A dictionary containing the ingredient's information.
    """
    ingredient_info = await asqlite_manager.get_ingredient_info_by_name(
        ingredient_name=ingredient_name, 
        user_id=user_id
    )

    if not ingredient_info:
        error_msg = f"{ingredient_name} not found in database. Please add it."
        raise HTTPException(status_code=404, detail=error_msg)
    return ingredient_info


@app.get("/v1/inventory/by_id/{ingredient_id}/info")
async def get_ingredient_info_by_id(ingredient_id: int, user_id: int = Depends(get_current_user_id)) -> dict:
    """
    Get the following information about the ingredient id of user id:
        - ingredient_id
        - name
        - category
        - unit_type
        - quantity
        - minimum_threshold
        - expiration_date
    Args:
        ingredient_id (int) - The id of the ingredient.
        user_id (int) - The user's id in the database.
    Returns:
        dict - A dictionary containing the ingredient's information.
    """
    ingredient_info = await asqlite_manager.get_ingredient_info_by_id(
        ingredient_id=ingredient_id, 
        user_id=user_id
    )

    if not ingredient_info:
        error_msg = f"{ingredient_id} not found in database. Please add it."
        raise HTTPException(status_code=404, detail=error_msg)
    return ingredient_info

@app.post("/v1/inventory", status_code=201, response_model=IngredientFullResponse)
async def add_ingredient_to_inventory(ingredient: Ingredient, user_id: int = Depends(get_current_user_id)):
    """
    Add a new ingredient into the inventory table.
    Break up the ingredient into two parts:
        - IngredientInsertion: name, category, unit_type
        - InventoryInsertion: quantity, minimum_threshold, expiration_date
    If the ingredient already exists in the inventory table, return a 409 Conflict error.
    If the ingredient already exists in the ingredients table, then just update the inventory table with the new values.
    If it does not exist in the ingredients table, then add it to the ingredients table first and then add it to the inventory table.

    Args:
        ingredient (Ingredient) - The ingredient to be added.
        user_id (int) - The user's id in the database.
    Returns:
        None - If the ingredient is added successfully.
    Raises:
        HTTPException - If the ingredient already exists in the inventory table.
    """
    ingredient_insertion = IngredientInsertion(
        name=ingredient.name,
        category=ingredient.category,
        unit_type=ingredient.unit_type
    )

    inventory_insertion = InventoryInsertion(
        quantity=ingredient.quantity,
        minimum_threshold=ingredient.minimum_threshold,
        expiration_date=ingredient.expiration_date
    )

    try:
        ingredient_exists_in_inventory = await asqlite_manager.ingredient_exists_in_inventory_by_name(
            ingredient_name=ingredient.name,
            user_id=user_id
        )
        if ingredient_exists_in_inventory:
            raise HTTPException(status_code=409, detail=f"{ingredient.name} already exists in the inventory. Update it's value instead.")
        
        ingredient_exists_in_ingredients_table = await asqlite_manager.ingredient_exists_in_ingredients_by_name(
            ingredient_name=ingredient.name
        )

        if not ingredient_exists_in_ingredients_table:
            # Add the ingredient into the ingredients table first
            try:
                ingredient_id = await asqlite_manager.add_ingredient_to_ingredients(ingredient_insertion)
            except Exception as e:
                error_msg = f"Error adding ingredient to ingredients table: {e}"
                if e.__class__.__name__ == "IngredientAlreadyExistsInIngredientsError":
                    raise HTTPException(status_code=409, detail=error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
        
        else:
            # Get the ingredient id from the ingredients table
            ingredient_id = await asqlite_manager.get_ingredient_id_by_name(ingredient_name=ingredient.name)
            if not ingredient_id:
                error_msg = f"Ingredient {ingredient.name} not found in ingredients table."
                raise HTTPException(status_code=404, detail=error_msg)

        # Add the ingredient into the inventory table
        try:
            inventory_meta_data: IngredientFullResponse = await asqlite_manager.add_ingredient_into_inventory(
                user_id=user_id,
                ingredient_id=ingredient_id,
                inventory_insertion=inventory_insertion
            )
        except Exception as e:
            error_msg = f"Error adding ingredient to inventory table: {e}"
            if e.__class__.__name__ == "IngredientAlreadyExistsInInventoryError":
                raise HTTPException(status_code=409, detail=error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        return inventory_meta_data
    
    except HTTPException as e:
        error_msg = f"Unknown error occurred while adding ingredient to inventory: {e}"
        logger.error(error_msg)
        raise e

@app.delete("/v1/inventory/by_id/{ingredient_id}")
async def delete_ingredient_from_inventory_by_id(ingredient_id: int, user_id: int = Depends(get_current_user_id)) -> None:
    """
    Delete an ingredient from the inventory table by its id for the user.
    
    If the ingredient does not exist in the inventory table, it will raise a 404 Not Found error.

    Args:
        ingredient_id (int) - The id of the ingredient to be deleted.
        user_id (int) - The user's id in the database.
    Returns:
        None - If the ingredient is deleted successfully.
    Raises:
        HTTPException - If the ingredient does not exist in the inventory table or if it is being used in any recipes.
    """
    try:
        # Check if the ingredient exists in the inventory for the user
        ingredient_exists = await asqlite_manager.ingredient_exists_in_inventory_by_id(
            ingredient_id=ingredient_id,
            user_id=user_id
        )
        
        if not ingredient_exists:
            error_msg = f"Ingredient with id {ingredient_id} does not exist in inventory for user {user_id}."
            raise HTTPException(status_code=404, detail=error_msg)
        
        
        res = await asqlite_manager.delete_ingredient_from_inventory_by_id(
            ingredient_id=ingredient_id,
            user_id=user_id
        )

        if not res:
            error_msg = f"Ingredient with id {ingredient_id} not found in inventory for user {user_id}."
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            logger.info(f"Deleted ingredient with id {ingredient_id} from inventory for user {user_id}.")
    
    except Exception as e:
        if e.__class__.__name__ == "InventoryDeletionError":
            error_msg = f"Error deleting ingredient from inventory: {e}"
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            error_msg = f"Unknown error occurred while deleting ingredient from inventory: {e}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

@app.patch("/v1/inventory/by_id/{ingredient_id}", response_model=IngredientFullResponse)
async def update_ingredient_in_inventory_by_id(ingredient_id: int, updates: InventoryUpdate, user_id: int = Depends(get_current_user_id)):
    """
    For a given ingredient id, together with the user id, update the ingredient in the inventory table.

    Args:
        ingredient_id (int) - The id of the ingredient to be updated.
        updates (InventoryInsertion) - The updates to be made to the ingredient.
        user_id (int) - The user's id in the database.
    Returns:
        IngredientFullResponse - The updated ingredient information.
    Raises:
        HTTPException - If the ingredient does not exist in the inventory table or if the updates are invalid.
    """
    try:
        # Check if the ingredient exists in the inventory for the user
        ingredient_exists = await asqlite_manager.ingredient_exists_in_inventory_by_id(
            ingredient_id=ingredient_id,
            user_id=user_id
        )

        if not ingredient_exists:
            error_msg = f"Ingredient with id {ingredient_id} does not exist in inventory for user {user_id}."
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Update the ingredient in the inventory table
        try:
            updates = updates.model_dump(exclude_unset=True)
            updated_ingredient: IngredientFullResponse = await asqlite_manager.update_ingredient_in_inventory_by_id(
                ingredient_id=ingredient_id,
                user_id=user_id,
                updates=updates
            )
            return updated_ingredient
        except Exception as e:
            error_msg = f"Error updating ingredient in inventory: {e}"
            if e.__class__.__name__ == "InventoryUpdateError":
                raise HTTPException(status_code=400, detail=error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
    
    except HTTPException as e:
        error_msg = f"Unknown error occurred while updating ingredient in inventory: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
# Get all the ingredients in the inventory for a user
@app.get("/v1/inventory")
async def get_all_ingredients_in_inventory(user_id: int = Depends(get_current_user_id)) -> list[IngredientFullResponse]:
    """
    Get all the ingredients in the inventory for a user.

    Args:
        user_id (int) - The user's id in the database.
    Returns:
        list[IngredientFullResponse] - A list of all ingredients in the user's inventory.
    """
    try:
        ingredients = await asqlite_manager.get_all_ingredients_in_inventory(user_id=user_id)
        return ingredients
    except Exception as e:
        error_msg = f"Error fetching ingredients from inventory: {e}"
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
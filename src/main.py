from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import os
import logging

from src.asqlite_class import SqliteManager

# Constants
DB_NAME = os.environ["DB_NAME"]
asqlite_manager = None

# Set up logger
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global asqlite_manager
    asqlite_manager = SqliteManager(db_name=DB_NAME)
    await asqlite_manager.connect()
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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
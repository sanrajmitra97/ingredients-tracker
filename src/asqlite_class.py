import aiosqlite
import logging
from typing import Tuple

from src.database_schemas import (
    users_schema, 
    ingredients_schema, 
    inventory_schema, 
    conversions_schema, 
    recipes_schema, 
    recipe_ingredients_schema
)

logger = logging.getLogger('uvicorn.error')

class SqliteManager:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self.conn = None
    
    async def connect(self) -> None:
        """
        Create a database with name self.db_name and initialize the tables: 
        users, ingredients, conversions, recipes, recipe_ingredients
        """
        # Connect to the database
        try:
            self.conn = await aiosqlite.connect(self.db_name)

            await self.conn.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints

            self.cur = await self.conn.cursor()

            # Initialize the users table
            await self.cur.execute(users_schema)
            
            # Initialize the ingredients table
            await self.cur.execute(ingredients_schema)

            # Initialize the inventory table
            await self.cur.execute(inventory_schema)

            # Initialize conversions table
            await self.cur.execute(conversions_schema)

            # Initialize recipes schema
            await self.cur.execute(recipes_schema)

            # Initialize recipe_ingredients schema
            await self.cur.execute(recipe_ingredients_schema)

            logger.info("Set up the tables.")

        except aiosqlite.Error as e1:
            logger.error(f"SQLite error when connnecting to {self.db_name} with error: {e1}")
            raise
        except Exception as e2:
            logger.error(f"Error when connecting to {self.db_name} with error: {e2}")
            raise

    async def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Closed asqlite connection.")
        
    async def get_connection(self) -> aiosqlite.Connection:
        """
        Get the connection to the sqlite database

        Args:
            None.
        Returns:
            Connection of type "aiosqlite.Connection".
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.conn
    
    async def get_ingredient_quantity_by_name(self, ingredient_name: str, user_id: int) -> float:
        """
        Get the quantity of ingredient name from the user's inventory.

        If the ingredient is not present in the user's inventory, function will return 0.0.
        
        Args:
            ingredient_name (str) - The name of the ingredient.
            user_id (int) - The user's id in the database.
        Returns:
            float - The quantity of ingredient.
        """
        query = """
            SELECT t1.quantity 
            FROM inventory t1
            INNER JOIN ingredients t2
            ON t1.ingredient_id = t2.id
            WHERE t1.user_id = ? AND t2.name = ?
        """
        res = await self.cur.execute(query, (user_id, ingredient_name))
        table: Tuple[float] = await res.fetchone()
        return table[0] if table else 0.0
    
    async def get_ingredient_quantity_by_id(self, ingredient_id: int, user_id: int) -> float:
        """
        Get the quantity of ingredient id from the user's inventory.

        If the ingredient is not present in the user's inventory, function will return 0.0.
        
        Args:
            ingredient_id (int) - The id of the ingredient.
            user_id (int) - The user's id in the database.
        Returns:
            float - The quantity of ingredient.
        """
        query = """
            SELECT quantity 
            FROM inventory 
            WHERE user_id = ? AND ingredient_id = ?
        """
        res = await self.cur.execute(query, (user_id, ingredient_id))
        table: Tuple[float] = await res.fetchone()
        return table[0] if table else 0.0
    
    async def get_ingredient_measurement_unit_by_name(self, ingredient_name: str) -> str:
        """
        Get the measurement unit of the ingredient name provided from the `ingredients` table. 
        If the ingredient does not exist in the `ingredient` table, raise an error.

        Args:
            ingredient_name (str) - The name of the ingredient.
        Returns:
            str - The measurement unit of the ingredient.
        """
        query = """
            SELECT unit_type
            FROM ingredients
            WHERE name = ?
        """
        res = await self.cur.execute(query, (ingredient_name, ))
        table: Tuple[str] = await res.fetchone()
        unit_type = table[0]
        if not unit_type:
            raise RuntimeError("Ingredient is not found inside the ingredients table")
        return unit_type
    
    async def get_ingredient_measurement_unit_by_id(self, ingredient_id: int) -> str:
        """
        Get the measurement unit of the ingredient id provided from the `ingredients` table. 
        If the ingredient does not exist in the `ingredients` table, raise an error.

        Args:
            ingredient_id (int) - The id of the ingredient.
        Returns:
            str - The measurement unit of the ingredient.
        """
        query = """
            SELECT unit_type
            FROM ingredients
            WHERE id = ?
        """
        res = await self.cur.execute(query, (ingredient_id, ))
        table: Tuple[str] = await res.fetchone()
        unit_type = table[0]
        if not unit_type:
            raise RuntimeError("Ingredient is not found inside the `ingredients` table")
        return unit_type
    
    async def get_ingredient_info_by_name(self, ingredient_name: str, user_id: int) -> dict:
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
        query = """
                SELECT t1.id, t1.name, t1.category, t1.unit_type, t2.quantity, t2.minimum_threshold, t2.expiration_date
                FROM ingredients t1
                RIGHT JOIN inventory t2
                ON t1.id = t2.ingredient_id
                WHERE t1.name = ? AND t2.user_id = ?
        """
        res = await self.cur.execute(query, (ingredient_name, user_id))
        table = await res.fetchone()
        if table:
            ingredient_id, name, category, unit_type, quantity, minimum_threshold, expiration_date = table
            return {
                "ingredient_id": ingredient_id,
                "name": name,
                "category": category,
                "unit_type": unit_type,
                "quantity": quantity,
                "minimum_threshold": minimum_threshold,
                "expiration_date": expiration_date
            }
        else:
            return {}

    async def get_ingredient_info_by_id(self, ingredient_id: int, user_id: int) -> dict:
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
            ingredient_id (id) - The id of the ingredient.
            user_id (int) - The user's id in the database.
        Returns:
            dict - A dictionary containing the ingredient's information.
        """
        query = """
                SELECT t1.id, t1.name, t1.category, t1.unit_type, t2.quantity, t2.minimum_threshold, t2.expiration_date
                FROM ingredients t1
                RIGHT JOIN inventory t2
                ON t1.id = t2.ingredient_id
                WHERE t1.id = ? AND t2.user_id = ?
        """
        res = await self.cur.execute(query, (ingredient_id, user_id))
        table = await res.fetchone()
        if table:
            ingredient_id, name, category, unit_type, quantity, minimum_threshold, expiration_date = table
            return {
                "ingredient_id": ingredient_id,
                "name": name,
                "category": category,
                "unit_type": unit_type,
                "quantity": quantity,
                "minimum_threshold": minimum_threshold,
                "expiration_date": expiration_date
            }
        else:
            return {}
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
from src.data_models import (
    IngredientInsertion,
    InventoryInsertion,
    IngredientFullResponse,
    Ingredient,
)
from src.error_models import (
    IngredientAlreadyExistsInIngredientsError,
    IngredientInsertionError,
    IngredientAlreadyExistsInInventoryError,
    InventoryDeletionError,
    InventoryUpdateError,
    IngredientNotFoundError
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
    
    async def create_test_user(self, email: str = "test@example.com") -> int:
        """Create a test user for development purposes. Not to be used in production."""
        query = """
            INSERT OR IGNORE INTO users (email, hashed_pw) 
            VALUES (?, 'dummy_hash_for_testing')
        """
        await self.cur.execute(query, (email,))
        await self.conn.commit()
        
        # Get the user ID
        get_query = "SELECT id FROM users WHERE email = ?"
        cursor = await self.cur.execute(get_query, (email,))
        result = await cursor.fetchone()
        return result[0] if result else None    
    
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
        Raises:
            IngredientNotFoundError - If the ingredient does not exist in the `ingredients` table.
        """
        query = """
            SELECT unit_type
            FROM ingredients
            WHERE name = ?
        """
        res = await self.cur.execute(query, (ingredient_name, ))
        table: Tuple[str] = await res.fetchone()
        if not table:
            raise IngredientNotFoundError("Ingredient is not found inside the ingredients table")
        return table[0]
    
    async def get_ingredient_measurement_unit_by_id(self, ingredient_id: int) -> str:
        """
        Get the measurement unit of the ingredient id provided from the `ingredients` table. 
        If the ingredient does not exist in the `ingredients` table, raise an error.

        Args:
            ingredient_id (int) - The id of the ingredient.
        Returns:
            str - The measurement unit of the ingredient.
        Raises:
            IngredientNotFoundError - If the ingredient does not exist in the `ingredients` table.
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
            raise IngredientNotFoundError("Ingredient is not found inside the `ingredients` table")
        return unit_type
    
    async def get_ingredient_info_by_name(self, ingredient_name: str, user_id: int) -> Ingredient:
        """
        Get the following information about the ingredient name of user id:
            - name
            - category
            - unit_type
            - quantity
            - minimum_threshold
            - expiration_date
        If the ingredient does not exist, return None.
        Args:
            ingredient_name (str) - The name of the ingredient.
            user_id (int) - The user's id in the database.
        Returns:
            Ingredient - The Ingredient class to return.
        """
        query = """
                SELECT t1.name, t1.category, t1.unit_type, t2.quantity, t2.minimum_threshold, t2.expiration_date
                FROM ingredients t1
                RIGHT JOIN inventory t2
                ON t1.id = t2.ingredient_id
                WHERE t1.name = ? AND t2.user_id = ?
        """
        res = await self.cur.execute(query, (ingredient_name, user_id))
        table = await res.fetchone()
        if table:
            name, category, unit_type, quantity, minimum_threshold, expiration_date = table
            return Ingredient(
                name=name,
                category=category,
                unit_type=unit_type,
                quantity=quantity,
                minimum_threshold=minimum_threshold,
                expiration_date=expiration_date
            )
        else:
            return None

    async def get_ingredient_info_by_id(self, ingredient_id: int, user_id: int) -> Ingredient:
        """
        Get the following information about the ingredient id of user id:
            - name
            - category
            - unit_type
            - quantity
            - minimum_threshold
            - expiration_date
        If the ingredient does not exist, return None.
        Args:
            ingredient_id (id) - The id of the ingredient.
            user_id (int) - The user's id in the database.
        Returns:
            Ingredient - The Ingredient class to return.
        """
        query = """
                SELECT t1.name, t1.category, t1.unit_type, t2.quantity, t2.minimum_threshold, t2.expiration_date
                FROM ingredients t1
                RIGHT JOIN inventory t2
                ON t1.id = t2.ingredient_id
                WHERE t1.id = ? AND t2.user_id = ?
        """
        res = await self.cur.execute(query, (ingredient_id, user_id))
        table = await res.fetchone()
        if table:
            name, category, unit_type, quantity, minimum_threshold, expiration_date = table
            return Ingredient(
                name=name,
                category=category,
                unit_type=unit_type,
                quantity=quantity,
                minimum_threshold=minimum_threshold,
                expiration_date=expiration_date
            )
        else:
            return None
    
    async def get_ingredient_id_by_name(self, ingredient_name: str) -> int | None:
        """
        Get the id of the ingredient name provided in the `ingredients` table.
        
        Args:
            ingredient_name (str) - The name of the ingredient.
        Returns:
            int - The id of the ingredient.
        Raises:
            IngredientNotFoundError - If the ingredient does not exist in the `ingredients` table.
        """
        query = """
                SELECT id
                FROM ingredients
                WHERE name = ?
        """
        res = await self.cur.execute(query, (ingredient_name,))
        table: Tuple[int] = await res.fetchone()
        if not table:
            raise IngredientNotFoundError(f"Ingredient {ingredient_name} not found in the `ingredients` table.")
        return table[0]
        
    async def ingredient_exists_in_inventory_by_name(self, ingredient_name: str, user_id: int) -> bool:
        """
        Given an ingredient name and user id, check if the ingredient exists in the user's inventory.
        Args:
            ingredient_name (str) - The name of the ingredient.
            user_id (int) - The user's id in the database.
        Returns:
            bool - True if the ingredient exists in the user's inventory, False otherwise.
        """
        query = """
                SELECT COUNT(*) 
                FROM inventory t1
                INNER JOIN ingredients t2
                ON t1.ingredient_id = t2.id
                WHERE t1.user_id = ? AND t2.name = ?
        """
        res = await self.cur.execute(query, (user_id, ingredient_name))
        exists: Tuple[int] = await res.fetchone()
        return exists[0] > 0

    async def ingredient_exists_in_inventory_by_id(self, ingredient_id: int, user_id: int) -> bool:
        """
        Given an ingredient id and user id, check if the ingredient exists in the user's inventory.
        
        Args:
            ingredient_id (int) - The id of the ingredient.
            user_id (int) - The user's id in the database.
        Returns:
            bool - True if the ingredient exists in the user's inventory, False otherwise.
        """
        query = """
                SELECT COUNT(*) 
                FROM inventory t1
                INNER JOIN ingredients t2
                ON t1.ingredient_id = t2.id
                WHERE t1.user_id = ? AND t2.id = ?
        """
        res = await self.cur.execute(query, (user_id, ingredient_id))
        exists: Tuple[int] = await res.fetchone()
        return exists[0] > 0
    
    async def ingredient_exists_in_ingredients_by_name(self, ingredient_name: str) -> bool:
        """
        Given an ingredient name, check if it exists in the `ingredients` table.
        
        Args:
            ingredient_name (str) - The name of the ingredient.
        Returns:
            bool - True if the ingredient exists in the `ingredients` table, False otherwise.
        """
        query = """
                SELECT COUNT(*) 
                FROM ingredients 
                WHERE name = ?
        """
        res = await self.cur.execute(query, (ingredient_name,))
        exists: Tuple[int] = await res.fetchone()
        return exists[0] > 0
    
    async def ingredient_exists_in_ingredients_by_id(self, ingredient_id: int) -> bool:
        """
        Given an ingredient id, check if it exists in the `ingredients` table.
        Args:
            ingredient_id (int) - The id of the ingredient.
        Returns:
            bool - True if the ingredient exists in the `ingredients` table, False otherwise.
        """
        query = """
                SELECT COUNT(*) 
                FROM ingredients 
                WHERE id = ?
        """
        res = await self.cur.execute(query, (ingredient_id,))
        exists: Tuple[int] = await res.fetchone()
        return exists[0] > 0

    async def add_ingredient_to_ingredients(self, ingredient: IngredientInsertion) -> int:
        """
        Add an ingredient into the `ingredients` table. Return the id of the ingredient.
        If the ingredient already exists in the `ingredients` table, raise an error.
        
        Args:
            ingredient (IngredientInsertion) - The ingredient to be added.
        Returns:
            int - The id of the ingredient.
        Raises:
            IngredientAlreadyExistsInIngredientsError - If the ingredient already exists in the `ingredients` table.
            IngredientInsertionError - If there is an error inserting the ingredient into the `ingredients` table.
        """
        if await self.ingredient_exists_in_ingredients_by_name(ingredient.name):
            raise IngredientAlreadyExistsInIngredientsError(f"Ingredient {ingredient.name} already exists in the `ingredients` table.")
        
        query = """
            INSERT INTO ingredients (name, category, unit_type)
            VALUES (?, ?, ?)
        """
        await self.cur.execute(query, (ingredient.name, ingredient.category, ingredient.unit_type))
        last_row_id = self.cur.lastrowid
        await self.conn.commit()
        if not last_row_id:
            await self.conn.rollback()
            raise IngredientInsertionError(f"Error inserting ingredient {ingredient.name} into the `ingredients` table.")
        logger.info(f"Added ingredient {ingredient.name} into the `ingredients` table with id {last_row_id}.")
        return last_row_id
        
    async def add_ingredient_into_inventory(self, user_id: int, ingredient_id: int, inventory_insertion: InventoryInsertion) -> IngredientFullResponse:
        """
        Add an ingredient into the `inventory` table. Return IngredientFullResponse object.
        
        Args:
            user_id (int) - The user's id in the database.
            ingredient_id (int) - The id of the ingredient.
            inventory_insertion (InventoryInsertion) - The inventory insertion data.
        
        Returns:
            IngredientFullResponse - The metadata of the ingredient insertion.
        
        Raises:
            IngredientInsertionError - If there is an error inserting the ingredient into the `inventory` table.
            IngredientAlreadyExistsInInventoryError - If the ingredient already exists in the `inventory` table for the user.
        """
        if await self.ingredient_exists_in_inventory_by_id(ingredient_id, user_id):
            raise IngredientAlreadyExistsInInventoryError(f"Ingredient with id {ingredient_id} already exists in the inventory for user {user_id}.")
        
        query = """
            INSERT INTO inventory (user_id, ingredient_id, quantity, minimum_threshold, expiration_date)
            VALUES (?, ?, ?, ?, ?)
        """
        await self.cur.execute(query, (user_id, ingredient_id, inventory_insertion.quantity, inventory_insertion.minimum_threshold, inventory_insertion.expiration_date))
        last_row_id = self.cur.lastrowid
        await self.conn.commit()
        if not last_row_id:
            await self.conn.rollback()
            raise IngredientInsertionError(f"Error inserting ingredient with id {ingredient_id} into the `inventory` table.")

        # Fetch the created_at and updated_at timestamps
        created_updated_timings_query = """
                                        SELECT created_at, updated_at
                                        FROM inventory
                                        WHERE id = ?
                                    """
        created_updated_res = await self.cur.execute(created_updated_timings_query, (last_row_id,))
        created_updated_table: Tuple[str, str] = await created_updated_res.fetchone()
        if not created_updated_table:
            raise IngredientInsertionError(f"Error fetching created_at and updated_at for ingredient with id {ingredient_id} in the `inventory` table.")
        
        created_at, updated_at = created_updated_table

        # Fetch the name, category, and unit_type from the ingredients table
        ingredient_info_query = """
                                    SELECT name, category, unit_type
                                    FROM ingredients
                                    WHERE id = ?
                                """
        ingredient_info_res = await self.cur.execute(ingredient_info_query, (ingredient_id,))
        ingredient_info_table: Tuple[str, str, str] = await ingredient_info_res.fetchone()
        if not ingredient_info_table:
            raise IngredientInsertionError(f"Error fetching ingredient info for ingredient with id {ingredient_id} in the `ingredients` table.")
        name, category, unit_type = ingredient_info_table
        logger.info(f"Added ingredient {name} with id {ingredient_id} into the `inventory` table with id {last_row_id} for user {user_id}.")
        return IngredientFullResponse(
            ingredient_id=ingredient_id,
            inventory_id=last_row_id,
            user_id=user_id,
            created_at=created_at,
            updated_at=updated_at,
            name=name,
            category=category,
            unit_type=unit_type,
            quantity=inventory_insertion.quantity,
            minimum_threshold=inventory_insertion.minimum_threshold,
            expiration_date=inventory_insertion.expiration_date
        )
    
    async def delete_ingredient_from_inventory_by_id(self, ingredient_id: int, user_id: int) -> bool:
        """
        Delete an ingredient from the `inventory` table by ingredient id and user id.
        
        Args:
            ingredient_id (int) - The id of the ingredient.
            user_id (int) - The user's id in the database.
        
        Returns:
            bool - True if the ingredient was deleted successfully, False otherwise.
        
        Raises:
            InventoryDeletionError - If the ingredient id does not exist in the `inventory` table for the user.
        """
        if not await self.ingredient_exists_in_inventory_by_id(ingredient_id, user_id):
            raise InventoryDeletionError(f"Ingredient with id {ingredient_id} does not exist in the inventory for user {user_id}.")
        
        query = """
            DELETE FROM inventory 
            WHERE ingredient_id = ? AND user_id = ?
        """
        await self.cur.execute(query, (ingredient_id, user_id))
        await self.conn.commit()
        if self.cur.rowcount == 0:
            return False
        logger.info(f"Deleted ingredient with id {ingredient_id} from the inventory for user {user_id}.")
        return True

    async def delete_ingredient_from_inventory_by_name(self, ingredient_name: str, user_id: int) -> bool:
        """
        Delete an ingredient from the `inventory` table by ingredient name and user id.
        
        Args:
            ingredient_name (str) - The name of the ingredient.
            user_id (int) - The user's id in the database.
        
        Returns:
            bool - True if the ingredient was deleted successfully, False otherwise.
        
        Raises:
            InventoryDeletionError - If the ingredient name does not exist in the `inventory` table for the user.
        """
        if not await self.ingredient_exists_in_inventory_by_name(ingredient_name, user_id):
            raise InventoryDeletionError(f"Ingredient {ingredient_name} does not exist in the inventory for user {user_id}.")
        
        query = """
            DELETE FROM inventory 
            WHERE user_id = ? AND ingredient_id = (
                SELECT id FROM ingredients WHERE name = ?
            )
        """
        await self.cur.execute(query, (user_id, ingredient_name))
        await self.conn.commit()

        if self.cur.rowcount == 0:
            return False
        logger.info(f"Deleted ingredient {ingredient_name} from the inventory for user {user_id}.")
        return True

    async def update_ingredient_in_inventory_by_id(self, ingredient_id: int, user_id: int, updates: dict) -> IngredientFullResponse:
        """
        Update an ingredient in the `inventory` table by ingredient id and user id.
        
        Args:
            ingredient_id (int) - The id of the ingredient.
            user_id (int) - The user's id in the database.
            updates (dict) - The updates to be made to the ingredient.
        
        Returns:
            IngredientFullResponse - The updated ingredient information.
        
        Raises:
            InventoryUpdateError - If the ingredient does not exist in the inventory table.
        """
        # Check if the ingredient exists in the inventory
        if not await self.ingredient_exists_in_inventory_by_id(ingredient_id, user_id):
            raise InventoryUpdateError(f"Ingredient with id {ingredient_id} does not exist in the inventory for user {user_id}.")
        
        # Prepare the update query
        update_fields = []
        update_values = []

        for key, value in updates.items():
            if value is not None:
                update_fields.append(f"{key} = ?")
                update_values.append(value)

        if not update_fields:
            raise InventoryUpdateError("No fields to update. At least one field must be provided for update.")
    

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.extend([user_id, ingredient_id])

        query = f"""
            UPDATE inventory
            SET {', '.join(update_fields)}
            WHERE user_id = ? AND ingredient_id = ?
        """
        await self.cur.execute(query, update_values)
        await self.conn.commit()

        if self.cur.rowcount == 0:
            raise InventoryUpdateError(f"Failed to update ingredient with id {ingredient_id} in the inventory for user {user_id}.")
        
        # Fetch the updated ingredient information
        updated_info_query = """
            SELECT t1.name, t1.category, t1.unit_type, t2.id, t2.quantity, t2.minimum_threshold, t2.expiration_date, t2.created_at, t2.updated_at
            FROM ingredients t1
            INNER JOIN inventory t2
            ON t1.id = t2.ingredient_id
            WHERE t1.id = ? AND t2.user_id = ?
        """
        updated_info_res = await self.cur.execute(updated_info_query, (ingredient_id, user_id))
        updated_info_table = await updated_info_res.fetchone()
        if not updated_info_table:
            raise InventoryUpdateError(f"Error fetching updated ingredient info for ingredient with id {ingredient_id} in the inventory for user {user_id}.")
        ingredient_name, category, unit_type, inventory_id, quantity, minimum_threshold, expiration_date, created_at, updated_at = updated_info_table

        logger.info(f"Updated ingredient with id {ingredient_id} in the inventory for user {user_id}.")
        return IngredientFullResponse(
            ingredient_id=ingredient_id,
            inventory_id=inventory_id,
            user_id=user_id,
            created_at=created_at,
            updated_at=updated_at,
            name=ingredient_name,
            category=category,
            unit_type=unit_type,
            quantity=quantity,
            minimum_threshold=minimum_threshold,
            expiration_date=expiration_date
        )
    
    async def update_ingredient_in_inventory_by_name(self, ingredient_name: str, user_id: int, updates: dict) -> IngredientFullResponse:
        """
        Update an ingredient in the `inventory` table by ingredient name and user id.
        
        Args:
            ingredient_name (str) - The name of the ingredient.
            user_id (int) - The user's id in the database.
            updates (dict) - The updates to be made to the ingredient.
        
        Returns:
            IngredientFullResponse - The updated ingredient information.
        
        Raises:
            InventoryUpdateError - If the ingredient does not exist in the inventory table.
        """
        # Check if the ingredient exists in the inventory
        if not await self.ingredient_exists_in_inventory_by_name(ingredient_name, user_id):
            raise InventoryUpdateError(f"Ingredient {ingredient_name} does not exist in the inventory for user {user_id}.")
        
        # Prepare the update query
        update_fields = []
        update_values = []

        for key, value in updates.items():
            if value is not None:
                update_fields.append(f"{key} = ?")
                update_values.append(value)

        if not update_fields:
            raise InventoryUpdateError("No fields to update. At least one field must be provided for update.")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.extend([user_id, ingredient_name])

        query = f"""
            UPDATE inventory
            SET {', '.join(update_fields)}
            WHERE user_id = ? AND ingredient_id = (
                SELECT id FROM ingredients WHERE name = ?
            )
        """
        await self.cur.execute(query, update_values)
        await self.conn.commit()

        if self.cur.rowcount == 0:
            raise InventoryUpdateError(f"Failed to update ingredient {ingredient_name} in the inventory for user {user_id}.")
        
        # Fetch the updated ingredient information
        updated_info_query = """
            SELECT t1.id, t1.name, t1.category, t1.unit_type, t2.id, t2.quantity, t2.minimum_threshold, t2.expiration_date, t2.created_at, t2.updated_at
            FROM ingredients t1
            INNER JOIN inventory t2
            ON t1.id = t2.ingredient_id
            WHERE t1.name = ? AND t2.user_id = ?
        """
        updated_info_res = await self.cur.execute(updated_info_query, (ingredient_name, user_id))
        updated_info_table = await updated_info_res.fetchone()
        if not updated_info_table:
            raise InventoryUpdateError(f"Error fetching updated ingredient info for ingredient {ingredient_name} in the inventory for user {user_id}.")
        ingredient_id, name, category, unit_type, inventory_id, quantity, minimum_threshold, expiration_date, created_at, updated_at = updated_info_table

        logger.info(f"Updated ingredient {ingredient_name} in the inventory for user {user_id}.")
        return IngredientFullResponse(
            ingredient_id=ingredient_id,
            inventory_id=inventory_id,
            user_id=user_id,
            created_at=created_at,
            updated_at=updated_at,
            name=name,
            category=category,
            unit_type=unit_type,
            quantity=quantity,
            minimum_threshold=minimum_threshold,
            expiration_date=expiration_date
        )
    
    async def get_all_ingredients_in_inventory(self, user_id: int) -> list[IngredientFullResponse]:
        """
        Get all ingredients in the inventory for a given user id.
        
        Args:
            user_id (int) - The user's id in the database.
        
        Returns:
            list[IngredientFullResponse] - A list of IngredientFullResponse objects containing ingredient information.
        """
        query = """
            SELECT t1.id, t1.name, t1.category, t1.unit_type, t2.id, t2.quantity, t2.minimum_threshold, t2.expiration_date, t2.created_at, t2.updated_at
            FROM ingredients t1
            INNER JOIN inventory t2
            ON t1.id = t2.ingredient_id
            WHERE t2.user_id = ?
        """
        res = await self.cur.execute(query, (user_id,))
        rows = await res.fetchall()
        
        ingredients = []
        for row in rows:
            ingredient_id, name, category, unit_type, inventory_id, quantity, minimum_threshold, expiration_date, created_at, updated_at = row
            ingredients.append(IngredientFullResponse(
                ingredient_id=ingredient_id,
                inventory_id=inventory_id,
                user_id=user_id,
                created_at=created_at,
                updated_at=updated_at,
                name=name,
                category=category,
                unit_type=unit_type,
                quantity=quantity,
                minimum_threshold=minimum_threshold,
                expiration_date=expiration_date
            ))
        
        return ingredients
        



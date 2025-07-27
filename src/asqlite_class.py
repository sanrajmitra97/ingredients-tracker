import aiosqlite
import logging

from src.database_schemas import (
    users_schema, 
    ingredients_schema, 
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
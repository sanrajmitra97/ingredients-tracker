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
    
    async def connect(self) -> None:
        """
        Create a database with name self.db_name and initialize the tables: 
        users, ingredients, conversions, recipes, recipe_ingredients
        """
        # Connect to the database
        try:
            self.conn = await aiosqlite.connect(self.db_name)

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

        except Exception as e:
            logger.error(f"Error when connectiong to {self.db_name} with error: {e}")

    async def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Closed asqlite connection.")
        

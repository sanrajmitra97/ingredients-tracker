users_schema = """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    hashed_pw TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """

ingredients_schema = """CREATE TABLE IF NOT EXISTS ingredients (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT UNIQUE NOT NULL,
                            category TEXT NOT NULL,
                            unit_type TEXT NOT NULL
                        );
                    """

inventory_schema = """CREATE TABLE IF NOT EXISTS inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        ingredient_id INTEGER NOT NULL,
                        quantity REAL NOT NULL,
                        minimum_threshold REAL NOT NULL,
                        expiration_date TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
                        UNIQUE(user_id, ingredient_id)
                    );
"""


conversions_schema = """CREATE TABLE IF NOT EXISTS conversions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ingredient_id INTEGER NOT NULL,
                            measurement_unit TEXT NOT NULL,
                            quantity_in_standard_unit REAL NOT NULL,
                            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON UPDATE CASCADE,
                            UNIQUE(ingredient_id, measurement_unit)
                        );
"""

recipes_schema = """CREATE TABLE IF NOT EXISTS recipes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        servings INTEGER DEFAULT 1,
                        prep_time_minutes INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );
"""


recipe_ingredients_schema = """CREATE TABLE IF NOT EXISTS recipe_ingredients (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    recipe_id INTEGER NOT NULL,
                                    ingredient_id TEXT NOT NULL,
                                    quantity REAL NOT NULL,
                                    unit TEXT NOT NULL,
                                    notes TEXT,
                                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                                    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
                                );
"""
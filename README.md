# High Level Thought Process

In this project, we want to build an app that tracks the number of ingredients you currently have in stock at your house. This lets a user view which recipes they can currently cook, as well as what they need to buy the next time they go shopping. And once bought, the quantities of the ingredients should be reflected in the app - either through manual input or through computer vision.

### Stack:

- Backend: FastAPI Web Server
- DB: SQLite
- Frontend: Undecided.

# `users` Table
1. `feature` - Every user will have an email and a password.
2. `feature` - Each password must be hashed for user protection.
3. `feature` - There will also be a "created date" and an "updated date" for each user. If a user decides to update their email or password, it should be reflected in the updated date.
4. `feature` - In the future, we want users to use their email to sign in (like they will log into google/twitter/etc.)

```sql
users (
		id INTEGER PRIMARY KEY AUTOINCREMENT
		email TEXT UNIQUE NOT NULL,
		hashed_pw TEXT NOT NULL,
		created_at TEXT DEFAULT CURRENT_TIMESTAMP,
		updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```
# `ingredients` Table
1. We need a table to record down all the unique ingredients we have in our database. 
2. We need to be consistent with units.  We use the following units:
    1. weight - grams.
    2. volume - millilitres. 
    3. pieces - itself.
3. The different categories:
    1. Produce - e.g. Banana, Garlic
    2. Protein - e.g. Eggs, Chicken Breast, Fish
    3. Staples - e.g. Sugar, Flour, Salt, Rice
    4. Dairy - e.g. Milk, Yogurt, Cheese
    5. Condiment - e.g. Rosemary
4. `feature` - For every new ingredient that the user wants to input, the app needs to update the `ingredients` table, as well as the `inventory` table.

```sql
ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL, -- category: produce, staples, protein, dairy, condiment
    unit_type TEXT NOT NULL, -- category: pieces, grams, millilitres
)
```
| id - `int` (pk) | name - `str` (unique) | category | unit_type - `str`
| --- | --- | --- | --- |
| 1 | banana | produce | pieces |
| 2 | rice | staples | grams |
| 3 | salt | staples | grams |
| 4 | milk | dairy | millilitres |
| 5 | flour | staples | grams |
| 6 | cooking oil | oils | millilitres |
| 7 | egg | protein | pieces |
| 8 | chicken breast | protein | grams |

# `inventory` Table
1. `feature` - For a new user, record down the different ingredients they have in the inventory table. This must be done if the user is not found in the `users` table.
4. `feature` - If an ingredient expires OR drops below the minimum_threshold value, we must notify the user that they need to top up this quantity in the UI. We can add this to a shopping list data structure.
5. `feature` - When a user is cooking a meal, the UI will display a check-box like design, telling the user to add the `quantity` `unit_type` of `name`. E.g. "Add 200 ml of milk". When the user has finished cooking, they would be prompted to "finish" cooking, which will give the backend the signal to subtract the quantities used during cooking.
6. `feature` - If a user decides to restock on ingredients, they should be allowed to add the ingredient into the app and the ingredient table should reflect this. This can later be upgraded to use computer vision to read the receipt, and add the values into a database.

```sql
inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ingredient_id INT NOT NULL,     -- users can have the same ingredient names
    quantity REAL NOT NULL,         -- The amount in stock
    minimum_threshold REAL NOT NULL,
    expiration_date TEXT,           -- some ingredients may not expire, like honey
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
    UNIQUE(user_id, ingredient_id)
)
```

| id - `int` (pk) | user_id - `str` (fk) | ingredient_id - `int` (fk) | quantity - `float` | minimum_threshold - `float` | expiration_date - `date` | created_at - `datetime` | updated_at - `datetime` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 12 | 3 | <today’s date + 5> | <today’s date> | <today’s date> |
| 2 | 1 | 2 | 5000 | 1000 | <today’s date + 5> | <today’s date> | <today’s date> |
| 3 | 1 | 3 | 500 | 100 | <today’s date + 5> | <today’s date> | <today’s date> |

# Conversion Table

1. In many recipes, different terms are used. For example, a cup of rice. A tablespoon of salt etc. Using a conversion table, we can convert the term used in the recipe, into the unit of measurement we are using under the `unit_type` column in the `ingredients` table. Then, we can subtract the value from the `inventory` table's "quantity" column as and when necessary.
2. `feature` - If a user wants to add a conversion, the backend must first check if the conversion exists for the `ingredient_id` and `measurement_unit` as this is distinct in the table.
3. `feature` - If a recipe states “Add (x) (measurement_unit)”, convert the (measurement_unit) used to get the quantity, and subtract the quantity from the `inventory` table when the user has used that ingredient to cook the dish.
4. For now, we are keeping this standardized across users for ease of implementation. In the future, users can add their own conversion values.

```sql
conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_id INTEGER NOT NULL,
    measurement_unit TEXT NOT NULL,
    quantity_in_standard_unit REAL NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON UPDATE CASCADE,
    UNIQUE(ingredient_id, measurement_unit)
)
```

| id - `int` (pk) | ingredient_id - `int` (fk) | measurement_unit - `str` | quantity_in_standard_unit - `float` |
| --- | --- | --- | --- |
| 1 | 2 | cup | 200 |
| 2 | 5 | cup | 120 |
| 3 | 3 | tablespoon | 19 |
| 4 | 3 | teaspoon | 6 |
| 5 | 4 | tablespoon | 14.7868 |
| 6 | 4 | teaspoon | 4.92892 |

# Recipe and Recipe Ingredients Table

1. `feature` - At any given point in time, we need to reflect what recipes are cookable, i.e. if the user has enough ingredients, then the UI should show these are the possible recipes. Hence, we should have a list of cookable recipes.
2. `feature` - When a user wants to cook a recipe, the backend will check whether they have enough ingredients to cook the chosen recipe, and if not, what are the missing ingredients, and their quantities.
3. `feature` - The app should have search a functionality of the different recipies and ingredients, so the user can see their recipes and see how much of their ingredients they have left.
4. `feature` - When adding a recipe, a user will add their own recipe, together with the ingredients required and the name, prep time etc. i.e. Everything that is required for `recipes` table and `recipe_ingredients` table.
5. `feature` - The user should also be able to search for recipes using the web, and add it dynamically to the app database. This can be added as a future feature.


```sql
recipes (
		id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,  -- user ownership of the recipe
		name TEXT NOT NULL,
		description TEXT,
		servings INTEGER DEFAULT 1,
		prep_time_minutes INTEGER,
		created_at TEXT DEFAULT CURRENT_TIMESTAMP,
		updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)

recipe_ingredients (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		recipe_id INTEGER NOT NULL,
		ingredient_name TEXT NOT NULL,
		quantity REAL NOT NULL,
		unit TEXT NOT NULL,
		notes TEXT, --e.g. "chopped", "room temperature" etc.
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_name) REFERENCES ingredients(name) ON UPDATE CASCADE
)
```

### Recipe

| id - `int` <primary_key> | user_id - `int` | name - `str` | description - `str` | servings - `int` | prep_time_minutes - `int` | created_at - `datetime` | updated_at - `datetime` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | Tomato Pasta | some text | 1 | 30 | datetime | datetime |
| … | … | … | … | … | … | … | … |

### Recipe Ingredients

| id - `int` <primary key> | recipe_id - `int` <foreign_key 1> | ingredient_name - `str` <foreign key 2> | quantity - `int` | unit - `str` | notes - `str` |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | salt | 1.0 | grams | some text |
| 2 | 1 | pasta | 100 | grams | some text |
| 3 | 1 | cooking oil |  5| millilitres | some text |

# Backend Endpoints
These are the general endpoints we want to create. It may not reflect the actual arguments that go into the endpoints or what is getting returned.

1. `get_ingredient_quantity(ingredient: str | int, user_id: int) -> float`
    1. Given an ingredient and user, return the quantity available.
2. `get_ingredient_info(ingredient: str | id, user_id: int) -> Ingredient`
    1. Given an ingredient and user, return the row associated with that ingredient from the `ingredients` and `inventory` table.
3. `add_new_ingredient(ingredient: Ingredient, user_id: int) -> None` 
    1. Adds a new ingredient into the `inventory` and `ingredient` table for that user.
4. `delete_ingredient(ingredient: Ingredient, user_id: int) -> None`
    1. This function deletes the entire ingredient from the `ingredients`, which should then cascade into the `inventory` table. It should not get deleted from the `conversions` table.
5. `update_ingredient(ingredient: str | id, info: dict, user_id: int) -> None`
    1. This function updates information of an ingredient like quantity, in the `inventory` table.
6. `get_recipe(recipe_id: int, user_id: int) → Recipe`
    1. This function should display the ingredients needed, together with their associated quantities, for a given recipe id and user id.
8. `add_recipe(recipe_name: str, recipe_ingredients: Recipe, user_id: int) -> None`
    1. This function should allow users to add recipes to the backend database. Populate both recipe and recipe_ingredients table.
9. `delete_recipe(recipe_name: str, user_id: int) -> None`
    1. Deletes the recipe row from the table. Delete from both recipe and recipe_ingredients table.
10. `is_cookable_recipe(recipe: str | int, user_id: int) -> bool`
    1. Checks if we have enough ingredients for a particular recipe.
11. `get_missing_ingredients(recipe: str | int, user_id: int) -> List[IngredientBasicInfo]`
    1. Lists the missing ingredients (name, quantity) for a particular recipe, given the current ingredients we have.
12. `get_cookable_recipes(user_id: int) -> List[Recipe]` 
    1. Check ingredient availailability for every recipe, and returns a List of recipes that we can cook.
13. `cook_recipe(recipe_id: int, servings: float, user_id: int, **kwargs) -> None`
    1. Deducts the ingredients from the Ingredients database, depending on the number of servings made. If a user added more than the necessary ingredients or less, then the user should provide a custom object that describes which fields should be updated, and by how much.
14. `get_shopping_list(user_id: int) -> List[IngredientBasicInfo]`
    1. A list of ingredients to buy that have dropped below the minimum threshold or have expired.
15. `get_expiring_ingredients(user_id: int, days: int = 7) -> List[Tuple[str, date]]`
    1. Show which ingredients are about to expire in `days` days, and when their expiry date is.
16. `get_conversion(ingredient: str | id) -> float`
    1. Get the conversion of an ingredient.
17. Other functions to add:
    1. unit_validation → Ensure recipe ingredients use units that exist in your conversion table or are already standardized.
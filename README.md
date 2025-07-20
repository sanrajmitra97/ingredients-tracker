# High Level Thought Process

In this project, we want to build an app that tracks the number of ingredients you currently have in stock at your house. This lets a user view which recipes they can currently cook, as well as what they need to buy the next time they go shopping.

### Stack:

- Backend: FastAPI Web Server
- DB: SQL Lite
- Frontend: Undecided.

# Ingredients Table

1. `feature` - For a new user, record down the different ingredients they have. 
2. We need to be consistent with units.  We use the following units:
    1. weight - grams.
    2. volume - millilitres. 
    3. atomic - itself.
3. The different categories:
    1. Produce - e.g. Banana, Garlic
    2. Proteins - e.g. Eggs, Chicken Breast, Fish
    3. Staples - e.g. Sugar, Flour, Salt, Rice
    4. Dairy - e.g. Milk, Yogurt, Cheese
4. `feature` - If an ingredient expires OR drops below the minimum_threshold value, we must notify the user that they need to top up this quantity in the UI. We can add this to a shopping list data structure.
5. `feature` - When a user is cooking a meal, the UI will display a check-box like design, telling the user to add the `quantity` `unit_type` `name`. E.g. "Add 200 ml of milk". When the user has finished cooking, they would be prompted to "finish" cooking, which will give the backend the signal to subtract the quantities used during cooking.
6. `feature` - If a user decides to buy new ingredients, they should be allowed to add the ingredient into the app and the database should reflect this. This can later be upgraded to use computer vision to read the receipt, and add the values into a database.

```sql
ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL, -- produce, staples, protein, dairy
    unit_type TEXT NOT NULL, -- atomic, grams, millilitres
    quantity FLOAT NOT NULL, -- The amount in stock
    minimum_threshold FLOAT NOT NULL,
    expiration_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

| id - `int` (pk) | name - `str` (unique) | catgegory - `str` | unit_type - `str` | quantity - `float` | minimum_threshold - `float` | expiration_date - `date` | created_at - `datetime` | updated_at - `datetime` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | banana | produce | atomic | 12 | 3 | <today’s date + 5> | <today’s date> | <today’s date> |
| 2 | rice | staples | grams | 5000 | 1000 | <today’s date + 5> | <today’s date> | <today’s date> |
| 3 | salt | staples | grams | 500 | 100 | <today’s date + 5> | <today’s date> | <today’s date> |
| 4 | milk | dairy | millilitres | 1500 | 200 | <today’s date + 5> | <today’s date> | <today’s date> |
| 5 | flour | staples | grams | 1000 | 200 | <today’s date + 5> | <today’s date> | <today’s date> |
| 6 | cooking oil | oils | millilitres | 1000 | 200 | <today’s date + 5> | <today’s date> | <today’s date> |
| 7 | egg | protein | atomic | 12 | 2 | <today’s date + 5> | <today’s date> | <today’s date> |
| 8 | chicken breast | protein | grams | 500 | 50 | <today’s date + 5> | <today’s date> | <today’s date> |

## Conversion Table

1. In many recipes, different terms are used. For example, a cup of rice. A tablespoon of salt etc. Using a conversion table, we can convert the term used in the recipe, into a quantity that is used in the Ingredients table. Then, we can subtract the value from the Ingredients table as and when necessary.
2. `feature` - If a recipe states “Add (x) (measurement_unit)”, convert the (measurement_unit) used to get the quantity, and subtract the quantity from the Ingredients table when the user has used that ingredient to cook the dish.

```sql
conversions (
    id INTEGER PRIMARY KEY,
    ingredient_name TEXT NOT NULL,
    measurement_unit TEXT NOT NULL,
    quantity_in_standard_unit FLOAT NOT NULL,
    FOREIGN KEY (ingredient_name) REFERENCES ingredients(name) ON UPDATE CASCADE,
    UNIQUE(ingredient_name, measurement_unit)
)
```

| id - `int` (pk) | ingredient_name - `str` (fk) | measurement_unit - `str` | quantity_in_standard_unit - `float` |
| --- | --- | --- | --- |
| 1 | rice | cup | 200 |
| 2 | flour | cup | 120 |
| 3 | salt | tablespoon | 19 |
| 4 | salt | teaspoon | 6 |
| 5 | cooking oil | tablespoon | 14.7868 |
| 6 | cooking oil | teaspoon | 4.92892 |

## Recipe and Recipe Ingredients Table

1. `feature` - At any given point in time, we need to reflect what recipes are cookable, i.e. if the user has enough ingredients, then the UI should show these are the possible recipes. Hence, we should have a list of cookable recipes.
2. `feature` - When a user wants to cook a recipe, the backend will check whether they have enough ingredients to cook the chosen recipe, and if not, what are the missing ingredients, and their quantities.
3. `feature` - The app should have search a functionality of the different recipies and ingredients, so the user can see their recipes and see how much of their ingredients they have left.
4. `feature` -The user should also be able to search for recipes using the web, and add it dynamically to the app database. This can be added as a future feature.

```sql
recipes (
		id INTEGER PRIMARY KEY,
		name TEXT NOT NULL,
		description TEXT,
		servings INTEGER DEFAULT 1,
		prep_time_minutes INTEGER,
		created_at DATETIME,
		updated_at DATETIME
)

recipe_ingredients (
		id INTEGER PRIMARY KEY,
		recipe_id INTEGER NOT NULL,
		ingredient_name TEXT NOT NULL,
		quantity FLOAT NOT NULL,
		unit TEXT NOT NULL,
		notes TEXT, --e.g. "chopped", "room temperature" etc.
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_name) REFERENCES ingredients(name) ON UPDATE CASCADE
)
```

### Recipe

| id - `int` <primary_key> | name - `str` | description - `str` | servings - `int` | prep_time_minutes - `int` | created_at - `datetime` | updated_at - `datetime` |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Tomato Pasta | some text | 1 | 30 | datetime | datetime |
| … | … | … | … | … | … | … |

### Recipe Ingredients

| id - `int` <primary key> | recipe_id - `int` <foreign_key 1> | ingredient_name - `str` <foreign key 2> | quantity - `int` | unit - `str` | notes - `str` |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | salt | 1.0 | grams | some text |
| 2 | 1 | pasta | 100 | grams | some text |
| 3 | 1 | cooking oil |  5| millilitres | some text |

# Backend Endpoints

1. `get_ingredient_quantity(ingredient: str | id) -> float`
    1. Given an ingredient, the function returns the quantity available.
2. `get_ingredient_info(ingredient: str | id) -> Ingredient`
    1. Given an ingredient, return the row associated with that ingredient from the Ingredients table.
3. `add_new_ingredient(ingredient: Ingredient) -> None` 
    1. This function should allow users to add a new ingredient into the Ingredients table.
4. `delete_ingredient(ingredient: Ingredient) -> None`
    1. This function deletes the entire ingredient from the Ingredients table.
5. `update_ingredient(ingredient: str | id, info: dict) -> None`
    1. This function updates information of an ingredient like quantity etc.
6. `get_recipe(recipe_id: int) → Recipe`
    1. This function should display the ingredients needed, together with their associated quantity, for a given recipe id.
8. `add_recipe(recipe_name: str, recipe_ingredients: Recipe) -> None`
    1. This function should allow users to add recipes to the backend database. Populate both recipe and recipe_ingredients table.
9. `delete_recipe(recipe_name: str) -> None`
    1. Deletes the recipe row from the table. Delete from both recipe and recipe_ingredients table.
10. `is_cookable_recipe(recipe: str | int) -> bool`
    1. Checks if we have enough ingredients for a particular recipe.
11. `get_missing_ingredients(recipe: str | int) -> List[IngredientBasicInfo]`
    1. Lists the missing ingredients (name, quantity) for a particular recipe, given the current ingredients we have.
12. `get_cookable_recipes() -> List[Recipe]` 
    1. Check ingredient availailability for every recipe, and returns a List of recipes that we can cook.
13. `cook_recipe(recipe_id: int, servings: float, **kwargs) -> None`
    1. Deducts the ingredients from the Ingredients database, depending on the number of servings made. If a user added more than the necessary ingredients or less, then the user should provide a custom object that describes which fields should be updated, and by how much.
14. `get_shopping_list() -> List[IngredientBasicInfo]`
    1. A list of ingredients to buy that have dropped below the minimum threshold or have expired.
15. `get_expiring_ingredients(days: int = 7) -> List[Tuple[str, date]]`
    1. Show which ingredients are about to expire in `days` days, and when their expiry date is.
16. Other functions to add:
    1. unit_validation → Ensure recipe ingredients use units that exist in your conversion table or are already standardized.


# Sources
1. Google.
#!/usr/bin/env python3
"""
Database population script for KitchenBuddy
Creates sample recipes and admin user for testing voice assistant features
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.db_models import User, Recipe, Step
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user for testing"""
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@kitchenbuddy.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True,
            voice_enabled=True,
            dietary_preferences='vegetarian,gluten-free'
        )
        db.session.add(admin)
        print("✓ Admin user created")
    else:
        print("✓ Admin user already exists")
    
    # Create a regular user
    user = User.query.filter_by(username='user').first()
    if not user:
        user = User(
            username='user',
            email='user@kitchenbuddy.com',
            password_hash=generate_password_hash('user123'),
            is_admin=False,
            voice_enabled=True,
            dietary_preferences='vegan'
        )
        db.session.add(user)
        print("✓ Regular user created")
    else:
        print("✓ Regular user already exists")

def create_sample_recipes():
    """Create sample recipes for testing voice commands"""
    
    # Sample recipes data
    recipes_data = [
        {
            'title': 'Butter Chicken',
            'category': 'Main Course',
            'ingredients': '''500g chicken breast, cubed
1 cup yogurt
2 tbsp tandoori masala
2 tbsp butter
1 cup tomato puree
1/2 cup cream
1 tbsp kasoori methi
1 tsp garam masala
1 tsp red chili powder
1 tbsp ginger-garlic paste
Salt to taste''',
            'dietary_tags': 'non-vegetarian,gluten-free,creamy',
            'cooking_time': 45,
            'difficulty_level': 'medium',
            'voice_description': 'A rich and creamy Indian curry with tender chicken pieces in a tomato-based sauce.',
            'steps': [
                'Marinate chicken with yogurt, tandoori masala, and salt for 2 hours.',
                'Grill or bake chicken until charred and cooked through.',
                'Heat butter in a pan, add ginger-garlic paste, cook for 2 minutes.',
                'Add tomato puree, spices, and cook until oil separates.',
                'Add cream, kasoori methi, and cooked chicken.',
                'Simmer for 10 minutes, garnish with cream and butter.',
                'Serve hot with naan or rice.'
            ]
        },
        {
            'title': 'Vegetable Stir Fry',
            'category': 'Main Course',
            'ingredients': '''2 tbsp vegetable oil
2 cloves garlic, minced
1 inch ginger, minced
2 bell peppers, sliced
1 cup broccoli florets
1 cup snap peas
2 carrots, julienned
2 tbsp soy sauce
1 tbsp oyster sauce
1 tsp cornstarch
1/4 cup water
Salt and pepper to taste''',
            'dietary_tags': 'vegetarian,vegan,gluten-free',
            'cooking_time': 20,
            'difficulty_level': 'easy',
            'voice_description': 'A quick and healthy stir-fry with colorful vegetables in a savory sauce.',
            'steps': [
                'Heat oil in a wok or large skillet over high heat.',
                'Add garlic and ginger, stir-fry for 30 seconds until fragrant.',
                'Add bell peppers and carrots, stir-fry for 2 minutes.',
                'Add broccoli and snap peas, continue stir-frying for 3 minutes.',
                'Mix cornstarch with water and add to pan along with soy sauce and oyster sauce.',
                'Stir until sauce thickens, about 1-2 minutes.',
                'Season with salt and pepper, serve hot over steamed rice.'
            ]
        },
        {
            'title': 'Chocolate Chip Cookies',
            'category': 'Dessert',
            'ingredients': '''2 1/4 cups all-purpose flour
1 tsp baking soda
1 tsp salt
1 cup unsalted butter, softened
3/4 cup granulated sugar
3/4 cup brown sugar
2 large eggs
2 tsp vanilla extract
2 cups chocolate chips''',
            'dietary_tags': 'vegetarian,contains-dairy',
            'cooking_time': 25,
            'difficulty_level': 'easy',
            'voice_description': 'Classic homemade chocolate chip cookies with crispy edges and chewy centers.',
            'steps': [
                'Preheat oven to 375°F (190°C) and line baking sheets with parchment paper.',
                'In a bowl, whisk together flour, baking soda, and salt.',
                'In a large bowl, cream together butter and both sugars until light and fluffy.',
                'Beat in eggs one at a time, then stir in vanilla.',
                'Gradually mix in the flour mixture until just combined.',
                'Stir in chocolate chips.',
                'Drop rounded tablespoons of dough onto prepared baking sheets.',
                'Bake for 9-11 minutes until golden brown around the edges.',
                'Let cool on baking sheets for 5 minutes, then transfer to wire racks.'
            ]
        },
        {
            'title': 'Greek Salad',
            'category': 'Salad',
            'ingredients': '''1 large cucumber, diced
4 large tomatoes, diced
1 red onion, thinly sliced
1 cup Kalamata olives
200g feta cheese, cubed
2 tbsp extra virgin olive oil
1 tbsp red wine vinegar
1 tsp dried oregano
Salt and pepper to taste''',
            'dietary_tags': 'vegetarian,gluten-free',
            'cooking_time': 15,
            'difficulty_level': 'easy',
            'voice_description': 'A refreshing Mediterranean salad with fresh vegetables and tangy feta cheese.',
            'steps': [
                'In a large bowl, combine cucumber, tomatoes, and red onion.',
                'Add Kalamata olives and feta cheese cubes.',
                'In a small bowl, whisk together olive oil, red wine vinegar, and oregano.',
                'Pour dressing over the salad and gently toss to combine.',
                'Season with salt and pepper to taste.',
                'Let the salad sit for 10 minutes to allow flavors to meld.',
                'Serve chilled as a refreshing side dish or light meal.'
            ]
        },
        {
            'title': 'Avocado Toast',
            'category': 'Breakfast',
            'ingredients': '''2 slices whole grain bread
1 ripe avocado
1 lemon
Salt and pepper to taste
Red pepper flakes (optional)
Microgreens or sprouts (optional)''',
            'dietary_tags': 'vegetarian,vegan,gluten-free',
            'cooking_time': 10,
            'difficulty_level': 'easy',
            'voice_description': 'A simple and nutritious breakfast with creamy avocado on crispy toast.',
            'steps': [
                'Toast the bread until golden brown and crispy.',
                'Cut the avocado in half, remove the pit, and scoop the flesh into a bowl.',
                'Mash the avocado with a fork until smooth but still slightly chunky.',
                'Squeeze lemon juice over the mashed avocado and season with salt and pepper.',
                'Spread the avocado mixture evenly over the toasted bread.',
                'Sprinkle with red pepper flakes if desired.',
                'Top with microgreens or sprouts for extra nutrition and presentation.',
                'Serve immediately while the toast is still warm and crispy.'
            ]
        }
    ]
    
    # Get admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("❌ Admin user not found. Please run create_admin_user() first.")
        return
    
    # Create recipes
    for recipe_data in recipes_data:
        # Check if recipe already exists
        existing_recipe = Recipe.query.filter_by(title=recipe_data['title']).first()
        if existing_recipe:
            print(f"✓ Recipe '{recipe_data['title']}' already exists")
            continue
        
        # Create recipe
        recipe = Recipe(
            title=recipe_data['title'],
            category=recipe_data['category'],
            ingredients=recipe_data['ingredients'],
            dietary_tags=recipe_data['dietary_tags'],
            user_id=admin.id,
            cooking_time=recipe_data['cooking_time'],
            difficulty_level=recipe_data['difficulty_level'],
            voice_description=recipe_data['voice_description']
        )
        db.session.add(recipe)
        db.session.flush()  # Get the recipe ID
        
        # Add steps
        for i, step_text in enumerate(recipe_data['steps'], 1):
            step = Step(
                recipe_id=recipe.id,
                step_number=i,
                instruction=step_text.strip()
            )
            db.session.add(step)
        
        print(f"✓ Recipe '{recipe_data['title']}' created with {len(recipe_data['steps'])} steps")

def main():
    """Main function to populate the database"""
    print("🍳 KitchenBuddy Database Population Script")
    print("=" * 50)
    
    with app.app_context():
        # Create database tables
        db.create_all()
        print("✓ Database tables created")
        
        # Create users
        create_admin_user()
        
        # Create sample recipes
        create_sample_recipes()
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Database population completed!")
        print("\n📋 Login Credentials:")
        print("Admin: username='admin', password='admin123'")
        print("User: username='user', password='user123'")
        print("\n🎤 Voice Commands to try:")
        print("- 'Start recipe for butter chicken'")
        print("- 'What are the ingredients?'")
        print("- 'Set timer for 5 minutes'")
        print("- 'Next step'")
        print("- 'Show vegetarian recipes'")

if __name__ == '__main__':
    main() 
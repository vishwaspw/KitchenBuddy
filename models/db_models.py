from flask_login import UserMixin
from datetime import datetime
from models import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Voice assistant preferences
    voice_enabled = db.Column(db.Boolean, default=True)
    dietary_preferences = db.Column(db.String(200))  # e.g., "vegan,gluten-free"
    voice_speed = db.Column(db.Float, default=1.0)
    
    # Relationships
    recipes = db.relationship('Recipe', backref='user', lazy=True)
    cooking_sessions = db.relationship('CookingSession', backref='user', lazy=True)
    ingredient_inventory = db.relationship('IngredientInventory', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    dietary_tags = db.Column(db.String(200))  # e.g., "vegetarian,gluten-free"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Voice assistant fields
    cooking_time = db.Column(db.Integer)  # in minutes
    difficulty_level = db.Column(db.String(20))  # easy, medium, hard
    voice_description = db.Column(db.Text)  # AI-generated description for voice
    
    # Relationships
    steps = db.relationship('Step', backref='recipe', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Recipe {self.title}>'

class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    instruction = db.Column(db.Text, nullable=False)
    
    # Voice assistant fields
    estimated_time = db.Column(db.Integer)  # in minutes
    voice_instruction = db.Column(db.Text)  # AI-enhanced instruction for voice
    
    def __repr__(self):
        return f'<Step {self.step_number} for Recipe {self.recipe_id}>'

class CookingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    current_step = db.Column(db.Integer, default=1)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    completed_at = db.Column(db.DateTime)
    
    # Voice assistant fields
    voice_enabled = db.Column(db.Boolean, default=True)
    auto_read_steps = db.Column(db.Boolean, default=True)
    
    # Relationships
    recipe = db.relationship('Recipe', backref='cooking_sessions')
    
    def __repr__(self):
        return f'<CookingSession {self.user_id} - {self.recipe_id}>'

class IngredientInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ingredient_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50))  # e.g., "2 cups", "500g"
    unit = db.Column(db.String(20))  # e.g., "cups", "grams", "pieces"
    category = db.Column(db.String(50))  # e.g., "vegetables", "dairy", "spices"
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<IngredientInventory {self.ingredient_name} for User {self.user_id}>'

class VoiceCommand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    command_text = db.Column(db.Text, nullable=False)
    intent_detected = db.Column(db.String(100))
    response_generated = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<VoiceCommand {self.intent_detected} for User {self.user_id}>' 
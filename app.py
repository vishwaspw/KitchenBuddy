from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json

app = Flask(__name__)
print("DEBUG: app type is", type(app))

# Production configuration
if os.environ.get('FLASK_ENV') == 'production':
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///kitchenbuddy.db')
else:
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kitchenbuddy.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all()

# THEN define routes here
@app.route("/")
def index():
    return "Hello, KitchenBuddy!"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models after db initialization
from models.db_models import User, Recipe, Step, VoiceCommand, CookingSession

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize voice assistant components
try:
    from voice_assistant.speech_to_text import SpeechToText
    from voice_assistant.intent_detector import IntentDetector
    from voice_assistant.text_to_speech import TextToSpeech
    from voice_assistant.ai_response import AIResponseGenerator
    from voice_assistant.timer_manager import timer_manager
    
    speech_to_text = SpeechToText()
    intent_detector = IntentDetector()
    text_to_speech = TextToSpeech()
    ai_generator = AIResponseGenerator()
except ImportError as e:
    print(f"Voice assistant modules not available: {e}. Voice features will be disabled.")
    speech_to_text = None
    intent_detector = None
    text_to_speech = None
    ai_generator = None
    timer_manager = None

@app.route('/')
def index():
    """Home page with featured recipes"""
    featured_recipes = Recipe.query.limit(6).all()
    return render_template('index.html', recipes=featured_recipes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with saved recipes and cooking history"""
    user_recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    all_recipes = Recipe.query.all()
    return render_template('dashboard.html', user_recipes=user_recipes, all_recipes=all_recipes)

@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id):
    """Display individual recipe with cooking steps"""
    recipe = Recipe.query.get_or_404(recipe_id)
    steps = Step.query.filter_by(recipe_id=recipe_id).order_by(Step.step_number).all()
    return render_template('recipe.html', recipe=recipe, steps=steps)

@app.route('/admin_panel')
@login_required
def admin_panel():
    """Admin panel for managing recipes"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    recipes = Recipe.query.all()
    return render_template('admin_panel.html', recipes=recipes)

@app.route('/admin/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    """Add new recipe (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        ingredients = request.form['ingredients']
        dietary_tags = request.form['dietary_tags']
        steps_data = request.form.getlist('steps[]')
        
        # Create recipe
        recipe = Recipe(
            title=title,
            category=category,
            ingredients=ingredients,
            dietary_tags=dietary_tags,
            user_id=current_user.id
        )
        db.session.add(recipe)
        db.session.flush()  # Get the recipe ID
        
        # Add steps
        for i, step_text in enumerate(steps_data, 1):
            if step_text.strip():
                step = Step(
                    recipe_id=recipe.id,
                    step_number=i,
                    instruction=step_text.strip()
                )
                db.session.add(step)
        
        db.session.commit()
        flash('Recipe added successfully!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('add_recipe.html')

@app.route('/admin/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    """Edit existing recipe (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    recipe = Recipe.query.get_or_404(recipe_id)
    steps = Step.query.filter_by(recipe_id=recipe_id).order_by(Step.step_number).all()
    
    if request.method == 'POST':
        recipe.title = request.form['title']
        recipe.category = request.form['category']
        recipe.ingredients = request.form['ingredients']
        recipe.dietary_tags = request.form['dietary_tags']
        
        # Delete existing steps
        Step.query.filter_by(recipe_id=recipe_id).delete()
        
        # Add new steps
        steps_data = request.form.getlist('steps[]')
        for i, step_text in enumerate(steps_data, 1):
            if step_text.strip():
                step = Step(
                    recipe_id=recipe_id,
                    step_number=i,
                    instruction=step_text.strip()
                )
                db.session.add(step)
        
        db.session.commit()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('edit_recipe.html', recipe=recipe, steps=steps)

@app.route('/admin/delete_recipe/<int:recipe_id>')
@login_required
def delete_recipe(recipe_id):
    """Delete recipe (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    recipe = Recipe.query.get_or_404(recipe_id)
    Step.query.filter_by(recipe_id=recipe_id).delete()
    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe deleted successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/search')
def search():
    """Search recipes by title or category"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    recipes = Recipe.query
    
    if query:
        recipes = recipes.filter(Recipe.title.contains(query))
    if category:
        recipes = recipes.filter(Recipe.category == category)
    
    recipes = recipes.all()
    return render_template('search_results.html', recipes=recipes, query=query, category=category)

@app.route('/recipe/<int:recipe_id>/step/<int:step_number>')
@login_required
def recipe_step(recipe_id, step_number):
    """Display a specific step of a recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    steps = Step.query.filter_by(recipe_id=recipe_id).order_by(Step.step_number).all()
    
    if not steps or step_number < 1 or step_number > len(steps):
        flash('Invalid step number', 'error')
        return redirect(url_for('recipe', recipe_id=recipe_id))
    
    current_step = steps[step_number - 1]
    total_steps = len(steps)
    
    # Update session with current cooking state
    session['current_recipe_id'] = recipe_id
    session['current_step'] = step_number
    
    return render_template('recipe_step.html', 
                         recipe=recipe, 
                         current_step=current_step,
                         step_number=step_number,
                         total_steps=total_steps,
                         steps=steps)

@app.route('/recipe/<int:recipe_id>/next_step')
@login_required
def next_step(recipe_id):
    """Navigate to next step"""
    current_step = session.get('current_step', 1)
    steps = Step.query.filter_by(recipe_id=recipe_id).order_by(Step.step_number).all()
    
    if current_step < len(steps):
        return redirect(url_for('recipe_step', recipe_id=recipe_id, step_number=current_step + 1))
    else:
        flash('Recipe completed! Great job!', 'success')
        return redirect(url_for('recipe', recipe_id=recipe_id))

@app.route('/recipe/<int:recipe_id>/prev_step')
@login_required
def prev_step(recipe_id):
    """Navigate to previous step"""
    current_step = session.get('current_step', 1)
    
    if current_step > 1:
        return redirect(url_for('recipe_step', recipe_id=recipe_id, step_number=current_step - 1))
    else:
        return redirect(url_for('recipe_step', recipe_id=recipe_id, step_number=1))

@app.route('/recipe/<int:recipe_id>/step/<int:step_number>/timer/<int:minutes>')
@login_required
def start_timer(recipe_id, step_number, minutes):
    """Start a timer for a specific step"""
    session['timer_minutes'] = minutes
    session['timer_start_time'] = datetime.utcnow().isoformat()
    flash(f'Timer started for {minutes} minutes', 'info')
    return redirect(url_for('recipe_step', recipe_id=recipe_id, step_number=step_number))

@app.route('/transcribe', methods=['POST'])
@login_required
def transcribe_audio():
    """Handle voice transcription and intent detection"""
    if not speech_to_text or not intent_detector:
        return jsonify({'error': 'Voice assistant not available'}), 503
    
    try:
        # Get audio file from request
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({'error': 'No audio file provided'}), 400
        
        # Convert speech to text
        text = speech_to_text.convert_speech_to_text(audio_file)
        if not text:
            return jsonify({'error': 'Could not convert speech to text'}), 400
        
        # Detect intent
        intent = intent_detector.detect_intent(text)
        
        # Log voice command
        voice_command = VoiceCommand(
            user_id=current_user.id,
            command_text=text,
            intent_detected=intent
        )
        db.session.add(voice_command)
        db.session.commit()
        
        # Get current recipe context from session
        current_recipe_id = session.get('current_recipe_id')
        current_step = session.get('current_step', 1)
        
        # Handle different intents
        response_data = handle_voice_intent(intent, text, current_recipe_id, current_step)
        
        # Update voice command with response
        voice_command.response_generated = response_data.get('message', '')
        voice_command.success = response_data.get('success', False)
        db.session.commit()
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_voice_intent(intent, text, current_recipe_id, current_step):
    """Handle different voice intents and return appropriate responses"""
    
    if intent == 'start_recipe':
        # Extract recipe name and find it
        recipe_name = intent_detector.extract_recipe_name(text)
        if recipe_name:
            recipe = intent_detector.find_recipe_by_name(recipe_name)
            if recipe:
                # Create cooking session
                cooking_session = CookingSession(
                    user_id=current_user.id,
                    recipe_id=recipe.id,
                    current_step=1
                )
                db.session.add(cooking_session)
                db.session.commit()
                
                # Speak confirmation
                if text_to_speech:
                    text_to_speech.speak_text(f"Great! Let's start cooking {recipe.title}. I'll guide you through each step.")
                
                return {
                    'success': True,
                    'text': text,
                    'intent': intent,
                    'redirect_url': url_for('recipe_step', recipe_id=recipe.id, step_number=1),
                    'message': f"Starting recipe: {recipe.title}"
                }
            else:
                message = f"I couldn't find a recipe for {recipe_name}. Please try again or search for available recipes."
                if text_to_speech:
                    text_to_speech.speak_text(message)
                return {
                    'success': False,
                    'text': text,
                    'intent': intent,
                    'message': message
                }
        else:
            message = "Please specify which recipe you'd like to cook. For example, 'Start recipe for butter chicken'."
            if text_to_speech:
                text_to_speech.speak_text(message)
            return {
                'success': False,
                'text': text,
                'intent': intent,
                'message': message
            }
    
    elif intent == 'next_step' and current_recipe_id:
        if text_to_speech:
            text_to_speech.speak_text("Moving to the next step.")
        return {
            'success': True,
            'text': text,
            'intent': intent,
            'redirect_url': url_for('next_step', recipe_id=current_recipe_id)
        }
    
    elif intent == 'prev_step' and current_recipe_id:
        if text_to_speech:
            text_to_speech.speak_text("Going back to the previous step.")
        return {
            'success': True,
            'text': text,
            'intent': intent,
            'redirect_url': url_for('prev_step', recipe_id=current_recipe_id)
        }
    
    elif intent == 'repeat_step' and current_recipe_id:
        if text_to_speech:
            text_to_speech.speak_text("I'll repeat the current step for you.")
        return {
            'success': True,
            'text': text,
            'intent': intent,
            'redirect_url': url_for('recipe_step', recipe_id=current_recipe_id, step_number=current_step)
        }
    
    elif intent == 'current_step' and current_recipe_id:
        recipe = Recipe.query.get(current_recipe_id)
        current_step_obj = Step.query.filter_by(recipe_id=current_recipe_id, step_number=current_step).first()
        if current_step_obj and text_to_speech:
            text_to_speech.speak_text(f"You're on step {current_step}: {current_step_obj.instruction}")
        return {
            'success': True,
            'text': text,
            'intent': intent,
            'message': f"Current step: {current_step}"
        }
    
    elif intent == 'set_timer':
        minutes = intent_detector.extract_timer_duration(text)
        if current_recipe_id:
            if text_to_speech:
                text_to_speech.speak_text(f"Setting timer for {minutes} minutes.")
            return {
                'success': True,
                'text': text,
                'intent': intent,
                'redirect_url': url_for('start_timer', recipe_id=current_recipe_id, step_number=current_step, minutes=minutes)
            }
        else:
            message = "Please start a recipe first before setting a timer."
            if text_to_speech:
                text_to_speech.speak_text(message)
            return {
                'success': False,
                'text': text,
                'intent': intent,
                'message': message
            }
    
    elif intent == 'ingredients_query' and current_recipe_id:
        recipe = Recipe.query.get(current_recipe_id)
        if recipe and ai_generator:
            ingredient_text = ai_generator.generate_ingredient_list(recipe.ingredients)
            if text_to_speech:
                text_to_speech.speak_text(ingredient_text)
            return {
                'success': True,
                'text': text,
                'intent': intent,
                'message': ingredient_text
            }
        else:
            message = "I couldn't find the recipe ingredients. Please try again."
            if text_to_speech:
                text_to_speech.speak_text(message)
            return {
                'success': False,
                'text': text,
                'intent': intent,
                'message': message
            }
    
    elif intent == 'dietary_filter':
        preference = intent_detector.extract_dietary_preference(text)
        if preference:
            message = f"Showing {preference} recipes for you."
            if text_to_speech:
                text_to_speech.speak_text(message)
            return {
                'success': True,
                'text': text,
                'intent': intent,
                'redirect_url': url_for('search', dietary=preference),
                'message': message
            }
        else:
            message = "Please specify a dietary preference like vegan, vegetarian, or gluten-free."
            if text_to_speech:
                text_to_speech.speak_text(message)
            return {
                'success': False,
                'text': text,
                'intent': intent,
                'message': message
            }
    
    elif intent == 'ai_query':
        if ai_generator:
            response = ai_generator.generate_response(text, {
                'user_id': current_user.id,
                'current_recipe_id': current_recipe_id,
                'current_step': current_step
            })
            if text_to_speech:
                text_to_speech.speak_text(response)
            return {
                'success': True,
                'text': text,
                'intent': intent,
                'message': response
            }
        else:
            message = "I'm sorry, I can't process that query right now. Please try a different command."
            if text_to_speech:
                text_to_speech.speak_text(message)
            return {
                'success': False,
                'text': text,
                'intent': intent,
                'message': message
            }
    
    elif intent == 'resume_cooking':
        active_session = CookingSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if active_session:
            recipe = Recipe.query.get(active_session.recipe_id)
            if text_to_speech:
                text_to_speech.speak_text(f"Resuming {recipe.title} from step {active_session.current_step}.")
            return {
                'success': True,
                'text': text,
                'intent': intent,
                'redirect_url': url_for('recipe_step', recipe_id=active_session.recipe_id, step_number=active_session.current_step),
                'message': f"Resuming {recipe.title}"
            }
        else:
            message = "You don't have any active cooking sessions to resume."
            if text_to_speech:
                text_to_speech.speak_text(message)
            return {
                'success': False,
                'text': text,
                'intent': intent,
                'message': message
            }
    
    elif intent == 'stop_cooking':
        # End active cooking session
        active_session = CookingSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if active_session:
            active_session.is_active = False
            active_session.completed_at = datetime.utcnow()
            db.session.commit()
        
        session.pop('current_recipe_id', None)
        session.pop('current_step', None)
        
        if text_to_speech:
            text_to_speech.speak_text("Cooking session ended. You can start a new recipe anytime.")
        
        return {
            'success': True,
            'text': text,
            'intent': intent,
            'redirect_url': url_for('dashboard'),
            'message': "Cooking session ended"
        }
    
    elif intent == 'help':
        help_message = """Here are some voice commands you can use:
        - "Start recipe for [recipe name]" to begin cooking
        - "Next step" or "Previous step" to navigate
        - "Repeat step" to hear the current instruction again
        - "Set timer for [time]" to start a cooking timer
        - "What are the ingredients?" to hear the ingredient list
        - "Show vegan recipes" to filter by dietary preference
        - "Stop cooking" to end the current session"""
        
        if text_to_speech:
            text_to_speech.speak_text("I'll help you with cooking commands. You can ask me to start recipes, navigate steps, set timers, and more.")
        
        return {
            'success': True,
            'text': text,
            'intent': intent,
            'message': help_message
        }
    
    else:
        message = "I didn't understand that command. Try saying 'help' to learn what I can do."
        if text_to_speech:
            text_to_speech.speak_text(message)
        return {
            'success': False,
            'text': text,
            'intent': intent,
            'message': message
        }

@app.route('/stop_timer/<timer_id>')
@login_required
def stop_timer(timer_id):
    """Stop a specific timer"""
    if timer_manager:
        success = timer_manager.stop_timer(timer_id)
        if success:
            flash('Timer stopped', 'info')
        else:
            flash('Timer not found', 'error')
    
    return jsonify({'success': success if timer_manager else False})

@app.route('/timer_status/<timer_id>')
@login_required
def timer_status(timer_id):
    """Get status of a timer"""
    if timer_manager:
        status = timer_manager.get_timer_status(timer_id)
        if status:
            return jsonify({
                'active': status['is_active'],
                'remaining': timer_manager.get_remaining_time(timer_id),
                'duration': status['duration_minutes']
            })
    
    return jsonify({'active': False})

@app.route('/voice_only')
@login_required
def voice_only_mode():
    """Voice-only interface for hands-free cooking"""
    active_session = CookingSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    return render_template('voice_only.html', active_session=active_session)

@app.route('/api/voice_status')
@login_required
def voice_status():
    """Get current voice assistant status"""
    return jsonify({
        'voice_enabled': speech_to_text is not None,
        'tts_enabled': text_to_speech is not None,
        'ai_enabled': ai_generator is not None,
        'timer_enabled': timer_manager is not None,
        'active_timers': timer_manager.get_timer_count() if timer_manager else 0
    })

@app.route('/ai_query', methods=['POST'])
@login_required
def ai_query():
    """Handle AI queries from the voice-only interface"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', 'general')
        
        if not query:
            return jsonify({
                'success': False,
                'response': 'Please provide a query.'
            })
        
        # Get current cooking session for context
        active_session = CookingSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        context_data = {
            'user_id': current_user.id,
            'current_recipe_id': active_session.recipe_id if active_session else None,
            'current_step': active_session.current_step if active_session else None,
            'context': context
        }
        
        if ai_generator:
            response = ai_generator.generate_response(query, context_data)
            return jsonify({
                'success': True,
                'response': response
            })
        else:
            return jsonify({
                'success': False,
                'response': "I'm sorry, I can't process that query right now. Please try a different command."
            })
    
    except Exception as e:
        print(f"Error in AI query: {e}")
        return jsonify({
            'success': False,
            'response': 'An error occurred while processing your query.'
        })

@app.route('/voice_command', methods=['POST'])
@login_required
def voice_command():
    """Handle voice commands from the voice-only interface"""
    try:
        data = request.get_json()
        command = data.get('command', '').lower()
        
        # Get current cooking session
        active_session = CookingSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not active_session:
            return jsonify({
                'success': False,
                'message': 'No active cooking session. Please start a recipe first.'
            })
        
        recipe = Recipe.query.get(active_session.recipe_id)
        if not recipe:
            return jsonify({
                'success': False,
                'message': 'Recipe not found.'
            })
        
        current_step = active_session.current_step
        total_steps = len(recipe.steps)
        
        if command == 'next_step':
            if current_step < total_steps:
                active_session.current_step += 1
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'Moving to step {active_session.current_step} of {recipe.title}',
                    'redirect_url': url_for('recipe_step', recipe_id=recipe.id, step_number=active_session.current_step)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'You are already at the last step of this recipe.'
                })
        
        elif command == 'previous_step':
            if current_step > 1:
                active_session.current_step -= 1
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'Moving to step {active_session.current_step} of {recipe.title}',
                    'redirect_url': url_for('recipe_step', recipe_id=recipe.id, step_number=active_session.current_step)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'You are already at the first step of this recipe.'
                })
        
        elif command == 'repeat_step':
            current_step_obj = recipe.steps[current_step - 1] if recipe.steps else None
            if current_step_obj:
                return jsonify({
                    'success': True,
                    'message': f'Step {current_step}: {current_step_obj.instruction}'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Step not found.'
                })
        
        elif command == 'show_ingredients':
            return jsonify({
                'success': True,
                'message': f'Ingredients for {recipe.title}: {recipe.ingredients}'
            })
        
        elif command == 'set_timer':
            return jsonify({
                'success': True,
                'message': 'Please specify the timer duration. You can say "set timer for 5 minutes" or use the timer buttons.'
            })
        
        elif command == 'stop_cooking':
            active_session.is_active = False
            active_session.completed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Cooking session ended. You can start a new recipe anytime.',
                'redirect_url': url_for('dashboard')
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown command: {command}. Try saying "help" for available commands.'
            })
    
    except Exception as e:
        print(f"Error in voice command: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your command.'
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True) 

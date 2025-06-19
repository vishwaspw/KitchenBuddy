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
@app.route('/')
def index():
    """Home page with featured recipes"""
    featured_recipes = Recipe.query.limit(6).all()
    return render_template('index.html', recipes=featured_recipes)

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

    # Timer session variables
    timer_minutes = session.get('timer_minutes')
    timer_start_time = session.get('timer_start_time')

    # Update session with current cooking state
    session['current_recipe_id'] = recipe_id
    session['current_step'] = step_number
    
    return render_template('recipe_step.html', 
                         recipe=recipe, 
                         current_step=current_step,
                         step_number=step_number,
                         total_steps=total_steps,
                         timer_minutes=timer_minutes,
                         timer_start_time=timer_start_time)

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

@app.route('/populate_all')
def populate_all():
    from models.db_models import User, Recipe, Step
    from werkzeug.security import generate_password_hash
    db.create_all()
    # Ensure permanent admin user
    admin = User.query.filter_by(username='Vishwas').first()
    if not admin:
        admin = User(
            username='Vishwas',
            email='vishwas@example.com',
            password_hash=generate_password_hash('Vish@1kb'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    else:
        admin.password_hash = generate_password_hash('Vish@1kb')
        admin.is_admin = True
        db.session.commit()

    # Populate sample recipes if none exist
    if Recipe.query.count() == 0:
        recipes_data = [
            {
                'title': 'Butter Chicken',
                'category': 'Main Course',
                'ingredients': '''500g chicken breast, cubed\n1 cup yogurt\n2 tbsp tandoori masala\n2 tbsp butter\n1 cup tomato puree\n1/2 cup cream\n1 tbsp kasoori methi\n1 tsp garam masala\n1 tsp red chili powder\n1 tbsp ginger-garlic paste\nSalt to taste''',
                'dietary_tags': 'non-vegetarian,gluten-free,creamy',
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
                'ingredients': '''2 tbsp vegetable oil\n2 cloves garlic, minced\n1 inch ginger, minced\n2 bell peppers, sliced\n1 cup broccoli florets\n1 cup snap peas\n2 carrots, julienned\n2 tbsp soy sauce\n1 tbsp oyster sauce\n1 tsp cornstarch\n1/4 cup water\nSalt and pepper to taste''',
                'dietary_tags': 'vegetarian,vegan,gluten-free',
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
                'ingredients': '''2 1/4 cups all-purpose flour\n1 tsp baking soda\n1 tsp salt\n1 cup unsalted butter, softened\n3/4 cup granulated sugar\n3/4 cup brown sugar\n2 large eggs\n2 tsp vanilla extract\n2 cups chocolate chips''',
                'dietary_tags': 'vegetarian,contains-dairy',
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
                'ingredients': '''1 large cucumber, diced\n4 large tomatoes, diced\n1 red onion, thinly sliced\n1 cup Kalamata olives\n200g feta cheese, cubed\n2 tbsp extra virgin olive oil\n1 tbsp red wine vinegar\n1 tsp dried oregano\nSalt and pepper to taste''',
                'dietary_tags': 'vegetarian,gluten-free',
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
                'ingredients': '''2 slices whole grain bread\n1 ripe avocado\n1 lemon\nSalt and pepper to taste\nRed pepper flakes (optional)\nMicrogreens or sprouts (optional)''',
                'dietary_tags': 'vegetarian,vegan,gluten-free',
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
            },
            {
                'title': 'Spaghetti Carbonara',
                'category': 'Main Course',
                'ingredients': '''200g spaghetti\n100g pancetta\n2 large eggs\n50g pecorino cheese\n50g parmesan\n2 cloves garlic, peeled\nSalt and black pepper to taste''',
                'dietary_tags': 'non-vegetarian,contains-dairy',
                'steps': [
                    'Cook spaghetti in salted boiling water until al dente.',
                    'Fry pancetta with garlic until crisp, then remove garlic.',
                    'Beat eggs and mix with grated cheeses.',
                    'Drain pasta and combine with pancetta.',
                    'Remove from heat, add egg and cheese mixture, and toss quickly.',
                    'Season with salt and pepper, serve immediately.'
                ]
            },
            {
                'title': 'Margherita Pizza',
                'category': 'Main Course',
                'ingredients': '''1 pizza dough base\n100g tomato sauce\n125g mozzarella cheese\nFresh basil leaves\n2 tbsp olive oil\nSalt to taste''',
                'dietary_tags': 'vegetarian,contains-dairy',
                'steps': [
                    'Preheat oven to 250°C (480°F).',
                    'Spread tomato sauce over the pizza base.',
                    'Add sliced mozzarella and drizzle with olive oil.',
                    'Bake for 10-12 minutes until crust is golden.',
                    'Top with fresh basil leaves and serve hot.'
                ]
            },
            {
                'title': 'Pancakes',
                'category': 'Breakfast',
                'ingredients': '''1 cup all-purpose flour\n2 tbsp sugar\n2 tsp baking powder\nPinch of salt\n1 cup milk\n1 egg\n2 tbsp melted butter\nMaple syrup to serve''',
                'dietary_tags': 'vegetarian,contains-dairy',
                'steps': [
                    'Mix flour, sugar, baking powder, and salt in a bowl.',
                    'Whisk milk, egg, and melted butter in another bowl.',
                    'Combine wet and dry ingredients until just mixed.',
                    'Heat a non-stick pan and pour batter to form pancakes.',
                    'Cook until bubbles form, flip and cook until golden.',
                    'Serve warm with maple syrup.'
                ]
            },
            {
                'title': 'Chicken Caesar Salad',
                'category': 'Salad',
                'ingredients': '''2 chicken breasts\n1 romaine lettuce\n50g parmesan cheese\n1 cup croutons\nCaesar dressing\nSalt and pepper to taste''',
                'dietary_tags': 'non-vegetarian,contains-dairy',
                'steps': [
                    'Season and grill chicken breasts, then slice.',
                    'Chop romaine lettuce and place in a bowl.',
                    'Add sliced chicken, croutons, and shaved parmesan.',
                    'Drizzle with Caesar dressing and toss gently.',
                    'Serve immediately.'
                ]
            },
            {
                'title': 'Tacos',
                'category': 'Main Course',
                'ingredients': '''8 small tortillas\n250g ground beef or chicken\n1 onion, chopped\n1 tomato, diced\nLettuce, shredded\nCheddar cheese, grated\nTaco seasoning\nSour cream and salsa to serve''',
                'dietary_tags': 'non-vegetarian,contains-dairy',
                'steps': [
                    'Cook ground meat with taco seasoning and chopped onion.',
                    'Warm tortillas in a pan.',
                    'Fill tortillas with meat, lettuce, tomato, and cheese.',
                    'Top with sour cream and salsa.',
                    'Serve immediately.'
                ]
            },
            {
                'title': 'Palak Paneer',
                'category': 'Main Course',
                'ingredients': '''200g paneer\n300g spinach\n2 onions\n2 tomatoes\n2 green chilies\n1 tsp ginger-garlic paste\n1 tsp cumin seeds\n1 tsp garam masala\nSalt to taste''',
                'dietary_tags': 'vegetarian,gluten-free',
                'steps': [
                    'Blanch spinach and blend to a puree.',
                    'Fry cumin seeds, onions, and ginger-garlic paste.',
                    'Add tomatoes and cook until soft.',
                    'Add spinach puree and spices, cook for 5 minutes.',
                    'Add paneer cubes and simmer for 5 minutes.',
                    'Serve hot with naan or rice.'
                ]
            },
            {
                'title': 'Beef Stroganoff',
                'category': 'Main Course',
                'ingredients': '''500g beef sirloin\n1 onion\n200g mushrooms\n1 cup sour cream\n2 tbsp flour\n2 tbsp butter\n1 cup beef broth\nSalt and pepper to taste''',
                'dietary_tags': 'non-vegetarian,contains-dairy',
                'steps': [
                    'Slice beef and brown in butter.',
                    'Remove beef, sauté onions and mushrooms.',
                    'Add flour, then beef broth, and simmer.',
                    'Return beef to pan, stir in sour cream.',
                    'Simmer until thickened, serve over noodles.'
                ]
            },
            {
                'title': 'Miso Soup',
                'category': 'Soup',
                'ingredients': '''4 cups dashi stock\n3 tbsp miso paste\n100g tofu\n2 green onions\n1 sheet nori''',
                'dietary_tags': 'vegetarian,gluten-free',
                'steps': [
                    'Heat dashi stock to a simmer.',
                    'Add tofu cubes and sliced green onions.',
                    'Dissolve miso paste in a little hot broth, then add to pot.',
                    'Add nori strips, simmer 2 minutes, serve hot.'
                ]
            },
            {
                'title': 'Fish Tacos',
                'category': 'Main Course',
                'ingredients': '''300g white fish fillets\n8 small tortillas\n1 cup cabbage, shredded\n1 tomato, diced\n1/2 cup sour cream\n1 lime\nTaco seasoning\nSalt and pepper to taste''',
                'dietary_tags': 'non-vegetarian',
                'steps': [
                    'Season fish with taco seasoning, salt, and pepper.',
                    'Grill or pan-fry fish until cooked through.',
                    'Warm tortillas, fill with fish, cabbage, and tomato.',
                    'Top with sour cream and a squeeze of lime.'
                ]
            },
            {
                'title': 'Banana Bread',
                'category': 'Dessert',
                'ingredients': '''2 cups all-purpose flour\n1 tsp baking soda\n1/4 tsp salt\n1/2 cup butter\n3/4 cup brown sugar\n2 eggs\n2 1/3 cups mashed bananas''',
                'dietary_tags': 'vegetarian,contains-dairy',
                'steps': [
                    'Preheat oven to 175°C (350°F).',
                    'Mix flour, baking soda, and salt.',
                    'Cream butter and sugar, add eggs and bananas.',
                    'Combine wet and dry ingredients.',
                    'Pour into greased loaf pan and bake 60 minutes.'
                ]
            },
            {
                'title': 'Shakshuka',
                'category': 'Breakfast',
                'ingredients': '''4 eggs\n1 onion\n1 bell pepper\n2 cloves garlic\n400g canned tomatoes\n1 tsp cumin\n1 tsp paprika\nSalt and pepper to taste''',
                'dietary_tags': 'vegetarian,gluten-free',
                'steps': [
                    'Sauté onion, bell pepper, and garlic.',
                    'Add tomatoes and spices, simmer 10 minutes.',
                    'Make wells and crack eggs into sauce.',
                    'Cover and cook until eggs are set.',
                    'Serve with bread.'
                ]
            },
            {
                'title': 'Egg Fried Rice',
                'category': 'Main Course',
                'ingredients': '''2 cups cooked rice\n2 eggs\n1 cup mixed vegetables\n2 tbsp soy sauce\n2 green onions\n1 tbsp oil\nSalt and pepper to taste''',
                'dietary_tags': 'vegetarian',
                'steps': [
                    'Heat oil in a wok, scramble eggs and set aside.',
                    'Sauté vegetables, add rice and soy sauce.',
                    'Add eggs back, toss with green onions.',
                    'Season and serve hot.'
                ]
            },
            {
                'title': 'Lemon Garlic Salmon',
                'category': 'Main Course',
                'ingredients': '''2 salmon fillets\n2 tbsp lemon juice\n2 cloves garlic, minced\n1 tbsp olive oil\nSalt and pepper to taste''',
                'dietary_tags': 'non-vegetarian,gluten-free',
                'steps': [
                    'Marinate salmon with lemon juice, garlic, salt, and pepper.',
                    'Pan-sear or bake until cooked through.',
                    'Serve with vegetables or rice.'
                ]
            },
            {
                'title': 'French Toast',
                'category': 'Breakfast',
                'ingredients': '''4 slices bread\n2 eggs\n1/2 cup milk\n1 tsp cinnamon\n1 tsp vanilla extract\nButter for frying\nMaple syrup to serve''',
                'dietary_tags': 'vegetarian,contains-dairy',
                'steps': [
                    'Whisk eggs, milk, cinnamon, and vanilla.',
                    'Dip bread slices in mixture.',
                    'Fry in butter until golden on both sides.',
                    'Serve with maple syrup.'
                ]
            },
            {
                'title': 'Quinoa Salad',
                'category': 'Salad',
                'ingredients': '''1 cup quinoa\n2 cups water\n1 cucumber, diced\n1 bell pepper, diced\n1/2 cup cherry tomatoes\n1/4 cup olive oil\n2 tbsp lemon juice\nSalt and pepper to taste''',
                'dietary_tags': 'vegan,gluten-free,healthy',
                'steps': [
                    'Cook quinoa in water until fluffy.',
                    'Mix with vegetables in a bowl.',
                    'Whisk olive oil and lemon juice, pour over salad.',
                    'Toss and season to taste.'
                ]
            }
        ]
        for r in recipes_data:
            recipe = Recipe(
                title=r['title'],
                category=r['category'],
                ingredients=r['ingredients'],
                dietary_tags=r['dietary_tags'],
                user_id=admin.id
            )
            db.session.add(recipe)
            db.session.flush()
            for i, step_text in enumerate(r['steps'], 1):
                step = Step(
                    recipe_id=recipe.id,
                    step_number=i,
                    instruction=step_text
                )
                db.session.add(step)
        db.session.commit()
    return "Admin and sample recipes populated!"

@app.route('/populate_db')
def populate_db_route():
    import populate_db
    from models.db_models import Recipe
    return f"Database populated! Recipe count: {Recipe.query.count()}"

@app.route('/create_admin')
def create_admin():
    from models.db_models import User
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(username='Vishwas').first()
    if not admin:
        admin = User(
            username='Vishwas',
            email='vishwas@example.com',
            password_hash=generate_password_hash('Vish@1kb'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    else:
        admin.password_hash = generate_password_hash('Vish@1kb')
        admin.is_admin = True
        db.session.commit()
    return "Admin user now has username: Vishwas and password: Vish@1kb"

@app.route('/debug_users')
def debug_users():
    from models.db_models import User
    users = User.query.all()
    return "<br>".join([f"username: {u.username}, email: {u.email}, is_admin: {u.is_admin}" for u in users])

@app.route('/debug_recipes')
def debug_recipes():
    from models.db_models import Recipe
    recipes = Recipe.query.all()
    return "<br>".join([f"title: {r.title}" for r in recipes])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Ensure permanent admin user
        admin = User.query.filter_by(username='Vishwas').first()
        if not admin:
            admin = User(
                username='Vishwas',
                email='vishwas@example.com',
                password_hash=generate_password_hash('Vish@1kb'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        else:
            admin.password_hash = generate_password_hash('Vish@1kb')
            admin.is_admin = True
            db.session.commit()

        # Populate sample recipes if none exist
        if Recipe.query.count() == 0:
            recipes_data = [
                {
                    'title': 'Butter Chicken',
                    'category': 'Main Course',
                    'ingredients': '''500g chicken breast, cubed\n1 cup yogurt\n2 tbsp tandoori masala\n2 tbsp butter\n1 cup tomato puree\n1/2 cup cream\n1 tbsp kasoori methi\n1 tsp garam masala\n1 tsp red chili powder\n1 tbsp ginger-garlic paste\nSalt to taste''',
                    'dietary_tags': 'non-vegetarian,gluten-free,creamy',
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
                    'ingredients': '''2 tbsp vegetable oil\n2 cloves garlic, minced\n1 inch ginger, minced\n2 bell peppers, sliced\n1 cup broccoli florets\n1 cup snap peas\n2 carrots, julienned\n2 tbsp soy sauce\n1 tbsp oyster sauce\n1 tsp cornstarch\n1/4 cup water\nSalt and pepper to taste''',
                    'dietary_tags': 'vegetarian,vegan,gluten-free',
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
                    'ingredients': '''2 1/4 cups all-purpose flour\n1 tsp baking soda\n1 tsp salt\n1 cup unsalted butter, softened\n3/4 cup granulated sugar\n3/4 cup brown sugar\n2 large eggs\n2 tsp vanilla extract\n2 cups chocolate chips''',
                    'dietary_tags': 'vegetarian,contains-dairy',
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
                    'ingredients': '''1 large cucumber, diced\n4 large tomatoes, diced\n1 red onion, thinly sliced\n1 cup Kalamata olives\n200g feta cheese, cubed\n2 tbsp extra virgin olive oil\n1 tbsp red wine vinegar\n1 tsp dried oregano\nSalt and pepper to taste''',
                    'dietary_tags': 'vegetarian,gluten-free',
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
                    'ingredients': '''2 slices whole grain bread\n1 ripe avocado\n1 lemon\nSalt and pepper to taste\nRed pepper flakes (optional)\nMicrogreens or sprouts (optional)''',
                    'dietary_tags': 'vegetarian,vegan,gluten-free',
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
                },
                {
                    'title': 'Spaghetti Carbonara',
                    'category': 'Main Course',
                    'ingredients': '''200g spaghetti\n100g pancetta\n2 large eggs\n50g pecorino cheese\n50g parmesan\n2 cloves garlic, peeled\nSalt and black pepper to taste''',
                    'dietary_tags': 'non-vegetarian,contains-dairy',
                    'steps': [
                        'Cook spaghetti in salted boiling water until al dente.',
                        'Fry pancetta with garlic until crisp, then remove garlic.',
                        'Beat eggs and mix with grated cheeses.',
                        'Drain pasta and combine with pancetta.',
                        'Remove from heat, add egg and cheese mixture, and toss quickly.',
                        'Season with salt and pepper, serve immediately.'
                    ]
                },
                {
                    'title': 'Margherita Pizza',
                    'category': 'Main Course',
                    'ingredients': '''1 pizza dough base\n100g tomato sauce\n125g mozzarella cheese\nFresh basil leaves\n2 tbsp olive oil\nSalt to taste''',
                    'dietary_tags': 'vegetarian,contains-dairy',
                    'steps': [
                        'Preheat oven to 250°C (480°F).',
                        'Spread tomato sauce over the pizza base.',
                        'Add sliced mozzarella and drizzle with olive oil.',
                        'Bake for 10-12 minutes until crust is golden.',
                        'Top with fresh basil leaves and serve hot.'
                    ]
                },
                {
                    'title': 'Pancakes',
                    'category': 'Breakfast',
                    'ingredients': '''1 cup all-purpose flour\n2 tbsp sugar\n2 tsp baking powder\nPinch of salt\n1 cup milk\n1 egg\n2 tbsp melted butter\nMaple syrup to serve''',
                    'dietary_tags': 'vegetarian,contains-dairy',
                    'steps': [
                        'Mix flour, sugar, baking powder, and salt in a bowl.',
                        'Whisk milk, egg, and melted butter in another bowl.',
                        'Combine wet and dry ingredients until just mixed.',
                        'Heat a non-stick pan and pour batter to form pancakes.',
                        'Cook until bubbles form, flip and cook until golden.',
                        'Serve warm with maple syrup.'
                    ]
                },
                {
                    'title': 'Chicken Caesar Salad',
                    'category': 'Salad',
                    'ingredients': '''2 chicken breasts\n1 romaine lettuce\n50g parmesan cheese\n1 cup croutons\nCaesar dressing\nSalt and pepper to taste''',
                    'dietary_tags': 'non-vegetarian,contains-dairy',
                    'steps': [
                        'Season and grill chicken breasts, then slice.',
                        'Chop romaine lettuce and place in a bowl.',
                        'Add sliced chicken, croutons, and shaved parmesan.',
                        'Drizzle with Caesar dressing and toss gently.',
                        'Serve immediately.'
                    ]
                },
                {
                    'title': 'Tacos',
                    'category': 'Main Course',
                    'ingredients': '''8 small tortillas\n250g ground beef or chicken\n1 onion, chopped\n1 tomato, diced\nLettuce, shredded\nCheddar cheese, grated\nTaco seasoning\nSour cream and salsa to serve''',
                    'dietary_tags': 'non-vegetarian,contains-dairy',
                    'steps': [
                        'Cook ground meat with taco seasoning and chopped onion.',
                        'Warm tortillas in a pan.',
                        'Fill tortillas with meat, lettuce, tomato, and cheese.',
                        'Top with sour cream and salsa.',
                        'Serve immediately.'
                    ]
                }
            ]
            for r in recipes_data:
                recipe = Recipe(
                    title=r['title'],
                    category=r['category'],
                    ingredients=r['ingredients'],
                    dietary_tags=r['dietary_tags'],
                    user_id=admin.id
                )
                db.session.add(recipe)
                db.session.flush()
                for i, step_text in enumerate(r['steps'], 1):
                    step = Step(
                        recipe_id=recipe.id,
                        step_number=i,
                        instruction=step_text
                    )
                    db.session.add(step)
            db.session.commit()
    
    app.run(debug=True) 

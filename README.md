# 🍳 KitchenBuddy - Voice-Controlled Cooking Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Flask-based web application that provides hands-free cooking assistance through advanced voice commands and AI-powered responses.

## ✨ Features

### 🎤 Voice Assistant Features

#### 1. **Voice-Activated Recipe Opening**
- Say: "Start recipe for butter chicken"
- Uses fuzzy matching to find the closest recipe
- Automatically loads the recipe and starts reading Step 1 aloud

#### 2. **Smart Step Navigation**
- **"Next step"** - Move to the next cooking step
- **"Previous step"** - Go back to the previous step
- **"Repeat step"** - Hear the current instruction again
- **"What's the current step?"** - Get current step information
- Maintains cooking progress in user session

#### 3. **Voice-Based Ingredient Handling**
- **"What are the ingredients?"** - Hear the complete ingredient list
- **"Do I have all ingredients?"** - Interactive ingredient checking
- Generates downloadable shopping lists for missing ingredients

#### 4. **Cooking Timer Voice Assistant**
- **"Set timer for 5 minutes"** - Start a voice-controlled timer
- **"How much time is left?"** - Check timer status
- **"Stop timer"** - Cancel active timers
- Voice notifications when timer completes

#### 5. **Resume Recipe Progress**
- Automatically detects active cooking sessions
- Offers to resume cooking when user logs in
- Voice prompt: "Would you like to resume 'Dosa' from Step 3?"

#### 6. **Dietary Preference Filter (Voice)**
- **"Show only vegan recipes"**
- **"Find vegetarian dishes"**
- **"Gluten-free recipes"**
- Filters recipes by dietary tags

#### 7. **AI-Powered Voice Responses**
- **"What can I cook with potatoes?"**
- **"Can you suggest a quick dinner?"**
- **"Is this recipe healthy?"**
- **"How do I substitute butter?"**
- Uses OpenAI GPT-3.5 or local knowledge base for intelligent responses

#### 8. **Voice-Only UI Mode**
- Simplified interface for hands-free cooking
- Large, easy-to-tap buttons as fallback
- Real-time voice feedback
- Keyboard shortcuts (Spacebar to start/stop recording)

### 🔧 Technical Features

- **Speech-to-Text**: Google Speech Recognition with offline fallback
- **Text-to-Speech**: pyttsx3 (offline) and gTTS (online)
- **Intent Detection**: Advanced NLP with spaCy and regex patterns
- **Timer Management**: Background threads with voice notifications
- **Cooking Sessions**: Persistent cooking progress tracking
- **AI Integration**: OpenAI API with local fallback responses

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Microphone access
- Internet connection (for online features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd KitchenBuddy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install spaCy English model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Set up environment variables** (optional)
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

5. **Populate the database**
   ```bash
   python populate_db.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open: http://localhost:5000
   - Login: admin/admin123 or user/user123

## 🎤 Voice Commands Reference

### Recipe Management
- **"Start recipe for [recipe name]"** - Begin cooking a specific recipe
- **"Open recipe [name]"** - Alternative way to start a recipe
- **"Show me recipes"** - Browse available recipes

### Step Navigation
- **"Next step"** - Move to the next cooking step
- **"Previous step"** - Go back to the previous step
- **"Repeat step"** - Hear the current instruction again
- **"What step am I on?"** - Get current step information
- **"Current step"** - Alternative way to check current step

### Timer Commands
- **"Set timer for [X] minutes"** - Start a cooking timer
- **"Timer for [X] minutes"** - Alternative timer command
- **"How much time is left?"** - Check timer status
- **"Stop timer"** - Cancel active timers

### Ingredient Queries
- **"What are the ingredients?"** - Hear the ingredient list
- **"Ingredients list"** - Alternative way to get ingredients
- **"What do I need?"** - Get ingredient requirements

### Dietary Filters
- **"Show vegan recipes"** - Filter by vegan dietary preference
- **"Vegetarian dishes"** - Find vegetarian recipes
- **"Gluten-free recipes"** - Filter gluten-free options
- **"Healthy recipes"** - Find healthy cooking options

### AI Queries
- **"What can I cook with [ingredient]?"** - Get recipe suggestions
- **"Suggest a quick dinner"** - Get meal recommendations
- **"Is this recipe healthy?"** - Get nutrition information
- **"How do I substitute [ingredient]?"** - Get substitution advice
- **"Cooking tips"** - Get general cooking advice

### Session Management
- **"Stop cooking"** - End the current cooking session
- **"Resume cooking"** - Continue from where you left off
- **"Take a break"** - Pause cooking session
- **"End recipe"** - End the current recipe
- **"Quit cooking"** - End the current cooking session

### Help & Support
- **"Help"** - Get list of available commands
- **"What can you do?"** - Learn about voice assistant capabilities

## 🏗️ Architecture

### Backend Components

```
voice_assistant/
├── speech_to_text.py      # Speech recognition
├── text_to_speech.py      # Voice synthesis
├── intent_detector.py     # Command understanding
├── ai_response.py         # AI-powered responses
└── timer_manager.py       # Timer management
```

### Database Models

- **User**: User accounts with voice preferences
- **Recipe**: Recipe data with voice descriptions
- **Step**: Cooking steps with voice instructions
- **CookingSession**: Active cooking sessions
- **IngredientInventory**: User's ingredient tracking
- **VoiceCommand**: Voice command history

### Frontend Components

- **Voice-Only Mode**: Simplified hands-free interface
- **Recipe Step View**: Enhanced with voice controls
- **Dashboard**: Voice assistant integration
- **Timer Display**: Real-time timer updates

## 🔧 Configuration

### Voice Assistant Settings

```python
# In app.py
app.config['VOICE_ENABLED'] = True
app.config['TTS_ENGINE'] = 'pyttsx3'  # or 'gtts'
app.config['STT_ENGINE'] = 'google'   # or 'sphinx'
```

### AI Integration

```python
# Set OpenAI API key in .env file
OPENAI_API_KEY=your_api_key_here
```

## 🧪 Testing Voice Commands

1. **Start the application**
2. **Login with admin/admin123**
3. **Navigate to Voice-Only Mode** or use the voice button
4. **Try these test commands**:
   - "Start recipe for butter chicken"
   - "What are the ingredients?"
   - "Set timer for 3 minutes"
   - "Next step"
   - "Show vegetarian recipes"

## 🐛 Troubleshooting

### Common Issues

1. **Microphone not working**
   - Check browser permissions
   - Ensure microphone is not used by other applications
   - Try refreshing the page

2. **Voice recognition not accurate**
   - Speak clearly and slowly
   - Reduce background noise
   - Check internet connection for Google Speech Recognition

3. **Text-to-speech not working**
   - Check system audio settings
   - Ensure speakers/headphones are connected
   - Try different TTS engines in configuration

4. **AI responses not working**
   - Check OpenAI API key configuration
   - Verify internet connection
   - Check API usage limits

### Debug Mode

Enable debug logging:
```python
app.config['DEBUG'] = True
app.config['VOICE_DEBUG'] = True
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **SpeechRecognition**: For speech-to-text capabilities
- **pyttsx3**: For offline text-to-speech
- **spaCy**: For natural language processing
- **OpenAI**: For AI-powered responses
- **Bootstrap**: For responsive UI design

---

**Happy Cooking with Voice Control! 🎤👨‍🍳** 
# 🍳 KitchenBuddy - Voice-Controlled Cooking Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Flask-based web application that provides hands-free cooking assistance through advanced voice commands and AI-powered responses.

## 🚀 Live Demo

Access the deployed app here: [https://web-production-2066f.up.railway.app/](https://web-production-2066f.up.railway.app/)

## 🆕 Recent Changes
- Switched to persistent Postgres database for production
- Added a permanent admin user: **Username:** Vishwas, **Password:** Vish@1kb
- Added a `/populate_all` route to populate the database with admin and sample recipes
- Expanded recipe library to include 20+ popular recipes
- Improved voice-only mode and AI assistant features

## 🥗 Recipe Library
The app now includes these recipes by default:
- Butter Chicken
- Vegetable Stir Fry
- Chocolate Chip Cookies
- Greek Salad
- Avocado Toast
- Spaghetti Carbonara
- Margherita Pizza
- Pancakes
- Chicken Caesar Salad
- Tacos
- Palak Paneer
- Beef Stroganoff
- Miso Soup
- Fish Tacos
- Banana Bread
- Shakshuka
- Egg Fried Rice
- Lemon Garlic Salmon
- French Toast
- Quinoa Salad

## 🗝️ Admin Login
- **Username:** Vishwas
- **Password:** Vish@1kb

## 🛠️ How to Populate the Database
After deploying, visit `/populate_all` once to create the admin user and add all sample recipes:
```
https://web-production-2066f.up.railway.app/populate_all
```

## 🔑 Features
- **Voice Commands:** Control your cooking experience hands-free. Say "next step", "repeat that", "set timer for 10 minutes", etc.
- **AI Assistant:** Get intelligent, context-aware cooking guidance.
- **Recipe Library:** Browse and search a growing collection of recipes with detailed steps and dietary info.
- **Voice-Only Mode:** Use `/voice_only` for a streamlined, hands-free cooking experience.
- **Admin Panel:** Manage recipes and users as an admin.

## 📝 Setup (for local development)
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your `.env` with the correct `DATABASE_URL` (for Postgres) or use SQLite for local testing
4. Run the app: `python app.py`
5. (Optional) Visit `/populate_all` to add admin and sample recipes

## 🎤 Voice Commands Reference
- "Start recipe for [recipe name]"
- "Next step"
- "Repeat step"
- "Set timer for 10 minutes"
- "What are the ingredients?"
- "Stop cooking"

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
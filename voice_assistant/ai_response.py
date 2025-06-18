import openai
import os
import json
from typing import Optional, Dict, Any

class AIResponseGenerator:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 150
        
        # Cooking knowledge base for fallback responses
        self.cooking_knowledge = {
            'ingredient_substitutions': {
                'butter': ['olive oil', 'coconut oil', 'applesauce'],
                'eggs': ['flax seeds', 'banana', 'applesauce'],
                'milk': ['almond milk', 'soy milk', 'oat milk'],
                'flour': ['almond flour', 'coconut flour', 'gluten-free flour'],
                'sugar': ['honey', 'maple syrup', 'stevia'],
                'salt': ['herbs', 'lemon juice', 'vinegar']
            },
            'cooking_tips': [
                "Always read the recipe completely before starting",
                "Prep all ingredients before cooking (mise en place)",
                "Use a sharp knife for safer and more efficient cutting",
                "Don't overcrowd the pan when sautéing",
                "Taste as you cook and adjust seasoning",
                "Let meat rest after cooking for juicier results",
                "Use the right size pot or pan for the job",
                "Keep your workspace clean and organized"
            ],
            'healthy_cooking': [
                "Use herbs and spices instead of salt for flavor",
                "Choose lean proteins like chicken breast or fish",
                "Include plenty of colorful vegetables",
                "Use healthy cooking methods like grilling or steaming",
                "Limit processed foods and added sugars",
                "Control portion sizes",
                "Stay hydrated while cooking"
            ]
        }
    
    def generate_response(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate an AI-powered response to a cooking query
        """
        if self.api_key and self._is_complex_query(query):
            return self._generate_openai_response(query, context)
        else:
            return self._generate_fallback_response(query, context)
    
    def _is_complex_query(self, query: str) -> bool:
        """
        Determine if a query is complex enough to warrant AI response
        """
        complex_keywords = [
            'why', 'how', 'explain', 'suggest', 'recommend', 'substitute',
            'alternative', 'healthy', 'nutrition', 'tips', 'advice',
            'what can i cook', 'ingredient', 'technique'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in complex_keywords)
    
    def _generate_openai_response(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate response using OpenAI API
        """
        try:
            # Prepare the prompt
            system_prompt = """You are a helpful cooking assistant. Provide concise, practical advice for cooking questions. 
            Keep responses under 100 words and use a friendly, encouraging tone. Focus on actionable tips and clear explanations."""
            
            user_prompt = f"Cooking question: {query}"
            if context:
                user_prompt += f"\nContext: {json.dumps(context)}"
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response(query, context)
    
    def _generate_fallback_response(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate response using local knowledge base
        """
        query_lower = query.lower()
        
        # Check for ingredient substitution queries
        if 'substitute' in query_lower or 'alternative' in query_lower:
            for ingredient, substitutes in self.cooking_knowledge['ingredient_substitutions'].items():
                if ingredient in query_lower:
                    return f"You can substitute {ingredient} with {', '.join(substitutes[:2])}. Choose based on your recipe and dietary needs."
        
        # Check for cooking tips queries
        if 'tip' in query_lower or 'advice' in query_lower or 'how to' in query_lower:
            import random
            tip = random.choice(self.cooking_knowledge['cooking_tips'])
            return f"Here's a helpful cooking tip: {tip}"
        
        # Check for healthy cooking queries
        if 'healthy' in query_lower or 'nutrition' in query_lower:
            import random
            health_tip = random.choice(self.cooking_knowledge['healthy_cooking'])
            return f"For healthy cooking: {health_tip}"
        
        # Check for ingredient queries
        if 'ingredient' in query_lower or 'what do i need' in query_lower:
            return "I'd be happy to help you with ingredients! Please tell me which recipe you're working on, and I'll list what you need."
        
        # Check for recipe suggestions
        if 'suggest' in query_lower or 'recommend' in query_lower or 'what can i cook' in query_lower:
            return "I can suggest recipes based on your preferences! Try saying 'show me vegetarian recipes' or 'find quick dinner ideas'."
        
        # Default response
        return "I'm here to help with your cooking! You can ask me about recipes, ingredients, cooking tips, or set timers. What would you like to know?"
    
    def generate_recipe_description(self, recipe_title: str, ingredients: str, steps: list) -> str:
        """
        Generate a voice-friendly description of a recipe
        """
        try:
            if self.api_key:
                system_prompt = """Generate a brief, engaging description of this recipe that would be pleasant to hear spoken aloud. 
                Focus on what makes it special and what the cook can expect. Keep it under 50 words."""
                
                user_prompt = f"Recipe: {recipe_title}\nIngredients: {ingredients[:200]}...\nSteps: {len(steps)} steps"
                
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
            else:
                return f"Let's cook {recipe_title}! This recipe has {len(steps)} steps and uses fresh ingredients. I'll guide you through each step."
                
        except Exception as e:
            print(f"Error generating recipe description: {e}")
            return f"Let's cook {recipe_title}! This recipe has {len(steps)} steps and uses fresh ingredients. I'll guide you through each step."
    
    def generate_step_instruction(self, step_text: str, step_number: int, total_steps: int) -> str:
        """
        Generate a voice-friendly version of a cooking step
        """
        try:
            if self.api_key:
                system_prompt = """Rewrite this cooking step to be clear and pleasant when spoken aloud. 
                Use natural language, add helpful context, and make it easy to follow while cooking."""
                
                user_prompt = f"Step {step_number} of {total_steps}: {step_text}"
                
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
            else:
                return f"Step {step_number}: {step_text}"
                
        except Exception as e:
            print(f"Error generating step instruction: {e}")
            return f"Step {step_number}: {step_text}"
    
    def generate_ingredient_list(self, ingredients: str) -> str:
        """
        Generate a voice-friendly ingredient list
        """
        try:
            # Parse ingredients and format for voice
            ingredient_lines = ingredients.split('\n')
            formatted_ingredients = []
            
            for line in ingredient_lines:
                line = line.strip()
                if line:
                    # Clean up common formatting issues
                    line = line.replace('•', '').replace('-', '').strip()
                    if line:
                        formatted_ingredients.append(line)
            
            if formatted_ingredients:
                return "Here are the ingredients you'll need: " + ". ".join(formatted_ingredients)
            else:
                return "Let me check the ingredients for you."
                
        except Exception as e:
            print(f"Error formatting ingredients: {e}")
            return "Let me check the ingredients for you." 
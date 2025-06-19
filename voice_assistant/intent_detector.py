import re
from difflib import SequenceMatcher
from models.db_models import Recipe

class IntentDetector:
    def __init__(self):
        # Only use simple keyword matching; spaCy removed for deployment compatibility
        self.nlp = None
        print("spaCy removed. Using simple keyword matching only.")

    def detect_intent(self, text):
        """
        Detect cooking-related intents from text
        """
        if not text:
            return "unknown"
        
        text = text.lower().strip()
        
        # Define intent patterns
        intent_patterns = {
            'start_recipe': [
                r'\b(start|begin|cook|make|prepare)\b',
                r'\b(recipe|dish|meal)\b',
                r'\b(lets cook|let\'s cook)\b',
                r'\b(open recipe|show recipe)\b'
            ],
            'next_step': [
                r'\b(next|continue|proceed|go on)\b',
                r'\b(what\'s next|what is next)\b',
                r'\b(move on|next step)\b',
                r'\b(continue cooking)\b'
            ],
            'prev_step': [
                r'\b(previous|back|go back|last step)\b',
                r'\b(what was before|repeat previous)\b',
                r'\b(step back|go backwards)\b'
            ],
            'repeat_step': [
                r'\b(repeat|say again|one more time)\b',
                r'\b(what was that|didn\'t hear)\b',
                r'\b(go back|previous step)\b',
                r'\b(read again|tell me again)\b'
            ],
            'current_step': [
                r'\b(current step|what step|which step)\b',
                r'\b(where am i|what am i doing)\b',
                r'\b(step number|current instruction)\b'
            ],
            'stop_cooking': [
                r'\b(stop|end|finish|done)\b',
                r'\b(quit|exit|cancel)\b',
                r'\b(stop cooking|end recipe)\b',
                r'\b(pause cooking|take a break)\b'
            ],
            'search_recipe': [
                r'\b(search|find|look for)\b',
                r'\b(recipe for|how to make)\b',
                r'\b(show me|find me)\b',
                r'\b(suggest|recommend)\b'
            ],
            'ingredients_query': [
                r'\b(ingredients|what do i need|what\'s needed)\b',
                r'\b(do i have|check ingredients)\b',
                r'\b(ingredient list|what\'s in it)\b',
                r'\b(missing ingredients|what\'s missing)\b'
            ],
            'set_timer': [
                r'\b(timer|set timer|start timer)\b',
                r'\b(countdown|alarm|reminder)\b',
                r'\b(wait|time|minutes)\b',
                r'\b(how long|duration)\b'
            ],
            'dietary_filter': [
                r'\b(vegan|vegetarian|gluten-free)\b',
                r'\b(show only|filter|dietary)\b',
                r'\b(healthy|low carb|keto)\b',
                r'\b(no meat|dairy-free)\b'
            ],
            'ai_query': [
                r'\b(what can i cook|suggest|recommend)\b',
                r'\b(how to|tips|advice)\b',
                r'\b(is this healthy|nutrition)\b',
                r'\b(substitute|alternative)\b',
                r'\b(why|explain|tell me about)\b'
            ],
            'resume_cooking': [
                r'\b(resume|continue|pick up)\b',
                r'\b(where was i|what was i cooking)\b',
                r'\b(restart|begin again)\b'
            ],
            'help': [
                r'\b(help|what can you do|commands)\b',
                r'\b(how to use|instructions)\b',
                r'\b(support|assist)\b'
            ]
        }
        # Check each intent pattern
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return intent
        return "unknown"

    def extract_recipe_name(self, text):
        """
        Extract recipe name from text using fuzzy matching
        """
        if not text:
            return None
        text = text.lower()
        patterns = [
            r'recipe for (.+)',
            r'how to make (.+)',
            r'cook (.+)',
            r'make (.+)',
            r'prepare (.+)',
            r'start (.+)',
            r'begin (.+)',
            r'open (.+)'
        ]
        extracted_name = None
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                extracted_name = match.group(1).strip()
                break
        if not extracted_name:
            words = text.split()
            if len(words) >= 2:
                recipe_indicators = ['recipe', 'dish', 'meal', 'food']
                for i, word in enumerate(words):
                    if word in recipe_indicators and i + 1 < len(words):
                        extracted_name = ' '.join(words[i+1:])
                        break
        if extracted_name:
            extracted_name = re.sub(r'\b(recipe|dish|meal|food|for|the|a|an)\b', '', extracted_name).strip()
            return extracted_name if extracted_name else None
        return None

    def find_recipe_by_name(self, recipe_name, recipes=None):
        """
        Find recipe by name using fuzzy matching
        """
        if not recipe_name:
            return None
        if recipes is None:
            recipes = Recipe.query.all()
        best_match = None
        best_ratio = 0
        for recipe in recipes:
            if recipe.title.lower() == recipe_name.lower():
                return recipe
            if recipe_name.lower() in recipe.title.lower():
                ratio = len(recipe_name) / len(recipe.title)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = recipe
            ratio = SequenceMatcher(None, recipe_name.lower(), recipe.title.lower()).ratio()
            if ratio > best_ratio and ratio > 0.6:
                best_ratio = ratio
                best_match = recipe
        return best_match

    def extract_timer_duration(self, text):
        """
        Extract timer duration from text
        """
        if not text:
            return 5  # Default 5 minutes
        text = text.lower()
        time_patterns = {
            r'(\d+)\s*minutes?': lambda x: int(x),
            r'(\d+)\s*mins?': lambda x: int(x),
            r'(\d+)\s*min': lambda x: int(x),
            r'five\s*minutes?': lambda x: 5,
            r'ten\s*minutes?': lambda x: 10,
            r'fifteen\s*minutes?': lambda x: 15,
            r'thirty\s*minutes?': lambda x: 30,
            r'one\s*hour': lambda x: 60,
            r'(\d+)\s*hours?': lambda x: int(x) * 60,
            r'(\d+)\s*hrs?': lambda x: int(x) * 60
        }
        for pattern, converter in time_patterns.items():
            match = re.search(pattern, text)
            if match:
                try:
                    if 'hour' in pattern or 'hr' in pattern:
                        return converter(match.group(1))
                    elif 'five' in pattern or 'ten' in pattern or 'fifteen' in pattern or 'thirty' in pattern:
                        return converter(None)
                    else:
                        return converter(match.group(1))
                except (ValueError, IndexError):
                    continue
        return 5  # Default 5 minutes

    def extract_dietary_preference(self, text):
        """
        Extract dietary preference from text
        """
        if not text:
            return None
        text = text.lower()
        dietary_keywords = {
            'vegan': ['vegan', 'no animal products'],
            'vegetarian': ['vegetarian', 'no meat', 'meatless'],
            'gluten-free': ['gluten-free', 'gluten free', 'no gluten'],
            'dairy-free': ['dairy-free', 'dairy free', 'no dairy', 'lactose-free'],
            'keto': ['keto', 'ketogenic', 'low carb'],
            'paleo': ['paleo', 'paleolithic'],
            'low-sodium': ['low sodium', 'low-sodium', 'no salt'],
            'low-fat': ['low fat', 'low-fat', 'fat-free']
        }
        for preference, keywords in dietary_keywords.items():
            if any(keyword in text for keyword in keywords):
                return preference
        return None 
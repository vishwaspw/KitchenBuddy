import os
import tempfile
import uuid

class TextToSpeech:
    def __init__(self):
        self.audio_dir = 'static/audio'
        self._ensure_audio_dir()
        
        # Initialize pyttsx3 for offline TTS
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume level
        except Exception as e:
            print(f"Could not initialize pyttsx3: {e}")
            self.engine = None
    
    def _ensure_audio_dir(self):
        """Ensure the audio directory exists"""
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
    
    def convert_text_to_speech(self, text, use_online=True):
        """
        Convert text to speech and return the audio file path
        """
        if not text:
            return None
        
        try:
            # Generate unique filename
            filename = f"speech_{uuid.uuid4().hex[:8]}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            
            if use_online and self._is_internet_available():
                # Use Google Text-to-Speech (online)
                return self._convert_with_gtts(text, filepath)
            else:
                # Use pyttsx3 (offline)
                return self._convert_with_pyttsx3(text, filepath)
                
        except Exception as e:
            print(f"Error in text to speech conversion: {e}")
            return None
    
    def _convert_with_gtts(self, text, filepath):
        """Convert text to speech using Google TTS"""
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filepath)
            return f"/static/audio/{os.path.basename(filepath)}"
        except ImportError:
            print("gTTS not available, falling back to pyttsx3")
            return self._convert_with_pyttsx3(text, filepath)
        except Exception as e:
            print(f"gTTS error: {e}")
            # Fallback to pyttsx3
            return self._convert_with_pyttsx3(text, filepath)
    
    def _convert_with_pyttsx3(self, text, filepath):
        """Convert text to speech using pyttsx3"""
        try:
            if self.engine:
                # Save to file
                self.engine.save_to_file(text, filepath)
                self.engine.runAndWait()
                return f"/static/audio/{os.path.basename(filepath)}"
            else:
                return None
        except Exception as e:
            print(f"pyttsx3 error: {e}")
            return None
    
    def _is_internet_available(self):
        """Check if internet connection is available"""
        try:
            import urllib.request
            urllib.request.urlopen('http://www.google.com', timeout=3)
            return True
        except:
            return False
    
    def speak_text(self, text):
        """
        Speak text directly (for immediate feedback)
        """
        if not text or not self.engine:
            return False
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"Error speaking text: {e}")
            return False
    
    def cleanup_old_audio_files(self, max_age_hours=24):
        """
        Clean up old audio files to save disk space
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        try:
            for filename in os.listdir(self.audio_dir):
                filepath = os.path.join(self.audio_dir, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        print(f"Cleaned up old audio file: {filename}")
        except Exception as e:
            print(f"Error cleaning up audio files: {e}") 
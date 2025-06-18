import speech_recognition as sr
import os
import tempfile
from werkzeug.utils import secure_filename

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
    
    def convert_speech_to_text(self, audio_file):
        """
        Convert uploaded audio file to text
        """
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                audio_file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            # Convert audio file to text
            with sr.AudioFile(temp_file_path) as source:
                audio = self.recognizer.record(source)
                
                # Try different recognition services
                try:
                    # Try Google Speech Recognition (requires internet)
                    text = self.recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    # Fallback to Sphinx (offline)
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                    except:
                        text = None
                except sr.RequestError:
                    # If Google service fails, try Sphinx
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                    except:
                        text = None
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return text.lower() if text else None
            
        except Exception as e:
            print(f"Error in speech to text conversion: {e}")
            return None
    
    def convert_microphone_to_text(self):
        """
        Convert live microphone input to text
        """
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    return text.lower()
                except sr.UnknownValueError:
                    return None
                except sr.RequestError:
                    return None
                    
        except Exception as e:
            print(f"Error in microphone conversion: {e}")
            return None 
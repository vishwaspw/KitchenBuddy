import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from voice_assistant.text_to_speech import TextToSpeech

class TimerManager:
    def __init__(self):
        self.active_timers: Dict[str, Dict] = {}
        self.tts = TextToSpeech()
        self._lock = threading.Lock()
    
    def start_timer(self, timer_id: str, minutes: int, callback: Optional[Callable] = None) -> bool:
        """
        Start a timer with voice notification
        """
        try:
            with self._lock:
                if timer_id in self.active_timers:
                    return False  # Timer already exists
                
                # Create timer info
                timer_info = {
                    'id': timer_id,
                    'duration_minutes': minutes,
                    'start_time': datetime.now(),
                    'end_time': datetime.now() + timedelta(minutes=minutes),
                    'callback': callback,
                    'thread': None,
                    'is_active': True
                }
                
                # Start timer thread
                timer_thread = threading.Thread(
                    target=self._timer_worker,
                    args=(timer_id, minutes),
                    daemon=True
                )
                timer_thread.start()
                
                timer_info['thread'] = timer_thread
                self.active_timers[timer_id] = timer_info
                
                # Announce timer start
                self.tts.speak_text(f"Timer started for {minutes} minutes")
                
                return True
                
        except Exception as e:
            print(f"Error starting timer: {e}")
            return False
    
    def _timer_worker(self, timer_id: str, minutes: int):
        """
        Background worker for timer countdown
        """
        try:
            # Sleep for the specified duration
            time.sleep(minutes * 60)
            
            # Check if timer is still active
            with self._lock:
                if timer_id in self.active_timers and self.active_timers[timer_id]['is_active']:
                    # Timer completed
                    timer_info = self.active_timers[timer_id]
                    timer_info['is_active'] = False
                    
                    # Announce completion
                    self.tts.speak_text(f"Time's up! Your {minutes} minute timer has finished. Let's continue cooking!")
                    
                    # Call callback if provided
                    if timer_info['callback']:
                        try:
                            timer_info['callback'](timer_id, minutes)
                        except Exception as e:
                            print(f"Error in timer callback: {e}")
                    
                    # Remove timer from active list
                    del self.active_timers[timer_id]
                    
        except Exception as e:
            print(f"Error in timer worker: {e}")
    
    def stop_timer(self, timer_id: str) -> bool:
        """
        Stop an active timer
        """
        try:
            with self._lock:
                if timer_id in self.active_timers:
                    timer_info = self.active_timers[timer_id]
                    timer_info['is_active'] = False
                    
                    # Announce timer stop
                    self.tts.speak_text("Timer stopped")
                    
                    # Remove from active timers
                    del self.active_timers[timer_id]
                    return True
                return False
                
        except Exception as e:
            print(f"Error stopping timer: {e}")
            return False
    
    def get_timer_status(self, timer_id: str) -> Optional[Dict]:
        """
        Get status of a timer
        """
        with self._lock:
            if timer_id in self.active_timers:
                timer_info = self.active_timers[timer_id].copy()
                if timer_info['is_active']:
                    remaining = timer_info['end_time'] - datetime.now()
                    timer_info['remaining_seconds'] = max(0, int(remaining.total_seconds()))
                    timer_info['remaining_minutes'] = max(0, int(remaining.total_seconds() // 60))
                return timer_info
            return None
    
    def get_all_timers(self) -> Dict[str, Dict]:
        """
        Get all active timers
        """
        with self._lock:
            return self.active_timers.copy()
    
    def get_remaining_time(self, timer_id: str) -> Optional[str]:
        """
        Get remaining time as a formatted string
        """
        timer_info = self.get_timer_status(timer_id)
        if timer_info and timer_info['is_active']:
            remaining_seconds = timer_info['remaining_seconds']
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        return None
    
    def announce_remaining_time(self, timer_id: str):
        """
        Announce remaining time for a timer
        """
        timer_info = self.get_timer_status(timer_id)
        if timer_info and timer_info['is_active']:
            remaining_minutes = timer_info['remaining_minutes']
            if remaining_minutes > 0:
                self.tts.speak_text(f"You have {remaining_minutes} minutes remaining on your timer")
            else:
                remaining_seconds = timer_info['remaining_seconds']
                self.tts.speak_text(f"You have {remaining_seconds} seconds remaining on your timer")
    
    def cleanup_expired_timers(self):
        """
        Clean up any expired timers
        """
        with self._lock:
            expired_timers = []
            for timer_id, timer_info in self.active_timers.items():
                if datetime.now() > timer_info['end_time']:
                    expired_timers.append(timer_id)
            
            for timer_id in expired_timers:
                del self.active_timers[timer_id]
    
    def get_timer_count(self) -> int:
        """
        Get number of active timers
        """
        with self._lock:
            return len(self.active_timers)

# Global timer manager instance
timer_manager = TimerManager() 
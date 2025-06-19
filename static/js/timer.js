// Minimal timer functionality for countdown display
class CookingTimer {
    constructor() {
        this.timer = null;
        this.endTime = null;
        this.isRunning = false;
    }

    startTimer(minutes) {
        if (this.isRunning) {
            this.stopTimer();
        }
        
        this.endTime = new Date().getTime() + (minutes * 60 * 1000);
        this.isRunning = true;
        this.updateDisplay();
        
        this.timer = setInterval(() => {
            this.updateDisplay();
        }, 1000);
    }

    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.isRunning = false;
        this.endTime = null;
        this.updateDisplay();
    }

    updateDisplay() {
        const timerDisplay = document.getElementById('timerDisplay');
        if (!timerDisplay) return;

        if (!this.isRunning || !this.endTime) {
            timerDisplay.textContent = '00:00';
            return;
        }

        const now = new Date().getTime();
        const distance = this.endTime - now;

        if (distance < 0) {
            this.stopTimer();
            timerDisplay.textContent = '00:00';
            this.showTimerComplete();
            return;
        }

        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        timerDisplay.textContent = 
            (minutes < 10 ? '0' : '') + minutes + ':' + 
            (seconds < 10 ? '0' : '') + seconds;
    }

    showTimerComplete() {
        const timerContainer = document.getElementById('timerContainer');
        if (timerContainer) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-warning alert-dismissible fade show';
            alert.innerHTML = `
                <i class="fas fa-bell me-2"></i>
                Timer completed!
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            timerContainer.appendChild(alert);
        }
        // Play timer sound
        let audio = document.getElementById('timerDoneAudio');
        if (!audio) {
            audio = document.createElement('audio');
            audio.id = 'timerDoneAudio';
            audio.src = '/static/audio/timer_done.mp3';
            audio.preload = 'auto';
            document.body.appendChild(audio);
        }
        audio.currentTime = 0;
        audio.play();
    }
}

// Initialize timer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const timer = new CookingTimer();
    window.CookingTimerInstance = timer;
    
    // Add timer controls to the page
    const timerButtons = document.querySelectorAll('.timer-btn');
    timerButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const minutes = parseInt(this.dataset.minutes);
            timer.startTimer(minutes);
        });
    });
    
    // Stop timer button
    const stopTimerBtn = document.getElementById('stopTimerBtn');
    if (stopTimerBtn) {
        stopTimerBtn.addEventListener('click', function() {
            timer.stopTimer();
        });
    }
}); 
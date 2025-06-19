// Voice-Only Mode JavaScript
class VoiceOnlyInterface {
    constructor() {
        this.isRecording = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.activeTimer = null;
        this.timerInterval = null;
        
        this.initializeSpeechRecognition();
        this.bindEvents();
        this.updateVoiceFeedback("Voice-only mode ready. Click the microphone button or say 'start cooking' to begin.");
    }

    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isRecording = true;
                this.updateUI('listening');
            };
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript.toLowerCase();
                this.processVoiceCommand(transcript);
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.updateVoiceFeedback("Sorry, I didn't catch that. Please try again.");
                this.updateUI('ready');
            };
            
            this.recognition.onend = () => {
                this.isRecording = false;
                this.updateUI('ready');
            };
        } else {
            this.updateVoiceFeedback("Speech recognition not supported in this browser. Use the buttons instead.");
        }
    }

    bindEvents() {
        // Voice recording button
        const voiceRecordBtn = document.getElementById('voiceRecordBtn');
        if (voiceRecordBtn) {
            voiceRecordBtn.addEventListener('click', () => this.toggleRecording());
        }

        // Quick action buttons
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.closest('.quick-action').dataset.action;
                this.executeAction(action);
            });
        });

        // Timer buttons
        document.querySelectorAll('.timer-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const minutes = parseInt(e.target.dataset.minutes);
                this.setTimer(minutes);
            });
        });

        // Stop timer button
        const stopTimerBtn = document.getElementById('stopTimerBtn');
        if (stopTimerBtn) {
            stopTimerBtn.addEventListener('click', () => this.stopTimer());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === ' ' && !this.isRecording) {
                e.preventDefault();
                this.toggleRecording();
            }
        });
    }

    toggleRecording() {
        if (!this.recognition) {
            this.updateVoiceFeedback("Speech recognition not available. Please use the buttons.");
            return;
        }

        if (this.isRecording) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    updateUI(state) {
        const recordBtn = document.getElementById('voiceRecordBtn');
        const recordBtnText = document.getElementById('recordBtnText');
        const recordingStatus = document.getElementById('recordingStatus');
        const statusText = document.getElementById('statusText');
        const voiceIndicator = document.querySelector('.voice-indicator');

        if (state === 'listening') {
            recordBtn.classList.remove('btn-primary');
            recordBtn.classList.add('btn-danger');
            recordBtnText.textContent = 'Stop Listening';
            recordingStatus.classList.remove('d-none');
            statusText.textContent = 'Listening...';
            voiceIndicator.style.backgroundColor = '#dc3545';
            voiceIndicator.style.animation = 'pulse 1s infinite';
        } else {
            recordBtn.classList.remove('btn-danger');
            recordBtn.classList.add('btn-primary');
            recordBtnText.textContent = 'Start Voice Control';
            recordingStatus.classList.add('d-none');
            statusText.textContent = 'Ready';
            voiceIndicator.style.backgroundColor = '#28a745';
            voiceIndicator.style.animation = 'none';
        }
    }

    processVoiceCommand(transcript) {
        console.log('Voice command:', transcript);
        this.updateVoiceFeedback(`Processing: "${transcript}"`);

        // Recipe navigation commands
        if (transcript.includes('next') || transcript.includes('next step')) {
            this.executeAction('next');
        } else if (transcript.includes('previous') || transcript.includes('back') || transcript.includes('prev')) {
            this.executeAction('prev');
        } else if (transcript.includes('repeat') || transcript.includes('say again')) {
            this.executeAction('repeat');
        } else if (transcript.includes('ingredients') || transcript.includes('ingredient list')) {
            this.executeAction('ingredients');
        } else if (transcript.includes('timer') || transcript.includes('set timer')) {
            this.executeAction('timer');
        } else if (transcript.includes('stop') || transcript.includes('stop cooking')) {
            this.executeAction('stop');
        } else if (transcript.includes('start') && (transcript.includes('recipe') || transcript.includes('cooking'))) {
            this.startRecipe();
        } else if (transcript.includes('help') || transcript.includes('what can you do')) {
            this.showHelp();
        } else {
            // Send to AI for processing
            this.sendToAI(transcript);
        }
    }

    async executeAction(action) {
        let response = '';
        switch (action) {
            case 'next':
                response = await this.sendVoiceCommand('next_step');
                break;
            case 'prev':
                response = await this.sendVoiceCommand('previous_step');
                break;
            case 'repeat':
                response = await this.sendVoiceCommand('repeat_step');
                break;
            case 'ingredients':
                response = await this.sendVoiceCommand('show_ingredients');
                break;
            case 'timer':
                response = await this.sendVoiceCommand('set_timer');
                break;
            case 'stop':
                response = await this.sendVoiceCommand('stop_cooking');
                break;
        }

        // Always prioritize step_instruction for TTS if present
        if (response && typeof response === 'object') {
            if (response.step_instruction) {
                this.updateVoiceFeedback(response.step_instruction);
                this.speak(response.step_instruction);
            } else if (response.message) {
                this.updateVoiceFeedback(response.message);
                this.speak(response.message);
            } else if (response.response) {
                this.updateVoiceFeedback(response.response);
                this.speak(response.response);
            }
        } else if (typeof response === 'string') {
            this.updateVoiceFeedback(response);
            this.speak(response);
        }
    }

    async sendVoiceCommand(command) {
        try {
            const response = await fetch('/voice_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command })
            });

            if (response.ok) {
                const data = await response.json();
                return data.response || data.message || 'Command executed successfully.';
            } else {
                throw new Error('Failed to execute command');
            }
        } catch (error) {
            console.error('Error sending voice command:', error);
            return 'Sorry, there was an error processing your command.';
        }
    }

    async sendToAI(transcript) {
        try {
            const response = await fetch('/ai_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: transcript,
                    context: 'voice_cooking'
                })
            });

            if (response.ok) {
                const data = await response.json();
                const aiResponse = data.response || 'I understand you said: ' + transcript;
                this.updateVoiceFeedback(aiResponse);
                this.speak(aiResponse);
            } else {
                throw new Error('Failed to get AI response');
            }
        } catch (error) {
            console.error('Error getting AI response:', error);
            this.updateVoiceFeedback("I didn't understand that command. Try saying 'help' for available commands.");
        }
    }

    setTimer(minutes) {
        if (this.activeTimer) {
            this.stopTimer();
        }

        const seconds = minutes * 60;
        this.activeTimer = seconds;
        
        // Show timer card
        const timerCard = document.getElementById('activeTimerCard');
        const timerDisplay = document.getElementById('timerDisplay');
        
        if (timerCard && timerDisplay) {
            timerCard.classList.remove('d-none');
            
            this.timerInterval = setInterval(() => {
                this.activeTimer--;
                const mins = Math.floor(this.activeTimer / 60);
                const secs = this.activeTimer % 60;
                timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                
                if (this.activeTimer <= 0) {
                    this.timerComplete();
                }
            }, 1000);
        }

        const message = `Timer set for ${minutes} minutes.`;
        this.updateVoiceFeedback(message);
        this.speak(message);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        this.activeTimer = null;
        
        const timerCard = document.getElementById('activeTimerCard');
        if (timerCard) {
            timerCard.classList.add('d-none');
        }

        const message = 'Timer stopped.';
        this.updateVoiceFeedback(message);
        this.speak(message);
    }

    timerComplete() {
        this.stopTimer();
        const message = 'Timer complete! Your food is ready!';
        this.updateVoiceFeedback(message);
        this.speak(message);
        
        // Visual notification
        const timerDisplay = document.getElementById('timerDisplay');
        if (timerDisplay) {
            timerDisplay.style.color = '#dc3545';
            timerDisplay.style.animation = 'blink 1s infinite';
        }
    }

    startRecipe() {
        this.updateVoiceFeedback("To start a recipe, please go to the dashboard and select a recipe first.");
        this.speak("To start a recipe, please go to the dashboard and select a recipe first.");
    }

    showHelp() {
        const helpText = `Available voice commands: Next step, Previous step, Repeat step, Show ingredients, Set timer, Stop cooking, and Help. You can also ask me cooking questions!`;
        this.updateVoiceFeedback(helpText);
        this.speak(helpText);
    }

    updateVoiceFeedback(message) {
        const feedbackElement = document.getElementById('voiceFeedback');
        if (feedbackElement) {
            feedbackElement.textContent = message;
        }
    }

    speak(text) {
        if (this.synthesis && this.synthesis.speak) {
            // Stop any current speech
            this.synthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 0.8;
            
            this.synthesis.speak(utterance);
        }
    }
}

// Global function for starting voice commands
function startVoiceCommand() {
    if (window.voiceInterface) {
        window.voiceInterface.toggleRecording();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.voiceInterface = new VoiceOnlyInterface();
});

// Add CSS for voice indicator
const style = document.createElement('style');
style.textContent = `
    .voice-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #28a745;
        display: inline-block;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    
    .step-content {
        min-height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
`;
document.head.appendChild(style); 
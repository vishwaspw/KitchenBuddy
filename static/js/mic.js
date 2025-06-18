// Minimal microphone functionality for voice recording
class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.sendAudioToServer();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            return true;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            return false;
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    async sendAudioToServer() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice_input.wav');

        try {
            const response = await fetch('/transcribe', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handleTranscriptionResult(result);
            } else {
                console.error('Transcription failed');
            }
        } catch (error) {
            console.error('Error sending audio:', error);
        }
    }

    handleTranscriptionResult(result) {
        // Redirect to the appropriate route based on the transcription
        if (result.redirect_url) {
            window.location.href = result.redirect_url;
        }
    }
}

// Initialize voice recorder when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const recordButton = document.getElementById('voiceRecordBtn');
    const voiceRecorder = new VoiceRecorder();
    
    if (recordButton) {
        recordButton.addEventListener('click', async function() {
            if (!voiceRecorder.isRecording) {
                const success = await voiceRecorder.startRecording();
                if (success) {
                    recordButton.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
                    recordButton.classList.remove('btn-primary');
                    recordButton.classList.add('btn-danger');
                }
            } else {
                voiceRecorder.stopRecording();
                recordButton.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
                recordButton.classList.remove('btn-danger');
                recordButton.classList.add('btn-primary');
            }
        });
    }
}); 
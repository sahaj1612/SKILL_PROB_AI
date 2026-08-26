// Speech recognition for interview answers
class SpeechRecognitionManager {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.finalTranscript = '';
        this.interimTranscript = '';
        this.isSupported = false;
        
        this.speechButton = document.getElementById('toggle-speech');
        this.speechStatus = document.getElementById('speech-status');
        this.transcriptDisplay = document.getElementById('transcript-display');
        this.answerText = document.getElementById('answer-text');
        
        this.init();
    }
    
    init() {
        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Speech Recognition API not supported in this browser');
            this.showUnsupportedMessage();
            return;
        }
        
        this.isSupported = true;
        
        // Initialize speech recognition
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        // Event handlers
        this.recognition.onstart = () => {
            console.log('Speech recognition started');
            this.isListening = true;
            this.updateUI();
            this.sendSpeechStatus(true);
        };
        
        this.recognition.onresult = (event) => {
            this.interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                
                if (event.results[i].isFinal) {
                    this.finalTranscript += transcript + ' ';
                    console.log('Final transcript chunk:', transcript);
                } else {
                    this.interimTranscript += transcript;
                }
            }
            
            this.updateTranscriptDisplay();
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.updateUI();
            this.sendSpeechStatus(false);
            
            // Show user-friendly error messages
            switch (event.error) {
                case 'no-speech':
                    // Silent retry or gentle notification
                    break;
                case 'audio-capture':
                    alert('No microphone found. Please ensure a microphone is connected and permissions are granted.');
                    break;
                case 'not-allowed':
                    alert('Microphone access was denied. Please allow microphone access in your browser settings.');
                    break;
                default:
                    console.warn('Speech recognition notice:', event.error);
            }
        };
        
        this.recognition.onend = () => {
            console.log('Speech recognition ended');
            this.isListening = false;
            this.updateUI();
            this.sendSpeechStatus(false);
        };
        
        // Button click handler
        this.speechButton?.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleSpeechRecognition();
        });
        
        // Initialize UI
        this.updateUI();
    }
    
    showUnsupportedMessage() {
        if (this.speechButton) {
            this.speechButton.disabled = true;
            this.speechButton.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i> Speech Not Supported';
            this.speechButton.classList.remove('from-green-500', 'to-blue-500');
            this.speechButton.classList.add('bg-gray-400');
        }
        
        if (this.speechStatus) {
            const statusIndicator = this.speechStatus.querySelector('.h-3');
            const statusText = this.speechStatus.querySelector('span:last-child');
            
            if (statusIndicator) statusIndicator.className = 'h-3 w-3 rounded-full bg-gray-500 mr-2';
            if (statusText) statusText.textContent = 'Unsupported';
        }
    }
    
    toggleSpeechRecognition() {
        if (!this.isSupported) {
            alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
            return;
        }
        
        if (this.isListening) {
            this.stop();
        } else {
            this.start();
        }
    }
    
    start() {
        if (!this.recognition) {
            alert('Speech recognition not initialized. Please refresh the page.');
            return;
        }
        
        if (this.isListening) {
            return;
        }
        
        // Request microphone permission first
        this.requestMicrophonePermission()
            .then(() => {
                try {
                    this.recognition.start();
                } catch (error) {
                    console.error('Failed to start speech recognition:', error);
                }
            })
            .catch(error => {
                console.error('Microphone permission denied:', error);
                alert('Microphone access is required for speech recognition. Please allow microphone access.');
            });
    }
    
    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: true,
                video: false 
            });
            
            // Stop the temporary stream tracks
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            throw error;
        }
    }
    
    stop() {
        if (this.recognition && this.isListening) {
            try {
                this.recognition.stop();
            } catch (error) {
                console.error('Failed to stop speech recognition:', error);
            }
            this.isListening = false;
            this.updateUI();
        }
    }
    
    updateUI() {
        if (!this.speechButton) return;
        
        if (this.isListening) {
            this.speechButton.innerHTML = '<i class="fas fa-microphone-slash mr-2"></i> Stop Speaking';
            this.speechButton.classList.remove('from-green-500', 'to-blue-500');
            this.speechButton.classList.add('from-red-500', 'to-purple-500');
            
            this.updateStatusIndicator('green', 'Listening...');
        } else {
            this.speechButton.innerHTML = '<i class="fas fa-microphone mr-2"></i> Start Speaking';
            this.speechButton.classList.remove('from-red-500', 'to-purple-500');
            this.speechButton.classList.add('from-green-500', 'to-blue-500');
            
            this.updateStatusIndicator('red', 'Off');
        }
    }
    
    updateStatusIndicator(color, text) {
        if (!this.speechStatus) return;
        
        const statusIndicator = this.speechStatus.querySelector('.h-3');
        const statusText = this.speechStatus.querySelector('span:last-child');
        
        if (statusIndicator) {
            statusIndicator.className = `h-3 w-3 rounded-full bg-${color}-500 mr-2 ${color === 'green' ? 'animate-pulse' : ''}`;
        }
        
        if (statusText) {
            statusText.textContent = text;
        }
    }
    
    updateTranscriptDisplay() {
        if (!this.transcriptDisplay) return;
        
        let displayText = this.finalTranscript;
        
        if (this.interimTranscript) {
            displayText += '<span class="text-gray-400">' + this.interimTranscript + '</span>';
        }
        
        if (displayText.trim() === '') {
            displayText = '<p class="text-gray-500 italic">Start speaking... Your words will appear here.</p>';
        } else {
            displayText = '<p>' + displayText + '</p>';
        }
        
        this.transcriptDisplay.innerHTML = displayText;
        this.transcriptDisplay.scrollTop = this.transcriptDisplay.scrollHeight;
    }
    
    async sendSpeechStatus(isActive) {
        try {
            await fetch('/api/speech-status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: isActive })
            });
        } catch (error) {
            console.error('Error sending speech status:', error);
        }
    }
    
    getTranscript() {
        return (this.finalTranscript + ' ' + this.interimTranscript).trim();
    }
    
    clearTranscript() {
        this.finalTranscript = '';
        this.interimTranscript = '';
        this.updateTranscriptDisplay();
    }
}

// Initialize speech recognition when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.speechManager = new SpeechRecognitionManager();
    
    // Add browser compatibility warning
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4';
        warningDiv.innerHTML = `
            <p class="font-bold">Browser Compatibility Note</p>
            <p>Speech recognition works best in Google Chrome, Microsoft Edge, and Safari.
            If you're using Firefox, please enable <code>media.webspeech.recognition.enable</code> in about:config.</p>
        `;
        
        const main = document.querySelector('main');
        if (main) {
            main.insertBefore(warningDiv, main.firstChild);
        }
    }
});
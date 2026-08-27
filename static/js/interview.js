// Interview session management
class InterviewManager {
    constructor() {
        this.currentQuestionIndex = 0;
        this.totalQuestions = 0;
        this.currentQuestion = null;
        this.sessionId = document.getElementById('session-id')?.value;
        this.questionStartedAt = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialQuestion();
    }
    
    setupEventListeners() {
        // Submit answer
        document.getElementById('submit-answer')?.addEventListener('click', () => this.submitAnswer());
        
        // Skip question
        document.getElementById('skip-question')?.addEventListener('click', () => this.skipQuestion());
        
        // Finish interview
        document.getElementById('finish-interview')?.addEventListener('click', () => this.finishInterview());
        
        // Next question
        document.getElementById('next-question-btn')?.addEventListener('click', () => this.nextQuestion());
        
    }
    
    async loadInitialQuestion() {
        try {
            const response = await fetch('/api/next-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'get_current' })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentQuestionIndex = data.current_index;
                this.totalQuestions = data.total_questions;
                this.displayQuestion(data.question);
            } else if (data.status === 'completed') {
                this.showCompletionMessage();
            } else {
                console.error('Failed to load initial question:', data.message);
            }
        } catch (error) {
            console.error('Error loading initial question:', error);
        }
    }
    
    displayQuestion(question) {
        if (!question) return;
        this.currentQuestion = question;

        // Update question text
        const questionTextEl = document.getElementById('question-text');
        if (questionTextEl) questionTextEl.textContent = question.question_text;
        
        // Update question ID
        const questionIdEl = document.getElementById('current-question-id');
        if (questionIdEl) questionIdEl.value = question.id;
        
        // Update question counter
        const counterEl = document.getElementById('question-counter');
        if (counterEl) {
            counterEl.textContent = `Question ${this.currentQuestionIndex + 1} of ${this.totalQuestions || 1}`;
        }
        
        // Update question tags
        const typeTag = document.getElementById('question-type');
        const difficultyTag = document.getElementById('question-difficulty');
        
        const qType = question.question_type || 'technical';
        const qDiff = question.difficulty || 'medium';
        
        if (typeTag) {
            typeTag.textContent = qType.charAt(0).toUpperCase() + qType.slice(1);
            typeTag.className = `px-3 py-1 rounded-full text-sm ${
                qType === 'technical' ? 'bg-blue-100 text-blue-800' :
                qType === 'behavioral' ? 'bg-green-100 text-green-800' :
                qType === 'situational' ? 'bg-yellow-100 text-yellow-800' :
                'bg-purple-100 text-purple-800'
            }`;
        }
        
        if (difficultyTag) {
            difficultyTag.textContent = qDiff.charAt(0).toUpperCase() + qDiff.slice(1);
            difficultyTag.className = `px-3 py-1 rounded-full text-sm ${
                qDiff === 'easy' ? 'bg-green-100 text-green-800' :
                qDiff === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
            }`;
        }
        
        this.questionStartedAt = Date.now();
        
        // Clear previous answer and speech transcript
        const answerTextarea = document.getElementById('answer-text');
        if (answerTextarea) answerTextarea.value = '';
        
        if (window.speechManager) {
            window.speechManager.stop();
            window.speechManager.clearTranscript();
        }
        
        // Hide feedback area and make sure answer inputs are enabled
        const feedbackArea = document.getElementById('feedback-area');
        if (feedbackArea) feedbackArea.classList.add('hidden');

        // Reset submit button state
        const submitBtn = document.getElementById('submit-answer');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i> Submit Answer';
        }
    }
    
    async submitAnswer() {
        // Stop speech recognition if listening
        if (window.speechManager && window.speechManager.isListening) {
            window.speechManager.stop();
        }
        
        const questionId = document.getElementById('current-question-id')?.value;
        const typedAnswer = (document.getElementById('answer-text')?.value || '').trim();
        const speechTranscript = window.speechManager ? window.speechManager.getTranscript().trim() : '';
        const duration = Math.max(1, Math.round((Date.now() - (this.questionStartedAt || Date.now())) / 1000));

        // Combine typed answer and speech transcript cleanly
        let combinedAnswer = '';
        if (typedAnswer && speechTranscript) {
            if (typedAnswer.includes(speechTranscript)) {
                combinedAnswer = typedAnswer;
            } else if (speechTranscript.includes(typedAnswer)) {
                combinedAnswer = speechTranscript;
            } else {
                combinedAnswer = typedAnswer + '\n' + speechTranscript;
            }
        } else {
            combinedAnswer = typedAnswer || speechTranscript;
        }

        if (!combinedAnswer.trim()) {
            alert('Please provide an answer before submitting. You can type or speak your answer.');
            return;
        }
        
        const submitBtn = document.getElementById('submit-answer');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Analyzing...';
        }
        
        try {
            const response = await fetch('/api/analyze-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: questionId,
                    answer_text: combinedAnswer,
                    transcript: speechTranscript || combinedAnswer,
                    duration: duration
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayFeedback(data.analysis, data.next_question_available);
            } else {
                alert(data.message || 'Error analyzing answer. Please try again.');
            }
        } catch (error) {
            console.error('Error submitting answer:', error);
            alert('Error submitting answer. Please try again.');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i> Submit Answer';
            }
        }
    }
    
    displayFeedback(analysis, hasNextQuestion) {
        const feedbackArea = document.getElementById('feedback-area');
        const feedbackContent = document.getElementById('feedback-content');
        const nextBtn = document.getElementById('next-question-btn');
        
        if (!feedbackArea || !feedbackContent) return;

        // Build feedback HTML
        let feedbackHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="text-center p-4 bg-blue-50 rounded-lg">
                    <div class="text-2xl font-bold text-blue-700">${analysis.grammar_score}/10</div>
                    <div class="text-sm text-blue-600">Grammar</div>
                </div>
                <div class="text-center p-4 bg-green-50 rounded-lg">
                    <div class="text-2xl font-bold text-green-700">${analysis.relevance_score}/10</div>
                    <div class="text-sm text-green-600">Relevance</div>
                </div>
                <div class="text-center p-4 bg-yellow-50 rounded-lg">
                    <div class="text-2xl font-bold text-yellow-700">${analysis.confidence_score}/10</div>
                    <div class="text-sm text-yellow-600">Confidence</div>
                </div>
                <div class="text-center p-4 bg-purple-50 rounded-lg">
                    <div class="text-2xl font-bold text-purple-700">${analysis.star_score}/10</div>
                    <div class="text-sm text-purple-600">STAR Method</div>
                </div>
            </div>
            
            <div class="p-4 bg-gray-50 rounded-lg mb-4">
                <h4 class="font-bold mb-2">Filler Words:</h4>
                <p>${analysis.filler_words_count} filler words detected (um, uh, like, etc.)</p>
            </div>
            
            <div class="p-4 bg-green-50 rounded-lg mb-4">
                <h4 class="font-bold mb-2">AI Feedback:</h4>
                <p>${analysis.feedback}</p>
            </div>
        `;
        
        if (analysis.suggested_answer) {
            feedbackHTML += `
                <div class="p-4 bg-blue-50 rounded-lg mb-4">
                    <h4 class="font-bold mb-2">Suggested Better Answer:</h4>
                    <p>${analysis.suggested_answer}</p>
                </div>
            `;
        }
        
        if (analysis.cross_question) {
            feedbackHTML += `
                <div class="p-4 bg-yellow-50 rounded-lg">
                    <h4 class="font-bold mb-2">Follow-up Question:</h4>
                    <p>${analysis.cross_question}</p>
                </div>
            `;
        }
        
        feedbackContent.innerHTML = feedbackHTML;
        
        // Update next button text and action
        if (nextBtn) {
            if (hasNextQuestion) {
                nextBtn.innerHTML = 'Next Question <i class="fas fa-arrow-right ml-2"></i>';
                nextBtn.onclick = () => this.nextQuestion();
            } else {
                nextBtn.innerHTML = 'View Performance Feedback <i class="fas fa-chart-bar ml-2"></i>';
                nextBtn.onclick = () => {
                    window.location.href = '/feedback';
                };
            }
        }
        
        // Show feedback area and scroll into view smoothly
        feedbackArea.classList.remove('hidden');
        feedbackArea.scrollIntoView({ behavior: 'smooth' });
    }
    
    async skipQuestion() {
        if (!confirm('Are you sure you want to skip this question?')) {
            return;
        }

        if (window.speechManager) {
            window.speechManager.stop();
            window.speechManager.clearTranscript();
        }
        try {
            const response = await fetch('/api/skip-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question_id: document.getElementById('current-question-id')?.value })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.currentQuestionIndex = data.current_index;
                this.totalQuestions = data.total_questions;
                this.displayQuestion(data.question);
            } else if (data.status === 'completed') {
                this.showCompletionMessage();
            } else {
                alert(data.message || 'Unable to skip question.');
            }
        } catch (error) {
            console.error('Error skipping question:', error);
            alert('Error skipping question. Please try again.');
        }
    }
    
    async nextQuestion() {
        if (window.speechManager) {
            window.speechManager.stop();
            window.speechManager.clearTranscript();
        }
        try {
            const response = await fetch('/api/next-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'advance' })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.currentQuestionIndex = data.current_index;
                this.totalQuestions = data.total_questions;
                this.displayQuestion(data.question);
            } else if (data.status === 'completed') {
                this.showCompletionMessage();
            } else {
                alert(data.message || 'No more questions available.');
            }
        } catch (error) {
            console.error('Error loading next question:', error);
        }
    }
    
    showCompletionMessage() {
        alert('All questions completed! Opening your performance feedback...');
        window.location.href = '/feedback';
    }
    
    finishInterview() {
        if (confirm('Are you sure you want to finish the interview? This will end the session.')) {
            if (window.speechManager) {
                window.speechManager.stop();
            }
            window.location.href = '/feedback';
        }
    }
}

// Initialize interview manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('question-text')) {
        window.interviewManager = new InterviewManager();
    }
});

try:
    import google.generativeai as genai
except Exception as e:
    print(f"WARNING: Could not import google.generativeai ({e}). Running in Mock/Fallback mode.")
    genai = None
import json
import re
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from config import Config

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class AIProcessor:
    def __init__(self):
        self.model = None
        if not Config.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY is not configured. AI functions will use fallback mock responses.")
        else:
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
            except Exception as e:
                print(f"WARNING: Failed to configure Gemini API: {e}. Falling back to mock responses.")
    
    def extract_text_from_resume(self, resume_text):
        """Extract key information from resume text"""
        prompt = f"""
        Extract the following information from this resume text:
        
        {resume_text[:2000]}
        
        Provide as JSON with these keys:
        - name: person's name (if available)
        - skills: list of technical skills
        - experience_years: total years of experience (as float)
        - education: list of educational qualifications
        - projects: list of key projects
        - certifications: list of certifications
        
        Return only JSON, no additional text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            print(f"Error extracting resume text: {e}")
            return {}
    
    def generate_questions(self, resume_data, domain, experience_level, count=10):
        """Generate interview questions based on resume and JD"""
        prompt = f"""
        You are an expert technical interviewer. Generate {count} interview questions for a {experience_level} level {domain} position.
        
        Resume Information:
        {json.dumps(resume_data, indent=2)}
        
        Generate a mix of questions:
        1. 3-4 Technical questions specific to {domain}
        2. 2-3 Behavioral questions (use STAR method)
        3. 2-3 Situational/Scenario-based questions
        4. 1-2 Advanced/Problem-solving questions
        
        For each question, provide:
        - question_text: The actual question
        - question_type: "technical", "behavioral", "situational", or "advanced"
        - difficulty: "easy", "medium", or "hard"
        - category: e.g., "Python", "System Design", "Teamwork"
        - time_allocated: Time in seconds (120 for easy, 180 for medium, 240 for hard)
        
        Return as a JSON list of questions.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                return questions[:count]
            
            # Fallback to some default questions
            return self._get_default_questions(domain, experience_level, count)
        except Exception as e:
            print(f"Error generating questions: {e}")
            return self._get_default_questions(domain, experience_level, count)
    
    def _get_default_questions(self, domain, experience_level, count):
        """Provide default questions if AI fails"""
        default_questions = [
            {
                "question_text": f"Tell me about your experience with {domain}.",
                "question_type": "behavioral",
                "difficulty": "easy",
                "category": domain,
                "time_allocated": 120
            },
            {
                "question_text": "Describe a challenging project you worked on and how you overcame obstacles.",
                "question_type": "behavioral",
                "difficulty": "medium",
                "category": "Project Management",
                "time_allocated": 180
            },
            {
                "question_text": "What are your strengths and weaknesses?",
                "question_type": "behavioral",
                "difficulty": "easy",
                "category": "Self Assessment",
                "time_allocated": 120
            }
        ]
        return default_questions[:count]
    
    def analyze_answer(self, question, answer, transcript):
        """Analyze candidate's answer"""
        filler_words = ['um', 'uh', 'ah', 'er', 'like', 'you know', 'so', 'well']
        # Count whole filler words/phrases only.  Substring matching can count
        # ordinary words such as "some" or "wellbeing" by mistake.
        filler_count = sum(
            len(re.findall(r'(?<!\w)' + re.escape(word) + r'(?!\w)', transcript.lower()))
            for word in filler_words
        )
        
        # Calculate sentiment using TextBlob
        blob = TextBlob(transcript)
        sentiment_score = blob.sentiment.polarity  # -1 to 1
        
        # Generate AI feedback
        prompt = f"""
        Analyze this interview answer and provide personalized feedback:

        Question: {question}
        Candidate's Answer: {answer}

        First, analyze the candidate's actual answer and identify:
        1. What they did well in their response
        2. What specific aspects could be improved
        3. What key points or examples they mentioned

        Then provide detailed analysis as JSON with these keys:
        - grammar_score: 0-10 score for grammar and sentence structure
        - relevance_score: 0-10 score for relevance to question
        - star_score: 0-10 score for STAR method usage (Situation, Task, Action, Result)
        - detailed_feedback: Specific, actionable feedback based on their actual answer
        - suggested_better_answer: A personalized improvement of their answer that builds on what they said, not a generic response. Make it specific to their content and context.
        - confidence_indicator: "low", "medium", or "high" based on answer quality

        For the suggested_better_answer, DO NOT provide a generic template. Instead:
        - Take their actual answer as a starting point
        - Improve their structure using STAR method
        - Add relevant details they might have missed
        - Keep their core message but make it more professional and complete
        - Make it sound natural, not robotic

        Also evaluate if the candidate needs a cross-question because:
        1. Answer is too short (< 30 words)
        2. Answer is vague or unclear
        3. Answer shows lack of depth

        If cross-question is needed, provide:
        - needs_cross_question: true
        - cross_question: A follow-up question to probe deeper

        Return only JSON, no additional text.
        """
        
        try:
            if not self.model:
                raise RuntimeError("Gemini model is not available")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Calculate confidence score (0-10)
                confidence_score = (
                    analysis.get('relevance_score', 5) * 0.3 +
                    analysis.get('star_score', 5) * 0.3 +
                    (1 + sentiment_score) * 5 * 0.2 +  # Convert -1 to 1 into 0-10
                    max(0, 10 - (filler_count * 0.5)) * 0.2  # Penalize filler words
                )
                
                return {
                    'grammar_score': analysis.get('grammar_score', 5),
                    'relevance_score': analysis.get('relevance_score', 5),
                    'star_score': analysis.get('star_score', 5),
                    'confidence_score': min(10, max(0, confidence_score)),
                    'filler_words_count': filler_count,
                    'feedback': analysis.get('detailed_feedback', 'No specific feedback available.'),
                    'suggested_answer': analysis.get('suggested_better_answer', ''),
                    'needs_cross_question': analysis.get('needs_cross_question', False),
                    'cross_question': analysis.get('cross_question', '') if analysis.get('needs_cross_question') else ''
                }
        except Exception as e:
            print(f"Error analyzing answer: {e}")
        
        # Gemini may be unavailable (for example, due to a bad/expired key or a
        # quota error).  The local evaluator must still assess the actual answer
        # instead of returning the same hard-coded result for every submission.
        return self._analyze_answer_locally(question, answer, transcript, filler_count)

    def _analyze_answer_locally(self, question, answer, transcript, filler_count):
        """Return answer-sensitive feedback when the remote AI service is unavailable."""
        answer_words = re.findall(r"[a-zA-Z0-9']+", answer.lower())
        question_words = re.findall(r"[a-zA-Z0-9']+", question.lower())
        ignored_words = {
            'about', 'and', 'are', 'can', 'could', 'describe', 'did', 'do', 'for',
            'from', 'have', 'how', 'in', 'is', 'me', 'of', 'on', 'or', 'the', 'to',
            'was', 'what', 'with', 'would', 'you', 'your', 'tell', 'experience'
        }
        keywords = {word for word in question_words if len(word) > 2 and word not in ignored_words}
        matched_keywords = sorted(keywords.intersection(answer_words))
        word_count = len(answer_words)
        sentence_count = len([part for part in re.split(r'[.!?]+', answer) if part.strip()])

        # Relevance is driven mainly by the question's important words, with a
        # small credit for enough detail.  An unrelated, long answer cannot score
        # well simply because it contains many words.
        keyword_coverage = len(matched_keywords) / max(1, len(keywords))
        detail_score = min(1.0, word_count / 80)
        behavioral_question = bool(
            set(question_words).intersection({'challenging', 'project', 'obstacles', 'team', 'conflict', 'strengths', 'weaknesses'})
        )
        behavioral_evidence = {
            'project', 'team', 'responsible', 'implemented', 'built', 'created', 'led',
            'improved', 'result', 'outcome', 'increased', 'reduced', 'delivered'
        }
        behavioral_coverage = len(set(answer_words).intersection(behavioral_evidence)) / len(behavioral_evidence)
        # Behavioral questions are often answered with natural wording that does
        # not repeat words such as "challenge" or "obstacle".  Credit clear
        # project/action/result evidence as well as literal keyword matches.
        relevance_evidence = max(keyword_coverage, behavioral_coverage * 1.8) if behavioral_question else keyword_coverage
        relevance_score = round(max(1, min(10, 1 + relevance_evidence * 7 + detail_score * 2)))

        sentence_starts = re.findall(r'(?:^|[.!?]\s+)([A-Za-z])', answer)
        capitalized_starts = sum(letter.isupper() for letter in sentence_starts)
        grammar_score = 3
        if word_count >= 8:
            grammar_score += 2
        if sentence_count >= 2:
            grammar_score += 1
        if sentence_count and capitalized_starts == sentence_count:
            grammar_score += 1
        if re.search(r'[.!?]$', answer.strip()):
            grammar_score += 1
        grammar_score -= min(3, filler_count // 2)
        grammar_score = max(1, min(10, grammar_score))

        star_markers = {
            'situation': {'situation', 'context', 'when', 'while', 'project', 'team'},
            'task': {'task', 'goal', 'needed', 'responsible', 'challenge'},
            'action': {'action', 'implemented', 'built', 'created', 'led', 'improved', 'developed', 'analyzed'},
            'result': {'result', 'outcome', 'increased', 'reduced', 'improved', 'delivered', 'saved', 'percent'}
        }
        answer_word_set = set(answer_words)
        star_parts = sum(bool(answer_word_set.intersection(markers)) for markers in star_markers.values())
        number_of_metrics = len(re.findall(r'\b\d+(?:\.\d+)?%?\b', answer))
        star_score = min(10, 1 + star_parts * 2 + min(1, number_of_metrics))

        confidence_score = round(max(1, min(
            10,
            2 + min(3, word_count / 25) + min(2, sentence_count / 2)
            + keyword_coverage * 2 - min(2, filler_count * 0.25)
        )))

        topic = ', '.join(sorted(keywords)[:3]) or 'the main topic in the question'
        if relevance_score <= 3:
            feedback = (
                f"Your answer has {word_count} words but does not address the question's key topic "
                f"({topic}). Give a direct answer before adding background or examples."
            )
        else:
            matched = ', '.join(matched_keywords[:4])
            feedback = (
                f"You addressed {matched}. To make the answer stronger, explain your specific role, "
                "what you did, and the measurable result."
            )

        suggested_answer = (
            f"Start by directly addressing {topic}. Then describe the situation, your responsibility, "
            "the actions you took, and the outcome with a concrete result."
        )
        needs_cross_question = word_count < 30 or relevance_score <= 3
        cross_question = (
            f"How does your answer relate to {topic}? Please give one specific example."
            if needs_cross_question else ''
        )

        return {
            'grammar_score': grammar_score,
            'relevance_score': relevance_score,
            'star_score': star_score,
            'confidence_score': confidence_score,
            'filler_words_count': filler_count,
            'feedback': feedback,
            'suggested_answer': suggested_answer,
            'needs_cross_question': needs_cross_question,
            'cross_question': cross_question
        }
    
    def generate_cross_question(self, question, answer):
        """Generate a cross-question when answer is insufficient"""
        prompt = f"""
        Based on this question and insufficient answer, generate a probing follow-up question:
        
        Original Question: {question}
        Candidate's Answer: {answer}
        
        The answer was too short/vague. Generate ONE follow-up question that will:
        1. Probe deeper into the topic
        2. Ask for specific examples
        3. Challenge the candidate constructively
        
        Return only the question text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return "Could you provide a more detailed example or elaborate on that point?"
    
    def generate_final_report(self, session_data, answers_data):
        """Generate final performance report"""
        prompt = f"""
        Generate a comprehensive interview performance report.
        
        Interview Session Details:
        - Domain: {session_data.get('domain')}
        - Experience Level: {session_data.get('experience_level')}
        
        Performance Analysis:
        {json.dumps(answers_data, indent=2)}
        
        Provide a detailed report as JSON with:
        - overall_score: 0-100 overall performance
        - strengths: list of 3-5 strengths
        - weaknesses: list of 3-5 areas to improve
        - communication_score: 0-10 for communication skills
        - technical_score: 0-10 for technical knowledge
        - confidence_score: 0-10 for confidence level
        - improvement_plan: 5-7 specific actionable recommendations
        - final_verdict: "Strong Candidate", "Needs Improvement", or "Not Ready"
        - detailed_analysis: Paragraph summarizing performance
        
        Return only JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error generating report: {e}")
        
        # Fallback report
        return {
            'overall_score': 70,
            'strengths': ['Basic technical knowledge', 'Clear communication'],
            'weaknesses': ['Need more examples', 'Improve STAR method usage'],
            'communication_score': 7,
            'technical_score': 6,
            'confidence_score': 6,
            'improvement_plan': [
                'Practice more behavioral questions',
                'Use STAR method consistently',
                'Reduce filler words',
                'Prepare specific examples'
            ],
            'final_verdict': 'Needs Improvement',
            'detailed_analysis': 'Basic performance with room for improvement.'
        }

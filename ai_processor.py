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
    
    def generate_questions(self, resume_data, job_description, domain, experience_level, count=10):
        """Generate interview questions based on resume and JD"""
        prompt = f"""
        You are an expert technical interviewer. Generate {count} interview questions for a {experience_level} level {domain} position.
        
        Resume Information:
        {json.dumps(resume_data, indent=2)}
        
        Job Description:
        {job_description[:1000]}
        
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
        filler_count = sum(transcript.lower().count(word) for word in filler_words)
        
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
        
        # Fallback analysis
        return {
            'grammar_score': 6,
            'relevance_score': 6,
            'star_score': 5,
            'confidence_score': 6,
            'filler_words_count': filler_count,
            'feedback': 'Basic analysis only. AI service unavailable.',
            'suggested_answer': 'Try to provide more specific examples and structure your answer using the STAR method.',
            'needs_cross_question': len(answer.split()) < 30,
            'cross_question': 'Could you elaborate more on that point?' if len(answer.split()) < 30 else ''
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
    
    def evaluate_code(self, problem_statement, user_code, language='python'):
        """Evaluate submitted code"""
        prompt = f"""
        Evaluate this coding solution:
        
        Problem: {problem_statement}
        Language: {language}
        Code:
        {user_code}
        
        Provide evaluation as JSON with:
        - logic_score: 0-10 for logical correctness
        - efficiency_score: 0-10 for time/space efficiency
        - clarity_score: 0-10 for code readability and structure
        - test_cases_passed: estimated test cases passed (0-5)
        - total_test_cases: 5 (assumed)
        - detailed_feedback: Specific feedback on improvements
        - suggested_improvements: How to improve the code
        - time_complexity: Estimated time complexity
        - space_complexity: Estimated space complexity
        
        Return only JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                return evaluation
        except Exception as e:
            print(f"Error evaluating code: {e}")
        
        # Fallback evaluation
        return {
            'logic_score': 6,
            'efficiency_score': 6,
            'clarity_score': 6,
            'test_cases_passed': 3,
            'total_test_cases': 5,
            'detailed_feedback': 'Basic evaluation only. AI service unavailable.',
            'suggested_improvements': 'Add more comments and handle edge cases.',
            'time_complexity': 'O(n)',
            'space_complexity': 'O(1)'
        }
    
    def generate_problem_statement(self, domain, difficulty='medium'):
        """Generate a coding problem statement"""
        prompt = f"""
        Generate a {difficulty} level coding problem for {domain} domain.
        The problem should be solvable in 10-15 minutes and test:
        1. Basic programming logic
        2. Problem-solving approach
        3. Clean code practices
        
        Provide as JSON with:
        - problem_statement: Clear description of the problem
        - example_input: Example input
        - example_output: Expected output for example
        - constraints: Any constraints (time/space)
        - hints: 1-2 hints for solving
        
        Return only JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Default problem
        return {
            'problem_statement': 'Write a function to find the maximum element in a list.',
            'example_input': '[1, 5, 3, 9, 2]',
            'example_output': '9',
            'constraints': 'Time complexity should be O(n)',
            'hints': ['Iterate through the list while keeping track of maximum']
        }
    
    def generate_final_report(self, session_data, answers_data, coding_data):
        """Generate final performance report"""
        prompt = f"""
        Generate a comprehensive interview performance report.
        
        Interview Session Details:
        - Domain: {session_data.get('domain')}
        - Experience Level: {session_data.get('experience_level')}
        
        Performance Analysis:
        {json.dumps(answers_data, indent=2)}
        
        Coding Test Results:
        {json.dumps(coding_data, indent=2) if coding_data else 'No coding test'}
        
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
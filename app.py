from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import PyPDF2

from config import Config
from database import init_db, save_interview_session, save_question, save_answer, save_coding_test
from ai_processor import AIProcessor
from code_sandbox import CodeSandbox
from report_generator import ReportGenerator

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize session
Session(app)

# Initialize database
init_db()

# Initialize AI processor
ai_processor = AIProcessor()

# Create upload directories
os.makedirs('uploads/resumes', exist_ok=True)
os.makedirs('uploads/job_descriptions', exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    """Extract text from PDF file"""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/mic-test')
def mic_test():
    """Microphone test page"""
    return render_template('mic_test.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload resume and job description"""
    if request.method == 'POST':
        # Handle file uploads
        resume_file = request.files.get('resume')
        jd_file = request.files.get('job_description')
        jd_text = request.form.get('job_description_text', '')
        
        resume_text = ""
        jd_final_text = ""
        
        # Process resume
        if resume_file and allowed_file(resume_file.filename):
            filename = secure_filename(resume_file.filename)
            filepath = os.path.join('uploads/resumes', filename)
            resume_file.save(filepath)
            
            # Extract text from resume
            if filename.endswith('.pdf'):
                resume_text = extract_text_from_pdf(filepath)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    resume_text = f.read()
        
        # Process job description
        if jd_file and allowed_file(jd_file.filename):
            filename = secure_filename(jd_file.filename)
            filepath = os.path.join('uploads/job_descriptions', filename)
            jd_file.save(filepath)
            
            if filename.endswith('.pdf'):
                jd_final_text = extract_text_from_pdf(filepath)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    jd_final_text = f.read()
        else:
            jd_final_text = jd_text
        
        # Store in session
        session['resume_text'] = resume_text
        session['job_description'] = jd_final_text
        
        return redirect(url_for('setup_interview'))
    
    return render_template('upload.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup_interview():
    """Set up interview parameters"""
    if request.method == 'POST':
        domain = request.form.get('domain')
        experience_level = request.form.get('experience_level')
        
        # Store in session
        session['domain'] = domain
        session['experience_level'] = experience_level
        
        return redirect(url_for('start_interview'))
    
    return render_template('setup.html')

@app.route('/start-interview')
def start_interview():
    """Start interview session"""
    # Extract resume data
    resume_text = session.get('resume_text', '')
    resume_data = ai_processor.extract_text_from_resume(resume_text)
    
    # Generate questions
    questions = ai_processor.generate_questions(
        resume_data=resume_data,
        job_description=session.get('job_description', ''),
        domain=session.get('domain', 'Software Engineering'),
        experience_level=session.get('experience_level', 'Entry'),
        count=8
    )
    
    # Save session to database
    session_data = {
        'user_id': 1,  # Default user for demo
        'domain': session.get('domain'),
        'experience_level': session.get('experience_level'),
        'resume_text': session.get('resume_text', ''),
        'job_description': session.get('job_description', '')
    }
    
    session_id = save_interview_session(session_data)
    session['session_id'] = session_id
    
    # Save questions
    question_ids = []
    for q in questions:
        q_id = save_question(session_id, q)
        question_ids.append(q_id)
        q['id'] = q_id
    
    session['questions'] = questions
    session['current_question_index'] = 0
    session['answers'] = []
    
    return render_template('interview.html', 
                         questions=questions,
                         current_index=0,
                         session_id=session_id)

@app.route('/api/next-question', methods=['POST'])
def next_question():
    """Get question (current, advance to next, or skip)"""
    data = request.get_json(silent=True) or {}
    action = data.get('action', 'get_current')  # 'get_current', 'advance', 'skip'

    questions = session.get('questions', [])
    current_index = session.get('current_question_index', 0)

    if action in ('advance', 'skip'):
        current_index += 1
        session['current_question_index'] = current_index

    if current_index >= len(questions):
        return jsonify({
            'status': 'completed',
            'message': 'All questions completed',
            'current_index': current_index,
            'total_questions': len(questions)
        })

    question = questions[current_index]

    return jsonify({
        'status': 'success',
        'question': question,
        'current_index': current_index,
        'total_questions': len(questions)
    })

@app.route('/api/skip-question', methods=['POST'])
def skip_question():
    """Skip current question and advance to next"""
    questions = session.get('questions', [])
    current_index = session.get('current_question_index', 0)

    current_index += 1
    session['current_question_index'] = current_index

    if current_index >= len(questions):
        return jsonify({
            'status': 'completed',
            'message': 'All questions completed',
            'current_index': current_index,
            'total_questions': len(questions)
        })

    question = questions[current_index]

    return jsonify({
        'status': 'success',
        'question': question,
        'current_index': current_index,
        'total_questions': len(questions)
    })

@app.route('/api/analyze-answer', methods=['POST'])
def analyze_answer():
    """Analyze candidate's answer"""
    data = request.json or {}
    question_id = data.get('question_id')
    answer_text = data.get('answer_text', '')
    transcript = data.get('transcript', '')
    duration = data.get('duration', 0)
    
    questions = session.get('questions', [])
    current_index = session.get('current_question_index', 0)
    
    # Find matching question by question_id or fallback to current_question_index
    current_question = None
    question_idx = current_index
    if question_id:
        for idx, q in enumerate(questions):
            if str(q.get('id')) == str(question_id):
                current_question = q
                question_idx = idx
                break

    if current_question is None and 0 <= current_index < len(questions):
        current_question = questions[current_index]
        question_idx = current_index

    if current_question:
        # Analyze answer
        analysis = ai_processor.analyze_answer(
            question=current_question.get('question_text', ''),
            answer=answer_text,
            transcript=transcript
        )
        
        # Save answer
        answer_data = {
            'question_id': current_question.get('id', question_id),
            'session_id': session.get('session_id'),
            'answer_text': answer_text,
            'transcript': transcript,
            'duration': duration,
            'grammar_score': analysis.get('grammar_score', 0),
            'relevance_score': analysis.get('relevance_score', 0),
            'confidence_score': analysis.get('confidence_score', 0),
            'star_score': analysis.get('star_score', 0),
            'filler_words_count': analysis.get('filler_words_count', 0),
            'feedback': analysis.get('feedback', ''),
            'cross_question_asked': analysis.get('needs_cross_question', False)
        }
        
        answer_id = save_answer(answer_data)
        
        # Store in session
        answer_data['id'] = answer_id
        answer_data['question_text'] = current_question.get('question_text', '')
        if 'answers' not in session or not isinstance(session['answers'], list):
            session['answers'] = []
        session['answers'].append(answer_data)
        
        has_next = (question_idx + 1) < len(questions)
        response = {
            'status': 'success',
            'analysis': analysis,
            'next_question_available': has_next,
            'current_index': question_idx,
            'total_questions': len(questions)
        }
        
        if analysis.get('needs_cross_question'):
            response['cross_question'] = analysis.get('cross_question', '')
        
        return jsonify(response)
    
    return jsonify({'status': 'error', 'message': 'Question not found or session expired'})

@app.route('/coding-test')
def coding_test():
    """Coding test page"""
    # Generate coding problem
    domain = session.get('domain', 'Software Engineering')
    problem = ai_processor.generate_problem_statement(domain)
    
    session['coding_problem'] = problem
    
    return render_template('coding.html', problem=problem)

@app.route('/api/evaluate-code', methods=['POST'])
def evaluate_code():
    """Evaluate submitted code"""
    data = request.json
    user_code = data.get('code', '')
    time_taken = data.get('time_taken', 0)
    
    problem = session.get('coding_problem', {})
    
    # Basic safety check
    if not CodeSandbox.is_code_safe(user_code):
        return jsonify({
            'status': 'error',
            'message': 'Code contains potentially unsafe operations'
        })
    
    # Execute code
    output, error, success = CodeSandbox.execute_python_code(user_code)
    
    # AI evaluation
    evaluation = ai_processor.evaluate_code(
        problem_statement=problem.get('problem_statement', ''),
        user_code=user_code
    )
    
    # Save coding test
    test_data = {
        'session_id': session.get('session_id'),
        'problem_statement': problem.get('problem_statement', ''),
        'language': 'python',
        'user_code': user_code,
        'test_cases_passed': evaluation.get('test_cases_passed', 0),
        'total_test_cases': evaluation.get('total_test_cases', 5),
        'efficiency_score': evaluation.get('efficiency_score', 0),
        'clarity_score': evaluation.get('clarity_score', 0),
        'logic_score': evaluation.get('logic_score', 0),
        'feedback': evaluation.get('detailed_feedback', ''),
        'time_taken': time_taken
    }
    
    test_id = save_coding_test(test_data)
    session['coding_test'] = test_data
    
    return jsonify({
        'status': 'success',
        'evaluation': evaluation,
        'execution': {
            'output': output,
            'error': error,
            'success': success
        }
    })

@app.route('/feedback')
def feedback():
    """Show feedback page"""
    answers = session.get('answers', [])

    # Calculate averages
    if answers:
        avg_scores = {
            'grammar': sum(a.get('grammar_score', 0) for a in answers) / len(answers),
            'relevance': sum(a.get('relevance_score', 0) for a in answers) / len(answers),
            'confidence': sum(a.get('confidence_score', 0) for a in answers) / len(answers),
            'star': sum(a.get('star_score', 0) for a in answers) / len(answers)
        }
    else:
        avg_scores = {'grammar': 0, 'relevance': 0, 'confidence': 0, 'star': 0}

    return render_template('feedback.html',
                         answers=answers,
                         avg_scores=avg_scores)

@app.route('/generate-report')
def generate_report():
    """Generate and display final report"""
    # Get session data
    session_data = {
        'domain': session.get('domain', 'Software Engineering'),
        'experience_level': session.get('experience_level', 'Entry Level')
    }

    # Get answers data
    answers_data = session.get('answers', [])

    # Get coding test data
    coding_data = session.get('coding_test', {})

    # Generate final report using AI
    report = ai_processor.generate_final_report(session_data, answers_data, coding_data)

    # Store report in session for potential download
    session['final_report'] = report

    return render_template('report.html',
                         report=report,
                         answers=answers_data,
                         coding_test=coding_data if coding_data else None)



@app.route('/api/speech-status', methods=['POST'])
def speech_status():
    """Update speech recognition status"""
    data = request.json
    session['speech_active'] = data.get('active', False)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
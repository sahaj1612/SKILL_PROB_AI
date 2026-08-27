import sqlite3
import json
from datetime import datetime
from config import Config

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Interview sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            domain TEXT,
            experience_level TEXT,
            resume_text TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            total_score REAL,
            feedback_summary TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            question_text TEXT,
            question_type TEXT,
            difficulty TEXT,
            category TEXT,
            time_allocated INTEGER,
            FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
        )
    ''')
    
    # Answers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            session_id INTEGER,
            answer_text TEXT,
            transcript TEXT,
            duration INTEGER,
            grammar_score REAL,
            relevance_score REAL,
            confidence_score REAL,
            star_score REAL,
            filler_words_count INTEGER,
            feedback TEXT,
            cross_question_asked BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions (id),
            FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
        )
    ''')
    
    # Performance history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id INTEGER,
            date DATE,
            overall_score REAL,
            communication_score REAL,
            technical_score REAL,
            confidence_score REAL,
            areas_to_improve TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_interview_session(session_data):
    """Save interview session data"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO interview_sessions 
        (user_id, domain, experience_level, resume_text, start_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        session_data['user_id'],
        session_data['domain'],
        session_data['experience_level'],
        session_data['resume_text'],
        datetime.now()
    ))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return session_id

def save_question(session_id, question_data):
    """Save generated question"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO questions 
        (session_id, question_text, question_type, difficulty, category, time_allocated)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        question_data['question_text'],
        question_data['question_type'],
        question_data['difficulty'],
        question_data['category'],
        question_data['time_allocated']
    ))
    
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return question_id

def save_answer(answer_data):
    """Save answer with analysis"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO answers 
        (question_id, session_id, answer_text, transcript, duration, 
         grammar_score, relevance_score, confidence_score, star_score, 
         filler_words_count, feedback, cross_question_asked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        answer_data['question_id'],
        answer_data['session_id'],
        answer_data['answer_text'],
        answer_data['transcript'],
        answer_data['duration'],
        answer_data['grammar_score'],
        answer_data['relevance_score'],
        answer_data['confidence_score'],
        answer_data['star_score'],
        answer_data['filler_words_count'],
        answer_data['feedback'],
        answer_data.get('cross_question_asked', False)
    ))
    
    answer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return answer_id

def get_session_performance(session_id):
    """Get performance data for a session"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get answers for this session
    cursor.execute('''
        SELECT * FROM answers 
        WHERE session_id = ?
    ''', (session_id,))
    
    answers = [dict(row) for row in cursor.fetchall()]
    
    # Get session info
    cursor.execute('''
        SELECT * FROM interview_sessions
        WHERE id = ?
    ''', (session_id,))

    session_row = cursor.fetchone()
    session = dict(session_row) if session_row else None
    
    conn.close()
    
    return {
        'session': session,
        'answers': answers
    }

def get_user_history(user_id):
    """Get user's performance history"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ph.*, is.domain, is.experience_level
        FROM performance_history ph
        JOIN interview_sessions is ON ph.session_id = is.id
        WHERE ph.user_id = ?
        ORDER BY ph.date DESC
    ''', (user_id,))
    
    history = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return history

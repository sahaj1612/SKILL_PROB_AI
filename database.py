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
            email TEXT UNIQUE,
            display_name TEXT,
            provider TEXT,
            provider_user_id TEXT,
            role TEXT NOT NULL DEFAULT 'candidate',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Existing demo databases may already have the original, smaller users table.
    # Add the OAuth fields safely when upgrading in place.
    existing_columns = {row['name'] for row in cursor.execute("PRAGMA table_info(users)")}
    for column, definition in (
        ('email', 'TEXT'), ('display_name', 'TEXT'), ('provider', 'TEXT'),
        ('provider_user_id', 'TEXT'), ('role', "TEXT NOT NULL DEFAULT 'candidate'")
    ):
        if column not in existing_columns:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {column} {definition}')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_provider_identity ON users(provider, provider_user_id)')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oauth_identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            provider_user_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider, provider_user_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Preserve OAuth users created by earlier versions of the schema.
    cursor.execute('''
        INSERT OR IGNORE INTO oauth_identities (user_id, provider, provider_user_id)
        SELECT id, provider, provider_user_id FROM users
        WHERE provider IS NOT NULL AND provider_user_id IS NOT NULL
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

def list_interview_sessions():
    """Return interview sessions with candidate details and summary scores for review."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT interview_sessions.id, interview_sessions.domain,
               interview_sessions.experience_level, interview_sessions.start_time,
               interview_sessions.end_time, users.display_name, users.email,
               COUNT(answers.id) AS answer_count,
               ROUND(AVG(answers.grammar_score), 1) AS grammar_score,
               ROUND(AVG(answers.relevance_score), 1) AS relevance_score,
               ROUND(AVG(answers.confidence_score), 1) AS confidence_score,
               ROUND(AVG(answers.star_score), 1) AS star_score
        FROM interview_sessions
        LEFT JOIN users ON users.id = interview_sessions.user_id
        LEFT JOIN answers ON answers.session_id = interview_sessions.id
        GROUP BY interview_sessions.id
        ORDER BY interview_sessions.start_time DESC
    ''')
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

def get_interview_review(session_id):
    """Return one session, its candidate, questions, and scored answers for reviewers."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT interview_sessions.id, interview_sessions.domain,
               interview_sessions.experience_level, interview_sessions.start_time,
               interview_sessions.end_time, users.display_name, users.email
        FROM interview_sessions
        LEFT JOIN users ON users.id = interview_sessions.user_id
        WHERE interview_sessions.id = ?
    ''', (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        conn.close()
        return None
    cursor.execute('''
        SELECT answers.*, questions.question_text, questions.question_type,
               questions.difficulty
        FROM answers
        LEFT JOIN questions ON questions.id = answers.question_id
        WHERE answers.session_id = ?
        ORDER BY answers.created_at ASC, answers.id ASC
    ''', (session_id,))
    answers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {'session': dict(session_row), 'answers': answers}

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

def get_or_create_oauth_user(provider, provider_user_id, email, display_name, role='candidate'):
    """Find an OAuth identity or create a user for it."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT users.* FROM users
           JOIN oauth_identities ON oauth_identities.user_id = users.id
           WHERE oauth_identities.provider = ? AND oauth_identities.provider_user_id = ?''',
        (provider, str(provider_user_id))
    )
    user = cursor.fetchone()
    if user:
        cursor.execute(
            '''UPDATE users
               SET email = ?, display_name = ?,
                   role = CASE WHEN ? = 'admin' THEN 'admin' ELSE role END
               WHERE id = ?''',
            (email, display_name, role, user['id'])
        )
        conn.commit()
        user_id = user['id']
    else:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        if user:
            user_id = user['id']
            cursor.execute(
                '''UPDATE users SET display_name = ?,
                   role = CASE WHEN ? = 'admin' THEN 'admin' ELSE role END
                   WHERE id = ?''',
                (display_name, role, user_id)
            )
        else:
            username = f'{provider}_{provider_user_id}'
            cursor.execute(
                '''INSERT INTO users (username, email, display_name, provider, provider_user_id, role)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (username, email, display_name, provider, str(provider_user_id), role)
            )
            user_id = cursor.lastrowid
        cursor.execute(
            'INSERT INTO oauth_identities (user_id, provider, provider_user_id) VALUES (?, ?, ?)',
            (user_id, provider, str(provider_user_id))
        )
        conn.commit()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    result = dict(cursor.fetchone())
    conn.close()
    return result

def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def list_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, display_name, provider, role, created_at FROM users ORDER BY created_at DESC')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def update_user_role(user_id, role):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
    changed = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return changed

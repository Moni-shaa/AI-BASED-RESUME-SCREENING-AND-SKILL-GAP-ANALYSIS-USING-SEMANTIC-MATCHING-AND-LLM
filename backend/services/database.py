import sqlite3
import json
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='resume_screener.db'):
        self.db_path = db_path
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create candidates table
        cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        resume_text TEXT NOT NULL,
        job_description TEXT,
        analysis TEXT NOT NULL,
        shortlisted INTEGER,

        skills TEXT,
        jd_skills TEXT,
        matched_skills TEXT,
        missing_skills TEXT,
        match_score REAL,
        semantic_score REAL,      -- ✅ ADD
        final_score REAL,                

        priority_map TEXT,
        score_breakdown TEXT,
        decision_reason TEXT,

        upload_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
        
        # Create chat_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id)
            )
        ''')
        
        # Create hr_chat_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hr_chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_candidate(self, candidate_data):
        """Save candidate data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO candidates (
    filename, file_path, resume_text, job_description, 
    analysis, shortlisted,
    skills, jd_skills, matched_skills, missing_skills, match_score,
    semantic_score,final_score,priority_map, score_breakdown, decision_reason,
    upload_date
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
        ''', (
            candidate_data['filename'],
            candidate_data['file_path'],
            candidate_data['resume_text'],
            candidate_data.get('job_description', ''),
            json.dumps(candidate_data['analysis']),
            int(candidate_data.get('shortlisted', 0)),

            json.dumps(candidate_data.get('skills', [])),
            json.dumps(candidate_data.get('jd_skills', [])),
            json.dumps(candidate_data.get('matched_skills', [])),
            json.dumps(candidate_data.get('missing_skills', [])),
            candidate_data.get('match_score'),
            candidate_data.get('semantic_score'),   # ✅ ADD
            candidate_data.get('final_score'), 

            json.dumps(candidate_data.get('priority_map', {})),
            json.dumps(candidate_data.get('score_breakdown', {})),
            candidate_data.get('decision_reason'),

            candidate_data['upload_date']
        ))
        
        candidate_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return candidate_id
    
    def get_candidate(self, candidate_id):
        """Get candidate by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_candidates(self):
        """Get all candidates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM candidates 
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row):
        """Convert database row to dictionary"""
        return {
            'id': row[0],
            'filename': row[1],
            'file_path': row[2],
            'resume_text': row[3],
            'job_description': row[4],
            'analysis': json.loads(row[5]) if row[5] else {},

            'shortlisted': bool(row[6]),

            'skills': json.loads(row[7]) if row[7] else [],
            'jd_skills': json.loads(row[8]) if row[8] else [],
            'matched_skills': json.loads(row[9]) if row[9] else [],
            'missing_skills': json.loads(row[10]) if row[10] else [],
            'match_score': row[11],
'semantic_score': row[12],   # ✅ NEW
'final_score': row[13],      # ✅ NEW
'priority_map': json.loads(row[14]) if row[14] else {},
'score_breakdown': json.loads(row[15]) if row[15] else {},
'decision_reason': row[16],
'upload_date': row[17],
'created_at': row[18]
        }
    
    def save_chat_message(self, candidate_id, message, response):
        """Save chat message and response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history (candidate_id, message, response)
            VALUES (?, ?, ?)
        ''', (candidate_id, message, response))
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, candidate_id):
        """Get chat history for a candidate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response, timestamp 
            FROM chat_history 
            WHERE candidate_id = ?
            ORDER BY timestamp ASC
        ''', (candidate_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {'message': row[0], 'response': row[1], 'timestamp': row[2]}
            for row in rows
        ]
    
    def save_hr_chat_message(self, message, response):
        """Save HR chat message and response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO hr_chat_history (message, response)
            VALUES (?, ?)
        ''', (message, response))
        
        conn.commit()
        conn.close()
    
    def get_hr_chat_history(self, limit=50):
        """Get HR chat history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response, timestamp 
            FROM hr_chat_history 
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {'message': row[0], 'response': row[1], 'timestamp': row[2]}
            for row in reversed(rows)
        ]
    
    def get_statistics(self):
        """Get application statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM candidates')
        total_candidates = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN json_extract(analysis, '$.category') = 'Highly Qualified' THEN 1 ELSE 0 END),
                SUM(CASE WHEN json_extract(analysis, '$.category') = 'Qualified' THEN 1 ELSE 0 END),
                SUM(CASE WHEN json_extract(analysis, '$.category') = 'Not a Fit' THEN 1 ELSE 0 END)
            FROM candidates
        ''')
        categories = cursor.fetchone()
        
        cursor.execute('''
            SELECT 
                AVG(CAST(json_extract(analysis, '$.overall_score') AS FLOAT)),
                AVG(CAST(json_extract(analysis, '$.skills_match') AS FLOAT))
            FROM candidates
        ''')
        scores = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM candidates 
            WHERE created_at >= datetime('now', '-7 days')
        ''')
        recent_uploads = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_candidates': total_candidates,
            'categories': {
                'highly_qualified': categories[0] or 0,
                'qualified': categories[1] or 0,
                'not_fit': categories[2] or 0
            },
            'average_scores': {
                'overall_score': round(scores[0] or 0, 2),
                'skills_match': round(scores[1] or 0, 2)
            },
            'recent_uploads': recent_uploads
        }
    
    def update_setting(self, key, value):
        """Update or insert a setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key, default=None):
        """Get a setting value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else default
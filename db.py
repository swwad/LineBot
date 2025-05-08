import sqlite3
from datetime import datetime

DB_PATH = 'chat_log.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            user_id TEXT,
            msg_type TEXT,
            user_content TEXT,
            reply_content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_to_db(user_id, user_content, reply_content, msg_type):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO chat_log (time, user_id, msg_type, user_content, reply_content)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, user_id, msg_type, user_content, reply_content))
    conn.commit()
    conn.close() 
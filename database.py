import sqlite3
def get_connection():
    connection = sqlite3.connect("assistant.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection



def create_database():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_content TEXT NOT NULL,
        file_type TEXT NOT NULL,
        chunk_header TEXT NOT NULL,
        embedded_string TEXT NOT NULL,
        FOREIGN KEY (doc_id) REFERENCES docs(id) ON DELETE CASCADE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        doc_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (doc_id) REFERENCES docs(id) ON DELETE CASCADE
    )
    """)
    connection.close()

def save_message(role, content, doc_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO messages(role, content, doc_id)
    VALUES (?, ?, ?)
    """,
    (role, content, doc_id)
)
    connection.commit()
    connection.close()

def save_doc(file_name, file_content, file_type, chunk_header, embedded_string, doc_id):
    if not file_content or not file_content.strip():
        return
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO documents(file_name, file_content, file_type, chunk_header, embedded_string, doc_id)
    VALUES (?, ?, ?, ?, ?, ?)  
    """,
    (file_name, file_content, file_type, chunk_header, embedded_string, doc_id)
) #TO DO populated by doc selector
    connection.commit()
    connection.close()

def get_messages(doc_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT role, content FROM messages 
    WHERE doc_id = ?         
    """,
    (doc_id,))
    result = cursor.fetchall()
    connection.close()
    return result

def get_doc(doc_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT file_content, chunk_header, embedded_string, doc_id FROM documents    
    WHERE doc_id = ?
    """,
    (doc_id,))
    result = cursor.fetchall()
    connection.close()
    return result

def clear_database():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    DROP TABLE IF EXISTS documents
    """)
    connection.commit()
    connection.close()

def clear_messages():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    DROP TABLE IF EXISTS messages
    """)
    connection.commit()
    connection.close()

def get_last_user_questions(limit=2):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT content FROM messages
    WHERE role = 'user'
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    result = [row[0] for row in cursor.fetchall()]
    connection.close()
    return result[::-1]

def find_doc_by_name(file_name):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT id FROM docs 
    WHERE file_name = ?""", (file_name,)
    )
    row = cursor.fetchone() 
    connection.close()
    return row[0] if row else None

def create_doc(file_name):
    connection = get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO docs(file_name, uploaded_at) 
    VALUES (?, datetime('now')) 
    """, 
    (file_name,)
)
    doc_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return doc_id

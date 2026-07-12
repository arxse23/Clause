import sqlite3

def create_database():
    connection = sqlite3.connect("assistant.db")
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        role TEXT,
        content TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY, 
        file_name TEXT,
        file_content TEXT,
        file_type TEXT,
        chunk_header TEXT
    )
    """)
    connection.close()

def save_message(role, content):
    connection = sqlite3.connect("assistant.db")
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO messages(role, content)
    VALUES (?, ?)
    """,
    (role, content)
)
    connection.commit()
    connection.close()

def save_doc(file_name, file_content, file_type, chunk_header):
    if not file_content or not file_content.strip():
        return
    connection = sqlite3.connect("assistant.db")
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO documents(file_name, file_content, file_type, chunk_header)
    VALUES (?, ?, ?, ?)  
    """,
    (file_name, file_content, file_type, chunk_header)
)
    connection.commit()
    connection.close()

def get_messages():
    connection = sqlite3.connect("assistant.db")
    cursor = connection.cursor()
    cursor.execute("""
    SELECT * FROM messages
    """)
    result = cursor.fetchall()
    connection.close()
    return result

def get_doc():
    connection = sqlite3.connect("assistant.db")
    cursor = connection.cursor()
    cursor.execute("""
    SELECT * FROM documents 
    """)
    result = cursor.fetchall()
    connection.close()
    return result

def clear_database():
    connection = sqlite3.connect("assistant.db")
    cursor = connection.cursor()
    cursor.execute("""
    DROP TABLE IF EXISTS documents
    """)
    connection.commit()
    connection.close()
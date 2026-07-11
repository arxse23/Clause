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

def get_messages():
    connection = sqlite3.connect("assistant.db")
    cursor = connection.cursor()
    cursor.execute("""
    SELECT * FROM messages
    """)
    result = cursor.fetchall()
    connection.close()
    return result

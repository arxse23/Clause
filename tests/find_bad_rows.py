import sqlite3

con = sqlite3.connect("assistant.db")
cur = con.cursor()

print("--- rows whose embedded_string doesn't start with '[' ---")
bad = cur.execute("""
    SELECT id, doc_id, chunk_header, length(embedded_string),
           substr(embedded_string, 1, 20)
    FROM documents
    WHERE substr(embedded_string, 1, 1) != '['
""").fetchall()

for row in bad:
    print(row)
print(f"bad rows: {len(bad)}")

print("\n--- and empty/null check ---")
n = cur.execute("""
    SELECT count(*) FROM documents
    WHERE embedded_string IS NULL OR length(embedded_string) = 0
""").fetchone()[0]
print(f"null/empty embedded_string rows: {n}")
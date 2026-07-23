from flask import Flask, render_template, request, redirect, url_for, jsonify
import ollama
from database import (save_message, create_database, save_doc, get_doc, clear_database, 
                     get_last_user_questions, find_doc_by_name, 
                      create_doc, get_connection, get_all_docs, get_chat_history_from_db, clear_messages)
from ai import (prepare_messages, prepare_doc, get_embedding, decode_content, needs_rewrite, 
                prepare_top_chunks, extract_clause_number, rewrite_question)
from file_reader import read_pdf, read_txt, read_docx
import json
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
create_database()

@app.route("/")
def home():
    docs = get_all_docs()
    return render_template("index.html", docs=docs)

def is_allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400
    
    uploaded_file = request.files["file"]
    if uploaded_file.filename == '':
        return "No selected file", 400
    
    if is_allowed_file(uploaded_file.filename):
        create_database()

        if find_doc_by_name(uploaded_file.filename) is not None:
            return "Doc already uploaded", 400
        else:
            doc_id = create_doc(uploaded_file.filename)

        extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(uploaded_file.filename)

        if extension == 'pdf':
            parsed = read_pdf(uploaded_file)
        elif extension == 'txt':
            parsed = read_txt(uploaded_file)
        elif extension == 'docx':
            parsed = read_docx(uploaded_file)
        else:
            return "Unsupported file type", 400
        
        for doc in parsed:
            content = doc['content']
            chunk_header = doc['chunk_header']
            if "Table data" in content:
                print(f"\n=== TABLE CHUNK under '{chunk_header}' ===\n{content}\n===\n")
            embedded_string = get_embedding(content, chunk_header)
            save_doc(uploaded_file.filename, content, extension, chunk_header, embedded_string, doc_id)
        
        return redirect(url_for('home'))
    
    return "File type not allowed", 400

@app.route("/chat-history/<int:doc_id>")
def chat_history(doc_id):
    history = get_chat_history_from_db(doc_id)
    return jsonify({"history": history})

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    doc_id = data.get("doc_id")
    question = (data.get("question") or "").strip()
    
    if not doc_id or not question:
        return jsonify({"status": "error", "message": "Missing document mapping context or query text."}), 400

    print(f"Number of docs in DB: {len(get_doc(doc_id))}")
    print(f"ASK | doc={doc_id} | q={question!r}") 
    previous = get_last_user_questions(doc_id)
    if previous and needs_rewrite(question):
        question = rewrite_question(question, previous)
        print(f"REWRITTEN TO: {question}")

    raw_embedded_question = get_embedding(question)                        
    embedded_question = json.loads(raw_embedded_question)
    extracted_number = extract_clause_number(question)
    rank = decode_content(embedded_question, doc_id)
    
    gap = rank[0]['score'] - rank[1]['score'] if len(rank) > 1 else 1.0
    

    for r in rank[:8]:
        print(r['chunk_header'], r['score'])
    for item in rank:
        if extracted_number and item['chunk_header'].startswith(extracted_number):
            item['score'] += 1
    rank.sort(key=lambda x: x['score'], reverse=True)
    
    if gap > 0.10:
        top_chunks = rank[:2]
        triggered = True
    elif len(rank) > 3 and rank[2]['score'] - rank[3]['score'] < 0.02:
        top_chunks = rank[:5]
        triggered = False
    else:
        top_chunks = rank[:3]
        triggered = False
    
    print(f" GAP {gap:.3f} | TRIGGERED {triggered} | SENT {len(top_chunks)}: {[c['chunk_header'] for c in top_chunks]}")
    
    save_message("user", question, doc_id)
    prepared_messages = prepare_messages(doc_id)
    prepared_doc = prepare_top_chunks(top_chunks)
    system_prompt = {"role": "system", "content": '''
    You are a helpful, professional assistant designed to help users find information in documents. Use the conversation history only to understand what the current question is referring to, not as a source of facts. Base your answer only on information explicitly present in the document excerpts below — you may combine, summarise, and reasonably apply that information, but do not add facts, figures, or details that are not present in the excerpts. If the excerpts genuinely do not contain the answer, say so explicitly rather than guessing.
    '''}  
    
    prepared_data = prepared_doc + [system_prompt] + prepared_messages
    with open("last_ask.txt", "w", encoding="utf-8") as f: f.write(str(prepared_data))
    
    t0 = time.time()
    response = ollama.chat(
        model="llama3.2:3b",
        messages=prepared_data,
        options={"num_ctx": 8192} 
    )
    print(f"LATENCY {time.time() - t0:.1f}s | SENT {len(top_chunks)}")

    answer = response["message"]["content"]
    save_message("assistant", answer, doc_id)
    sources = [c['chunk_header'] for c in top_chunks]
    return jsonify({
        "status": "success",
        "answer": answer,
        "sources": sources
    })

@app.route("/delete/<int:doc_id>", methods=["POST"])
def delete_doc(doc_id):
    connection = get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM docs WHERE id = ?", (doc_id,))
    connection.commit()
    connection.close()
    return redirect(url_for('home'))

@app.route("/clear-system-db", methods=["POST"])
def clear_system_db():
    # Trigger drop and reconstruct loops safely
    clear_database()
    create_database()
    # Flash state arrays back to starting home terminal point context layouts
    return redirect(url_for('home'))

@app.route("/clear-messages/<int:doc_id>", methods=["POST"])
def clear_messages_route(doc_id):
    clear_messages(doc_id)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)

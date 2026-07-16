from flask import Flask, render_template, request, redirect, url_for
import ollama
from database import save_message, create_database, save_doc, get_doc, clear_database, clear_messages, get_last_user_questions
from ai import prepare_messages, prepare_doc, get_embedding, decode_content, needs_rewrite, prepare_top_chunks, extract_clause_number, rewrite_question
from file_reader import read_pdf, read_txt, read_docx
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)


create_database()

@app.route("/")
def home():
    return render_template("index.html")

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
        clear_database()
        create_database()

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
            save_doc(uploaded_file.filename, content, extension, chunk_header, embedded_string)
        
        return redirect(url_for('home'))
    
    return "File type not allowed", 400



@app.route("/ask", methods=["POST"])
def ask():
    print(f"Number of docs in DB: {len(get_doc())}")
    question = request.form["question"]
    print(f"ASK | q={question!r}")  
    previous = get_last_user_questions(2)
    if previous and needs_rewrite(question):
        question = rewrite_question(question, previous)
        print(f"REWRITTEN TO: {question}")


    raw_embedded_question = get_embedding(question)                        
    embedded_question = json.loads(raw_embedded_question)
    extracted_number = extract_clause_number(question)
    rank = decode_content(embedded_question)
    for r in rank[:8]:
        print(r['chunk_header'], r['score'])
    for item in rank:
        if extracted_number and item['chunk_header'].startswith(extracted_number):
            item['score'] += 1
    rank.sort(key=lambda x: x['score'], reverse=True)
    if len(rank) > 3 and rank[2]['score'] - rank[3]['score'] < 0.02:
        top_chunks = rank[:5]
    else:
        top_chunks = rank[:3]
    
    print(f"SENT {len(top_chunks)}: {[c['chunk_header'] for c in top_chunks]}")
    
    save_message("user", question)
    prepared_messages = prepare_messages()
    prepared_doc = prepare_top_chunks(top_chunks)
    system_prompt = {"role": "system", "content": '''
    You are a helpful, professional assistant designed to help users find information in documents. Use the conversation history only to understand what the current question is referring to, not as a source of facts. Base your answer only on information explicitly present in the document excerpts below — you may combine, summarise, and reasonably apply that information (for example, working out which row of a table applies to a specific number, or recognising that a time range like '6pm to 5am' corresponds to night hours), but do not add facts, figures, or details that are not present in the excerpts. If the excerpts genuinely do not contain the answer, say so explicitly rather than guessing. Check whether multiple amounts or entitlements apply together and combine them (for example, a base rate in addition to a further rate).

    If a table has multiple columns and/or rows, identify which column/row applies based on details the user has given you — if the user hasn't specified which category applies, explicitly state which column you're using and why, rather than picking one silently.

    Treat ranges as strict mathematical conditions. Check which range the user's situation falls into. Do not assume adjacent ranges overlap. Pay close attention to words like 'more than', 'less than', 'no more than', 'at least', and 'up to'. If a value exactly matches a boundary, determine which condition explicitly includes that boundary.

    Be consistent. Don't state something and contradict it. Don't state something is absent and quote it. If you are not sure, say you are not sure, instead of choosing an answer.

    If there is pushback on something you stated, recheck the previous excerpts and correct only from that information. Don't introduce new details to satisfy the user. If the recheck doesn't support a correction, say so. When asked where or whether the document mentions something, only report occurrences you can literally see in the excerpts - never inferred, assumed, or plausible-sounding ones.
    
    '''}  
    print(f"PROMPT HEAD: {system_prompt['content'][:60].strip()!r}")
    prepared_data = prepared_doc + [system_prompt] + prepared_messages
    with open("last_ask.txt", "w", encoding="utf-8") as f: f.write(str(prepared_data))
    response = ollama.chat(
        model="llama3.2:3b",
        messages=prepared_data,
        options={"num_ctx": 8192} 
    )

    answer = response["message"]["content"]
    save_message("assistant", answer)
    return render_template("index.html", answer=answer)

@app.route("/clear-messages", methods=["POST"])
def clear_msgdb():
    clear_messages()
    create_database()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
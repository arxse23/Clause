from flask import Flask, render_template, request, redirect, url_for
import ollama
from database import save_message, create_database, save_doc, get_doc
from ai import prepare_messages, prepare_doc
from file_reader import read_pdf, read_txt

app = Flask(__name__)


create_database()

@app.route("/")
def home():
    return render_template("index.html")

def is_allowed_file(uploaded_file):
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}
    extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
    if extension in ALLOWED_EXTENSIONS:
        return True

@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files["file"]
    extension = uploaded_file.filename.rsplit('.', 1)[1].lower()

    if uploaded_file.filename != '' and is_allowed_file(uploaded_file):
        uploaded_file.save(uploaded_file.filename)
        print('Upload successful')

        if extension == 'pdf':
            parsed_pdf = read_pdf(uploaded_file)
            save_doc(uploaded_file.filename, parsed_pdf, "pdf")
            print(f"Saved pdf: {uploaded_file.filename}")

        elif extension == 'txt':
            parsed_txt = read_txt(uploaded_file.filename)
            save_doc(uploaded_file.filename, parsed_txt, "txt")

        return redirect(url_for('home'))
    
    return render_template("index.html")



@app.route("/ask", methods=["POST"])
def ask():
    print(f"Number of docs in DB: {len(get_doc())}")
    question = request.form["question"]
                            
    save_message("user", question)
    prepared_messages = prepare_messages()
    prepared_doc = prepare_doc()
    system_prompt = {"role": "system", "content": "You are a helpful, professional assistant designed to help users find information in docments. Rely on conversation history and keep your answer relevant to the question. If the document doesn't contain the answer, say so explicitly rather than guessing."}

    prepared_data = prepared_doc + [system_prompt] + prepared_messages
    print(prepared_data)
    response = ollama.chat(
        model="llama3.2:3b",
        messages=prepared_data,
        options={"num_ctx": 8192} 
    )

    answer = response["message"]["content"]
    save_message("assistant", answer)
    return render_template("index.html", answer=answer)


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request
import ollama
from database import save_message, create_database
from ai import prepare_messages

app = Flask(__name__)

create_database()

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    question = request.form["question"]
                            
    save_message("user", question)
    prepared_messages = prepare_messages()

    response = ollama.chat(
        model="llama3.2:3b",
        messages=prepared_messages 
    )

    answer = response["message"]["content"]
    save_message("assistant", answer)
    return answer


if __name__ == "__main__":
    app.run(debug=True)
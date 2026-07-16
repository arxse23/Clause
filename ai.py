from database import get_messages, get_doc
import ollama
import json
import math
import re

def prepare_messages(doc_id):
    saved_messages = get_messages(doc_id)
    converted_list = []
    for msg in saved_messages:
        role=msg[0]
        content=msg[1]
        converted_dict={"role": role, "content": content}
        converted_list.append(converted_dict)
    return converted_list   

def prepare_doc(doc_id):
    saved_docs = get_doc(doc_id)
    docs_list = []
    for doc in saved_docs:
        content = doc[0]
        chunk_header = doc[1]
        docs_dict = {
            "role": "system",
            "content": f"""
        DOCUMENT SECTION:
        {chunk_header}

        CONTENT:
        {content}
        """
        }
        docs_list.append(docs_dict)
    return docs_list

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (magnitude1 * magnitude2)

def get_embedding(content, chunk_header=None):
    if chunk_header is None:
        embed_input = content
    else:
        embed_input = f'{chunk_header}\n{content}'
    embedded_text = ollama.embeddings(model="nomic-embed-text", prompt=embed_input)
    embedded_response = embedded_text["embedding"]
    embedded_string = json.dumps(embedded_response)
    return embedded_string

def decode_content(question, doc_id):
    saved_embedding = get_doc(doc_id)
    docs_list = []
    for doc in saved_embedding:
        content = doc[0]
        chunk_header = doc[1]
        embedded_string= doc[2]
        decoded_string = json.loads(embedded_string)
        score = cosine_similarity(question, decoded_string)
        docs_list.append({"content": content, "chunk_header": chunk_header, "score": score})
    sorted_list = sorted(docs_list, key=lambda item: item["score"], reverse=True)

    return sorted_list
    
def prepare_top_chunks(top_chunks):
    docs_list = []
    for doc in top_chunks:
        content = doc["content"]
        chunk_header = doc["chunk_header"]
        docs_list.append({
            "role": "system",
            "content": f"""
        DOCUMENT SECTION:
        {chunk_header}

        CONTENT:
        {content}
        """
        })

    return docs_list                 

def extract_clause_number(question):
    match = re.search(r"\d+\.\d+", question)
    if match:
        return match.group()
    return None

def needs_rewrite(question: str) -> bool:
    cleaned = question.strip().lower()
    
    if not cleaned:
        return False
        
    words = cleaned.split()
    
    unambiguous_openers = ("what about", "and what", "how about")
    conjunctions = {"and", "but", "so", "also"}
    if cleaned.startswith(unambiguous_openers) or (words and words[0] in conjunctions):
        return True
        
    reference_words = {"that", "it", "this", "they", "those"}
    has_reference_word = any(word in reference_words for word in words)
    has_phrase_reference = "the above" in cleaned
    has_any_reference = has_reference_word or has_phrase_reference
    
    if len(words) <= 7 and has_any_reference:
        return True
        
    return False

def rewrite_question(question, previous_questions):
    history_block = "\n".join(
        f"{i}. {q}" for i, q in enumerate(previous_questions, 1)
    )

    prompt = f"""You are a query writing component for a document retrieval system.  Your ONLY task is to rewrite the users question into a standalone search query. Rules:

1. Do not answer the question.
2. Do not provide explanations.
3. Do not add information that is not present in the user's question or conversation history.
4. Do not change the user's intent.
5. Preserve clause numbers, names, dates, amounts and terminology exactly.

If the user's question is already standalone and understandable without conversation history, return it exactly unchanged.
If the user's question depends on previous conversation context, rewrite it into a standalone question by replacing references such as: "that", "it", "this", "the above". "my previous question" with the specific subject from the conversation.

Output ONLY the rewritten query. No quotes. No prefix. No commentary.

Previous user questions:
{history_block}

Current question: {question}"""

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip().strip('"')
from database import get_messages, get_doc

def prepare_messages():
    saved_messages = get_messages()
    converted_list = []
    for msg in saved_messages:
        role=msg[1]
        content=msg[2]
        converted_dict={"role": role, "content": content}
        converted_list.append(converted_dict)
    return converted_list   

def prepare_doc():
    saved_docs = get_doc()
    docs_list = []
    for doc in saved_docs:
        content = doc[2]
        chunk_header = doc[4]
        docs_dict = {"role": "system", "content": f"This is an excerpt from the uploaded document, under the heading '{chunk_header}': {content}"}
        docs_list.append(docs_dict)
    return docs_list
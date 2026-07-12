from pypdf import PdfReader
import re
from docx import Document

pattern = r"(^\d+(?:\.\d+)?\s[A-Z][^\n]+)"

def content_split(raw_text):
    split_content = re.split(pattern, raw_text, flags=re.M)
    doc_list = []
    for i, val in enumerate(split_content):
        if i % 2 == 0 or i == 0:
            content = val
            if i != 0:
                doc_list.append({"content": content, "chunk_header": chunk_header})
        else:
            chunk_header = val
    return doc_list

def read_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    file_content = "\n".join(p.extract_text() for p in reader.pages)
    split_content = content_split(file_content)
    return split_content

def read_txt(uploaded_file):
    with open(uploaded_file, "r", encoding="utf-8") as f:
        content = f.read()
    split_content = content_split(content)
    return split_content

def read_docx(uploaded_file):
    doc = Document(uploaded_file)
    docx_list = []
    for paragraph in doc.paragraphs:
        docx_list.append(paragraph.text)
    content = '\n'.join(docx_list)
    split_content = content_split(content)
    return split_content
from pypdf import PdfReader

def read_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    file_content = "\n".join(p.extract_text() for p in reader.pages)
    return file_content

def read_txt(uploaded_file):
    with open(uploaded_file, "r", encoding="utf-8") as f:
        content = f.read()
    return content
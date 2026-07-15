from pypdf import PdfReader
import re
from docx import Document
import pdfplumber

pattern = r"(^\d+(?:\.\d+)?\s[A-Z][^\n]+)"

def content_split(raw_text):
    split_content = re.split(pattern, raw_text, flags=re.M)
    doc_list = []

    chunk_header = "Introduction / Preface"
    
    for i, val in enumerate(split_content):
        if i % 2 == 0 or i == 0:
            content = val.strip()
            if content:
                doc_list.append({"content": content, "chunk_header": chunk_header})
        else:
            chunk_header = val.strip()

    return doc_list

def _is_ghost(table):
    """
    Ignore obvious layout/ghost tables.

    A real table should have at least a few populated cells.
    Tiny fragments created by PDF formatting are discarded.
    """
    if len(table) < 3:
        return True

    non_empty = sum(
        bool(cell and cell.strip())
        for row in table
        for cell in row
    )

    return non_empty < 6


def _is_fragment(cells):
    """
    Detect rows that are continuations of the previous row.

    These are typically text-only rows beginning with '&',
    ',', '(', lowercase text, or standalone words like
    'Member' produced by poor PDF extraction.
    """
    if any("$" in c or "%" in c for c in cells):
        return False

    return all(
        c and (
            c[0] in "&,("
            or c[0].islower()
            or c == "Member"
        )
        for c in cells
    )


def _repair_table(raw):
    """
    Convert extracted PDF tables into readable text.

    Steps:
        1. Merge fragmented rows.
        2. Forward-fill inherited rates.
        3. Convert each row into a natural-language sentence.
    """

    # Merge continuation rows
    rows = []

    for row in raw:
        cells = [
            c.replace("\n", " ").strip()
            for c in row
            if c and c.strip()
        ]

        if not cells:
            continue

        if rows and _is_fragment(cells):
            rows[-1].extend(cells)
        else:
            rows.append(cells)

    if len(rows) <= 1:
        return ""

    # Convert rows into readable sentences
    sentences = []
    current_rates = []

    for cells in rows[1:]:      # Skip header row

        rates = [c for c in cells if "$" in c or "%" in c]
        texts = [c for c in cells if c not in rates]

        if rates:
            current_rates = rates

        if not texts or not current_rates:
            continue

        role = " / ".join(texts)

        if len(current_rates) >= 2:
            sentences.append(
                f"{role}: base rate {current_rates[0]}, "
                f"casual hourly rate {current_rates[1]}."
            )
        else:
            sentences.append(
                f"{role}: rate {current_rates[0]}."
            )

    return "\n".join(sentences)


def read_pdf(uploaded_file):
    """
    Read a PDF while preserving the original reading order.

    Instead of extracting all text followed by all tables,
    the page is reconstructed as:

        text above table
        table
        text below table

    This keeps surrounding context attached to each table,
    producing much higher-quality chunks for embeddings.
    """

    parts = []

    with pdfplumber.open(uploaded_file) as pdf:

        for page in pdf.pages:

            # Cache extracted tables so we only parse each once
            tables = []

            for table in page.find_tables():
                raw = table.extract()

                if not _is_ghost(raw):
                    tables.append((table, raw))

            # No tables on this page
            if not tables:
                text = page.extract_text()

                if text and text.strip():
                    parts.append(text)

                continue

            # Process tables from top to bottom
            tables.sort(key=lambda x: x[0].bbox[1])

            cursor = 0

            for table, raw in tables:

                top = table.bbox[1]
                bottom = table.bbox[3]

                # Text before table
                if top > cursor:

                    above = page.within_bbox(
                        (
                            page.bbox[0],
                            cursor,
                            page.bbox[2],
                            top,
                        )
                    ).extract_text()

                    if above and above.strip():
                        parts.append(above)

                # Repaired table
                repaired = _repair_table(raw)

                if repaired:
                    parts.append("Table data:\n" + repaired)
                else:
                    fallback = page.within_bbox(table.bbox).extract_text()
                    if fallback and fallback.strip():
                        parts.append(fallback)

                cursor = bottom

            # Remaining text below final table
            if cursor < page.height:

                below = page.within_bbox(
                    (
                        page.bbox[0],
                        cursor,
                        page.bbox[2],
                        page.height,
                    )
                ).extract_text()

                if below and below.strip():
                    parts.append(below)

    return content_split("\n".join(parts))

def read_txt(uploaded_file):
    content = uploaded_file.read().decode('utf-8')
    return content_split(content)


def read_docx(uploaded_file):
    doc = Document(uploaded_file.stream)
    docx_list = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
    content = '\n'.join(docx_list)
    return content_split(content)
  


import pypdf
import pdfplumber
import re
import docx
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


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
    print(doc_list)
    return doc_list

def _is_ghost(table):
    if len(table) < 3:
        return True
    non_empty = sum(bool(cell and cell.strip()) for row in table for cell in row)
    return non_empty < 6

def _is_fragment(cells):
    if any("$" in c or "%" in c for c in cells):
        return False
    non_empty = [c for c in cells if c]
    if not non_empty:
        return False
    return all(c[0] in "&,(" or c[0].islower() or c == "Member" for c in non_empty)

_VALUE_TOKENS = {"NIL", "N/A", "NA", "-"}

def _is_numeric_cell(cell):
    t = cell.replace("$", "").replace("%", "").replace(",", "").strip()
    if not t:
        return False
    try:
        float(t)
        return True
    except ValueError:
        return False

def _is_value_cell(cell):
    return _is_numeric_cell(cell) or cell.strip().upper() in _VALUE_TOKENS

def _repair_table_v2(raw):
    rows = []
    for row in raw:
        cells = [(c or "").replace("\n", " ").strip() for c in row]
        if not any(c for c in cells):
            continue
        if rows and _is_fragment(cells):
            rows[-1].extend(cells)
        else:
            rows.append(cells)

    if len(rows) <= 1:
        return ""

    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]

    first_data = next((i for i, r in enumerate(rows) if any(_is_value_cell(c) for c in r)), None)
    if not first_data:
        return ""

    banner_rows = set()
    for ri, r in enumerate(rows[:first_data]):
        non_empty_cols = [c for c, v in enumerate(r) if v]
        if len(non_empty_cols) == 1:
            banner_rows.add(ri)

    labels = []
    for c in range(ncols):
        parts = []
        for ri, r in enumerate(rows[:first_data]):
            if not r[c] or ri in banner_rows:
                continue
            parts.append(r[c])
        labels.append(" ".join(parts))

    if any(len(lab) > 150 for lab in labels):
        return ""

    subject_col = next((c for c in range(ncols) if any(r[c] and not _is_value_cell(r[c]) for r in rows[first_data:])), 0)

    def nearest_label(pos):
        best, best_dist, best_c = None, None, None
        for c, lab in enumerate(labels):
            if not lab or c == subject_col:
                continue
            d = abs(c - pos)
            if best_dist is None or d < best_dist:
                best, best_dist, best_c = lab, d, c
            elif d == best_dist and c > best_c:
                best, best_c = lab, c
        return best if best is not None else "[?]"

    sentences, carried_values = [], None
    for r in rows[first_data:]:
        subject_parts = [c for i, c in enumerate(r) if c and (i == subject_col or not _is_value_cell(c))]
        values = [(i, c) for i, c in enumerate(r) if i != subject_col and _is_value_cell(c)]
        has_numeric = any(_is_numeric_cell(c) for _, c in values)
        if has_numeric:
            carried_values = values
        elif carried_values and subject_parts:
            values = carried_values

        if not subject_parts:
            continue
        subject = " / ".join(subject_parts)
        if not values:
            sentences.append(f"{subject}: [?].")
            continue
        pairs = ", ".join(f"{labels[i] or nearest_label(i)} {v}" for i, v in values)
        sentences.append(f"{subject}: {pairs}.")
    return "\n".join(sentences)

def _repair_table_v1(raw):
    rows = []
    for row in raw:
        cells = [c.replace("\n", " ").strip() for c in row if c and c.strip()]
        if not cells:
            continue
        if rows and _is_fragment(cells):
            rows[-1] = rows[-1] + cells
        else:
            rows.append(cells)
    sentences = []
    current_rates = []
    for cells in rows[1:]:
        rates = [c for c in cells if "$" in c or "%" in c]
        texts = [c for c in cells if c not in rates]
        if rates:
            current_rates = rates
        if not texts or not current_rates:
            continue
        role = " / ".join(texts)
        if len(current_rates) >= 2:
            sentences.append(f"{role}: base rate {current_rates[0]}, casual hourly rate {current_rates[1]}.")
        else:
            sentences.append(f"{role}: rate {current_rates[0]}.")
    return "\n".join(sentences)

def read_pdf(uploaded_file):
    parts = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            tables = []
            for table in page.find_tables():
                raw = table.extract()
                if not _is_ghost(raw):
                    tables.append((table, raw))

            if not tables:
                text = page.extract_text()
                if text and text.strip():
                    parts.append(text)
                continue

            tables.sort(key=lambda x: x[0].bbox[1])
            cursor = 0

            for table, raw in tables:
                top = table.bbox[1]
                bottom = table.bbox[3]

                if top > cursor:
                    above = page.within_bbox((page.bbox[0], cursor, page.bbox[2], top)).extract_text()
                    if above and above.strip():
                        parts.append(above)

                repaired = _repair_table_v2(raw)
                if not repaired:
                    repaired = _repair_table_v1(raw)

                if repaired:
                    parts.append("Table data:\n" + repaired)
                else:
                    fallback = page.within_bbox(table.bbox).extract_text()
                    if fallback and fallback.strip():
                        parts.append(fallback)
                cursor = bottom

            if cursor < page.height:
                below = page.within_bbox((page.bbox[0], cursor, page.bbox[2], page.height)).extract_text()
                if below and below.strip():
                    parts.append(below)
    return content_split("\n".join(parts))

def read_txt(uploaded_file):
    content = uploaded_file.read().decode('utf-8')
    return content_split(content)


def serialise_docx_table(table):
    if not table.rows:
        return ""
    
    #extract header from first row
    first_row = table.rows[0].cells
    keys = tuple(cell.text.strip() for cell in first_row)

    #detect garabage header
    is_garbage_header = not keys or keys[0] == ""

    data = []
    
    #fall back if garbage
    if is_garbage_header:
        for row in table.rows:
            row_items = []
            for cell in row.cells:
                text = cell.text.strip()
                if text and text not in row_items:
                    row_items.append(text)
            if row_items:
                data.append(", ".join(row_items) + ".")
    
    else:
        for row in table.rows[1:]:
            text = (cell.text.strip() for cell in row.cells)

            #maps keys to row valyes
            row_pairs = [(k, v) for k, v in zip(keys, text) if k]

            if row_pairs:
                first_k, first_v = row_pairs[0] #sets the header
                sentence_head = f'{first_k} {first_v}:'
                body = [f'{k} {v}' for k, v in row_pairs[1:]] #sets the body from row 2
                sentence = ", ".join(body) #joins key value as pairs into sentences seperated by ,

                if sentence:
                    data.append(f'{sentence_head} {sentence}.')
                else:
                    data.append(f'{first_k} {first_v}.')

                
    return '\n'.join(data)
    
def read_docx(uploaded_file):
    doc = Document(uploaded_file.stream)

    chunks = []
    current_header = "Introduction / Preface"     # ruling 2: pre-heading default
    current_parts = []

    def close_chunk():
        content = "\n".join(current_parts).strip()
        if content:
            chunks.append({"content": content, "chunk_header": current_header})

    for item in doc.iter_inner_content():
        if isinstance(item, Paragraph):
            if item.style.name.startswith("Heading") and item.text.strip():
                close_chunk()                      # ruling 1: heading = new chunk
                current_header = item.text.strip()
                current_parts = []
            elif item.text.strip():
                current_parts.append(item.text)
        elif isinstance(item, Table):
            serialised = serialise_docx_table(item)
            if serialised:
                current_parts.append(serialised)

    close_chunk()                                  # don't orphan the last section
    return chunks

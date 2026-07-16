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

    Empty cells are ignored — only non-empty cells are checked.
    This handles PDF extractions where continuation rows have
    text in only one column (e.g. '& Trade Desk Team' or 'Member'
    as a continuation of 'Special Orders, Service').
    """
    if any("$" in c or "%" in c for c in cells):
        return False

    non_empty = [c for c in cells if c]

    if not non_empty:
        return False

    return all(
        c[0] in "&,("
        or c[0].islower()
        or c == "Member"
        for c in non_empty
    )


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
    """Header-aware repair: read the table's own header, emit honest sentences.
    Returns "" when it can't find header+data — caller falls back to raw text
    (never excise without replacing)."""
    # === Step 1: normalize grid, strip cells, pad rows to equal width ===
    # Keep ALL cells (including empty ones) to preserve column alignment.
    # Stripping empty cells collapses the structure — PDF tables often have
    # merged cells where header text sits in a different column than the values.
    rows = []
    for row in raw:
        cells = [
            (c or "").replace("\n", " ").strip()
            for c in row
        ]
        if not any(c for c in cells):
            continue
        # Merge continuation rows (ported from v1)
        if rows and _is_fragment(cells):
            rows[-1].extend(cells)
        else:
            rows.append(cells)

    if len(rows) <= 1:
        return ""

    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]

    # === Step 2: detect header vs data rows ===
    # header = all rows above the first row containing a value cell
    first_data = next((i for i, r in enumerate(rows)
                        if any(_is_value_cell(c) for c in r)), None)
    if not first_data:          # no data rows → fallback
        return ""

    # === Step 3: merge header column-wise ===
    # Build labels column by column from header rows.
    # Skip decorative banner rows that have exactly 1 non-empty cell
    # (e.g. a row with just "Hourly Wage Rates September 2023" in one cell).
    # Multi-cell header rows are legitimate column labels.
    banner_rows = set()
    for ri, r in enumerate(rows[:first_data]):
        non_empty_cols = [c for c, v in enumerate(r) if v]
        if len(non_empty_cols) == 1:
            banner_rows.add(ri)

    labels = []
    for c in range(ncols):
        parts = []
        for ri, r in enumerate(rows[:first_data]):
            if not r[c]:
                continue
            if ri in banner_rows:
                continue
            parts.append(r[c])
        labels.append(" ".join(parts))

    # Salad/wonk detection: if any header is absurdly long, fall back
    if any(len(lab) > 150 for lab in labels):
        return ""

    # subject column = leftmost column with text in the data rows
    subject_col = next((c for c in range(ncols)
                        if any(r[c] and not _is_value_cell(r[c])
                               for r in rows[first_data:])), 0)

    def nearest_label(pos):
        """Find the nearest non-empty header for a given column.
        Skips the subject column and empty labels.
        On ties, prefers the rightward label (higher column index) —
        value descriptions in PDF tables are typically to the right
        of the subject column (e.g. header in col 2 describes values in col 1)."""
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

    # === Step 4: convert data rows to sentences ===
    sentences, carried_values = [], None
    for r in rows[first_data:]:
        subject_parts = [c for i, c in enumerate(r)
                         if c and (i == subject_col or not _is_value_cell(c))]
        values = [(i, c) for i, c in enumerate(r)
                  if i != subject_col and _is_value_cell(c)]

        has_numeric = any(_is_numeric_cell(c) for _, c in values)
        if has_numeric:
            carried_values = values
        elif carried_values and subject_parts:
            values = carried_values                # forward-fill inherited values

        if not subject_parts:
            continue

        subject = " / ".join(subject_parts)

        if not values:
            sentences.append(f"{subject}: [?].")
            continue

        pairs = ", ".join(
            f"{labels[i] or nearest_label(i)} {v}" for i, v in values
        )
        sentences.append(f"{subject}: {pairs}.")

    return "\n".join(sentences)

# _repair_table_v1 — recovered from chat history (deleted from file_reader.py
# during late-night edits). Known-good rollback target: this version + bbox
# read_pdf produced the 3/3 Supervisor result. Paste back into file_reader.py
# if rollback to v1 is needed.

def _repair_table_v1(raw):
    # 1. merge continuation fragments into row above
    rows = []
    for row in raw:
        cells = [c.replace("\n", " ").strip() for c in row if c and c.strip()]
        if not cells:
            continue
        if rows and _is_fragment(cells):
            rows[-1] = rows[-1] + cells   # glue onto previous row
        else:
            rows.append(cells)
    # 2. forward-fill: rows with a rate set the "current rates"; rows without inherit
    sentences = []
    current_rates = []
    for cells in rows[1:]:  # skip header row
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

                # Repaired table — now using v2
                repaired = _repair_table_v1(raw)

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
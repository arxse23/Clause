# table_recon.py — throwaway: compare pypdf vs pdfplumber on the wage table
# pip install pdfplumber
import pdfplumber
from pypdf import PdfReader

PDF_PATH = "Bunnings Retail Enterprise Agreement 2023.pdf"   # <-- your actual filename
PAGE_NUM = 30                # <-- 1-based page number of the wage table; adjust

# --- What the model currently sees (pypdf) ---
print("=" * 60)
print("PYPDF extract_text():")
print("=" * 60)
reader = PdfReader(PDF_PATH)
print(reader.pages[PAGE_NUM - 1].extract_text())

# --- What pdfplumber finds ---
with pdfplumber.open(PDF_PATH) as pdf:
    page = pdf.pages[PAGE_NUM - 1]

    tables = page.extract_tables()
    print("\n" + "=" * 60)
    print(f"PDFPLUMBER: found {len(tables)} table(s) on page {PAGE_NUM}")
    print("=" * 60)

    for t_idx, table in enumerate(tables):
        print(f"\n--- Table {t_idx + 1} ({len(table)} rows) ---")
        for row in table:
            # cells can be None or contain embedded newlines
            print([("" if c is None else c.replace("\n", " ⏎ ")) for c in row])

    print("\n" + "=" * 60)
    print("PDFPLUMBER extract_text() (prose view of same page):")
    print("=" * 60)
    print(page.extract_text())
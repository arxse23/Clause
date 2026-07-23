# capture_fixtures.py — one-shot: dump the two battle-scarred grids as a fixtures file
import pdfplumber
import pprint

PDF = "Bunnings Retail Enterprise Agreement 2023.pdf"   # ← your actual filename
WAGE_PAGE = 6          # 1-based
REDUNDANCY_PAGE = 30   # 1-based

with pdfplumber.open(PDF) as pdf:
    wage = pdf.pages[WAGE_PAGE - 1].extract_tables()
    redun = pdf.pages[REDUNDANCY_PAGE - 1].extract_tables()

with open("tests/fixtures.py", "w", encoding="utf-8") as f:
    f.write("# Auto-captured real grids from the Bunnings PDF. Do not hand-edit.\n\n")
    f.write("WAGE_TABLES = ")
    f.write(pprint.pformat(wage, width=120))
    f.write("\n\nREDUNDANCY_TABLES = ")
    f.write(pprint.pformat(redun, width=120))
    f.write("\n")

print(f"wage page: {len(wage)} table(s); redundancy page: {len(redun)} table(s)")
print("written to tests/fixtures.py")
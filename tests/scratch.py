# scratch: gate_test's little sibling
from ai import extract_clause_number
tests = [
    ("I'm 50 and worked at Bunnings for 3.5 years, what redundancy pay would I get?", None),
    ("What does clause 12.1 cover?", "12.1"),
    ("What does 12.1 cover?", "12.1"),
    ("I worked 3.5 years, what does 12.3 say?", "12.3"),
    ("Can I work 10 hours?", None),
    ("What is clause 8?", "8"),
]
for q, want in tests:
    got = extract_clause_number(q)
    print("✓" if got == want else f"✗ (got {got})", q)
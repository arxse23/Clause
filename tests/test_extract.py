import pytest
from ai import extract_clause_number

@pytest.mark.parametrize("question, expected", [
    ("I'm 50 and worked at Bunnings for 3.5 years, what redundancy pay would I get?", None),
    ("What does clause 12.1 cover?", "12.1"),
    ("What does 12.1 cover?", "12.1"),
    ("I worked 3.5 years, what does 12.3 say?", "12.3"),
    ("Can I work 10 hours?", None),
    ("What is clause 8?", "8"),
])
def test_extract_clause_number(question, expected):
    assert extract_clause_number(question) == expected
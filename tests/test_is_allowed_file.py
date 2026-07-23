import pytest
from app import is_allowed_file

CASES = [
    ("sample.docx", True),
    ("sample.txt", True),
    ("Bunnings.pdf", True),
    ("virus.exe", False),
    ("README", False),        # ← the extensionless gravestone — this one crashed the app once
]

@pytest.mark.parametrize("filename, expected", CASES)
def test_is_allowed_file(filename, expected):
    assert is_allowed_file(filename) == expected
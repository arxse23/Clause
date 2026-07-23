import pytest
from ai import needs_rewrite

STANDALONE = [
    "What are the overtime conditions?",
    "I'm a casual Supervisor. What's my hourly rate?",
    "What is the meal allowance?",
    "What is shiftwork?",
    "Can I get paid extra for working nights?",
    "I'm 50 and worked at Bunnings for 3.5 years, what redundancy pay would I get?",
    "What does a Kitchen Specialist do?",
    "Which section mentions grandchild?",
]

FOLLOWUPS = [
    "what about part-timers?",
    "how much is that per week?",
    "and on Sundays?",
    "does it apply to casuals?",
    "what do they get instead?",
    "tell me more about this",
]

CASES = [(q, False) for q in STANDALONE] + [(q, True) for q in FOLLOWUPS]

@pytest.mark.parametrize("question, expected", CASES)
def test_needs_rewrite(question, expected):
    assert needs_rewrite(question) == expected
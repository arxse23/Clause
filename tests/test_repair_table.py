import re
from file_reader import _repair_table_v2
from tests.fixtures import WAGE_TABLES, REDUNDANCY_TABLES

WAGE = WAGE_TABLES[0]          # the 19-row main grid (index 1 is the ghost)
REDUNDANCY = REDUNDANCY_TABLES[0]


def test_supervisor_rate_present():
    # Gravestone: the flagship. $35.54 must survive repair.
    result = _repair_table_v2(WAGE)
    assert "$35.54" in result
    assert "Supervisor" in result


def test_fragments_are_merged():
    # Gravestone: v2.0 dropped v1's fragment merge; '& Trade Desk Team'
    # became a standalone fake role. Merged = present, but never leading a line.
    result = _repair_table_v2(WAGE)
    assert "& Trade Desk Team" in result                      # not lost...
    assert not any(line.strip().startswith("&")               # ...not standalone
                   for line in result.split("\n"))


def test_redundancy_first_tier_present():
    # Gravestone: numeric-only header detection swallowed 'less than 1 year'
    # into the header, deleting the tier.
    result = _repair_table_v2(REDUNDANCY)
    assert "less than 1 year" in result


def test_no_phantom_nil_fusion():
    # Gravestone: the swallowed tier's Nils fused into labels ("Nil 4").
    result = _repair_table_v2(REDUNDANCY)
    assert not re.search(r"Nil \d", result)


def test_thirteen_keeps_its_age_label():
    # The design goal itself: 13 must sit in a line that also carries the
    # 45-and-over association. (This is the sentence-format's whole point.)
    result = _repair_table_v2(REDUNDANCY)
    assert any("13" in line and "45" in line for line in result.split("\n"))


def test_salad_guard_falls_back():
    # Gravestone: Appendix-1-style monster labels must trigger "" (fallback),
    # never a context-exploding chunk. Synthetic grid, label > 150 chars.
    monster = [
        ["X" * 200, "header2"],
        ["row label", "$10.00"],
    ]
    assert _repair_table_v2(monster) == ""
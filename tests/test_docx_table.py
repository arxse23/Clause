from file_reader import serialise_docx_table

class FakeCell:
    def __init__(self, text): self.text = text

class FakeRow:
    def __init__(self, cells): self.cells = [FakeCell(c) for c in cells]

class FakeTable:
    def __init__(self, rows): self.rows = [FakeRow(r) for r in rows]



def test_clean_header():
    result = serialise_docx_table(FakeTable([["Season", "Episodes", "First Released", "Last Released"], ["1", "22", "September 10, 2009", "May 13, 2010"], ["2", "22", "September 9, 2010", "May 12, 2011"], ["4", "23", "October 11, 2012", "May 16, 2013"]]))
    assert "Season 4" in result
    assert "October 11, 2012" in result

def test_garbage_header():
    result = serialise_docx_table(FakeTable([["", "Track 2", "Atatürk Havalimanı"], ["Island Platform", "Island Platform"], ["", "Track 1", "Yenikapı"]]))
    assert result != ""
    assert result.count("Island Platform") == 1

def test_merged_headers():
    result = serialise_docx_table(FakeTable([["Name", "Score", "Score"], ["Alice", "10", "99"]]))
    assert "10" in result
    assert "99" in result
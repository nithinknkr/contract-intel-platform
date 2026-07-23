from app.services.chunking import chunk_text

PARAGRAPH = """This is a clause about liability caps and indemnification obligations between the parties. Either party's total liability under this agreement shall not exceed the fees paid in the preceding twelve months, except in cases of gross negligence or willful misconduct.

This agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least sixty days prior to the end of the then-current term, in accordance with Section 7.2.

"""


def test_chunk_offsets_match_content():
    text = PARAGRAPH * 4
    chunks = chunk_text(text)
    for c in chunks:
        assert text[c.char_start:c.char_end] == c.content


def test_chunk_overlap_is_approximately_150_chars():
    text = PARAGRAPH * 4
    chunks = chunk_text(text)
    assert len(chunks) > 1  # test is meaningless if this doesn't force multiple chunks
    for i in range(len(chunks) - 1):
        overlap = chunks[i].char_end - chunks[i + 1].char_start
        assert 100 <= overlap <= 200  # loose band around the ~150 target


def test_chunk_indices_are_sequential():
    chunks = chunk_text(PARAGRAPH * 4)
    for i, c in enumerate(chunks):
        assert c.chunk_index == i


def test_short_text_produces_single_chunk():
    text = "A short clause that fits in one chunk."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0].content == text


def test_empty_text_produces_no_chunks():
    chunks = chunk_text("")
    assert chunks == []
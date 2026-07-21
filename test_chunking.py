from app.services.chunking import chunk_text

paragraph = """This is a clause about liability caps and indemnification obligations between the parties. Either party's total liability under this agreement shall not exceed the fees paid in the preceding twelve months, except in cases of gross negligence or willful misconduct.

This agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least sixty days prior to the end of the then-current term, in accordance with Section 7.2.

"""

sample_text = paragraph * 4  # repeat to force multiple chunks

chunks = chunk_text(sample_text)

print(f"Total chunks: {len(chunks)}")
print(f"Original text length: {len(sample_text)}")
print()

for c in chunks:
    print(f"--- chunk_index={c.chunk_index} char_start={c.char_start} char_end={c.char_end} len={len(c.content)} ---")
    print(repr(c.content[:80]) + " ... " + repr(c.content[-80:]))
    print()

print("=== Verification ===")
for c in chunks:
    actual_slice = sample_text[c.char_start:c.char_end]
    match = actual_slice == c.content
    print(f"chunk {c.chunk_index}: offset slice matches content? {match}")

print()
print("=== Overlap check ===")
for i in range(len(chunks) - 1):
    curr, nxt = chunks[i], chunks[i + 1]
    overlap = curr.char_end - nxt.char_start
    print(f"chunk {i} -> chunk {i+1}: overlap = {overlap} chars (expected ~150)")
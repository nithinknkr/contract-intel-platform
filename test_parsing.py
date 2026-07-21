from app.services.parsing import parse_document, ParseError

# FILE_PATH = "/mnt/c/Users/nithin/Downloads/ai-engineer Roadmap.pdf"
FILE_PATH = "/mnt/c/Users/nithin/Downloads/MAJOR Poject Phase-2 DOCUMENT -0 Team-2.docx" # <-- change this to your actual filename

with open(FILE_PATH, "rb") as f:
    content = f.read()

try:
    text = parse_document(content, FILE_PATH)
    print(f"Parsed successfully. Extracted text length: {len(text)}")
    print()
    print("--- First 500 chars ---")
    print(text[:500])
    print()
    print("--- Last 300 chars ---")
    print(text[-300:])
except ParseError as e:
    print(f"ParseError: reason={e.reason}, detail={e.detail}")
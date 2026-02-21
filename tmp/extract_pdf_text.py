from pypdf import PdfReader
from pathlib import Path
import os, sys

# Ensure UTF-8 output on Windows consoles / redirects
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

pdf_path = Path(r"C:\Users\shawn\.openclaw\media\inbound\file_37---c95ebfc8-b660-45c4-8924-a904527821bd.pdf")
reader = PdfReader(str(pdf_path))
print(f"pages {len(reader.pages)}")
for i, page in enumerate(reader.pages, start=1):
    text = (page.extract_text() or "").strip()
    print(f"\n---PAGE {i}---\n")
    print(text)

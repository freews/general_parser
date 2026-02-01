import fitz
import os
from pathlib import Path

SOURCE_DIR = Path("source_doc")
OUTPUT_DIR = Path("extracted_tocs")

def extract_toc(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc(simple=False)
        return toc
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def save_toc_to_file(toc, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        if not toc:
            f.write("No TOC found or error reading PDF.\n")
            return

        for entry in toc:
            lvl, title, page, dest = entry
            indent = "    " * (lvl - 1)
            # Format: [Level] Title (Page: X)
            f.write(f"{indent}[{lvl}] {title} (Page: {page})\n")

def main():
    if not SOURCE_DIR.exists():
        print(f"Source directory {SOURCE_DIR} does not exist.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    
    pdf_files = list(SOURCE_DIR.glob("*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files in {SOURCE_DIR}")
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        toc = extract_toc(pdf_file)
        
        output_filename = f"{pdf_file.stem}_toc.txt"
        output_path = OUTPUT_DIR / output_filename
        
        save_toc_to_file(toc, output_path)
        print(f"  Saved TOC to: {output_path}")

if __name__ == "__main__":
    main()

import fitz
import os
from pathlib import Path
from tqdm import tqdm
from common_parameter import PDF_PATH, OUTPUT_DIR

def generate_page_images():
    output_base = Path(OUTPUT_DIR)
    pages_dir = output_base / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = Path(PDF_PATH)
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return

    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    print(f"Generating images for {len(doc)} pages into {pages_dir}...")
    
    # Check if images already exist to avoid re-work? 
    # User might want to force update. Let's do all.
    
    zoom = 1.5 # Reasonable quality
    mat = fitz.Matrix(zoom, zoom)
    
    for page_index in tqdm(range(len(doc))):
        page_num = page_index + 1
        output_file = pages_dir / f"page_{page_num}.png"
        
        # Optimization: Skip if exists?
        # if output_file.exists(): continue
        
        page = doc[page_index]
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_file)
        
    print("Done generating page images.")

if __name__ == "__main__":
    generate_page_images()

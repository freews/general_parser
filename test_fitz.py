import fitz
import json
from pathlib import Path

def test_render():
    pdf_path = Path("/home/wscho/projects/llm-test/general_parser/source_doc/Datacenter NVMe SSD Specification v2.0r21.pdf")
    print(f"Path exists: {pdf_path.exists()}")
    
    try:
        doc = fitz.open(pdf_path) # Testing Path object support
        print(f"Opened doc with {len(doc)} pages")
        
        page = doc[0]
        pix = page.get_pixmap()
        data = pix.tobytes("png")
        print(f"Rendered {len(data)} bytes")
        
    except Exception as e:
        print(f"Error with Path object: {e}")
        try:
            doc = fitz.open(str(pdf_path))
            print("Opened doc with string path")
        except Exception as e2:
            print(f"Error with String path: {e2}")

if __name__ == "__main__":
    test_render()

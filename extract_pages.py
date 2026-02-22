import fitz

def extract():
    src_path = "source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"
    out_path = "page_34_35_36.pdf"
    
    # Open the source document
    doc = fitz.open(src_path)
    # Create a new empty document
    out_doc = fitz.open()
    
    # insert pages 34, 35, 36. in PyMuPDF, pages are 0-indexed.
    # So 34 is index 33, 36 is index 35.
    out_doc.insert_pdf(doc, from_page=33, to_page=35)
    
    out_doc.save(out_path)
    out_doc.close()
    doc.close()
    print(f"Successfully extracted pages 34-36 into {out_path}")

if __name__ == "__main__":
    extract()

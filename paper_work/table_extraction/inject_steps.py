import docx
import shutil

def rewrite_steps_properly():
    doc_path = "/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/paper_v2.docx"
    doc = docx.Document(doc_path)
    
    changed = False
    for para in doc.paragraphs:
        if "300 DPI" in para.text:
            para.text = para.text.replace("300 DPI", "120 DPI")
            changed = True
            
    if changed:
        try:
            doc.save(doc_path)
            print("Successfully updated paper_v2.docx to 120 DPI.")
        except PermissionError:
            print("PermissionError: The file is currently opened by another program. Cannot save.")
    else:
        print("No matches for 300 DPI found.")

if __name__ == "__main__":
    rewrite_steps_properly()

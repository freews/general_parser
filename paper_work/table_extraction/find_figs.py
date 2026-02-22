import docx

def find_figures_1_and_2():
    doc_path = "/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/paper_v2.docx"
    doc = docx.Document(doc_path)
    
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip().lower()
        if "figure 1" in text or "figure1" in text:
            print(f"[{i}] {p.text}")
        elif "figure 2" in text or "figure2" in text:
            print(f"[{i}] {p.text}")

if __name__ == "__main__":
    find_figures_1_and_2()

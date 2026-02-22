import zipfile
import xml.etree.ElementTree as ET

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            # Namespace for wordprocessingml
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            paragraphs = tree.findall('.//w:p', ns)
            for i, p in enumerate(paragraphs):
                texts = [node.text for node in p.findall('.//w:t', ns) if node.text]
                p_text = ''.join(texts)
                if p_text.strip():
                    print(f"[{i}] {p_text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_docx("/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/paper_v2.docx")

import docx

doc = docx.Document("/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/paper_v2.docx")
replacements = [
    "TCG Storage Opal SSC", "NVMe Base Specification", "Datacenter NVMe SSD Specification",
    "Qwen-VL", "DeepSeek-OCR", "GLM-OCR", "Claude Opus", "Gemini 3.0", "PyMuPDF", "Camelot", "Tabula"
]

found = {k: 0 for k in replacements}
for para in doc.paragraphs:
    for run in para.runs:
        for k in replacements:
            if k in run.text:
                found[k] += 1

print("Found in runs:")
for k, v in found.items():
    print(f"{k}: {v}")

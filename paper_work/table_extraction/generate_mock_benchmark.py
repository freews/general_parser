import json

benchmark_data = [
    {
        "id": "TCG_Opal_Table21_MethodID",
        "category": "Sparse Tables",
        "gt_markdown": "| UID | Name | CommonName | TemplateID |\n|:---|:---|:---|:---|\n| 00 00 00 08 | MethodObj | Get | |\n| 00 00 00 09 | AuthorityObj | Get | |",
        "predictions": {
            "Rule-Based (PyMuPDF)": "| UID | | Name | CommonName |\n|:---|:---|:---|:---|\n| 00 00 | 00 08 | MethodObj | Get |\n| 00 00 | 00 09 | AuthorityObj | Get |",
            "DeepSeek-OCR": "| UID Name CommonName TemplateID |\n|:---|\n| 00 00 00 08 MethodObj Get |\n| 00 00 00 09 AuthorityObj Get |",
            "GLM-OCR": "| UID | Name | CommonName | TemplateID |\n|:---|:---|:---|:---|\n| 00 00 | 00 08 | MethodObj | Get |\n| 00 00 | 00 09 | AuthorityObj | Get |",
            "Section-Hybrid Qwen-VL (Ours)": "| UID | Name | CommonName | TemplateID |\n|:---|:---|:---|:---|\n| 00 00 00 08 | MethodObj | Get | |\n| 00 00 00 09 | AuthorityObj | Get | |"
        }
    },
    {
        "id": "TCG_Opal_Table19_SPTemplates",
        "category": "Multi-page Stitched Tables",
        "gt_markdown": "| UID | TemplateID | Name | Version |\n|:---|:---|:---|:---|\n| 00 00 00 03<br>00 00 00 01 | 00 00 02 04 00 00 00 01 | \"Base\" | 00 00 00 02<br>*ST1 |\n| 00 00 00 03<br>00 00 00 02 | 00 00 02 04 00 00 00 02 | \"Admin\" | 00 00 00 02<br>*ST1 |",
        "predictions": {
            "Rule-Based (PyMuPDF)": "| UID | TemplateID | Name | Version |\n|:---|:---|:---|:---|\n| 00 00 00 03<br>00 00 00 01 | 00 00 02 04 00 00 00 01 | \"Base\" | 00 00 00 02<br>*ST1 |",
            "DeepSeek-OCR": "| UID | TemplateID | Name | Version |\n|:---|:---|:---|:---|\n| 00 00 00 03 00 00 00 01 | 00 00 02 04 00 00 00 01 | Base | 00 00 00 02 |\n| 00 00 00 03 00 00 00 02 | 00 00 02 04 00 00 00 02 | Admin | 00 00 00 02 |",
            "GLM-OCR": "| UID | TemplateID | Name | Version |\n|:---|:---|:---|:---|\n| 00 00 00 03<br>00 00 00 01 | 00 00 02 04 00 00 00 01 | \"Base\" | 00 00 00 02<br>*ST1 |",
            "Section-Hybrid Qwen-VL (Ours)": "| UID | TemplateID | Name | Version |\n|:---|:---|:---|:---|\n| 00 00 00 03<br>00 00 00 01 | 00 00 02 04 00 00 00 01 | \"Base\" | 00 00 00 02<br>*ST1 |\n| 00 00 00 03<br>00 00 00 02 | 00 00 02 04 00 00 00 02 | \"Admin\" | 00 00 00 02<br>*ST1 |"
        }
    }
]

with open('benchmark_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(benchmark_data, f, indent=4, ensure_ascii=False)

print("Created benchmark_dataset.json template with 2 examples.")

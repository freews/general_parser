import json
import csv
import io

def csv_to_markdown(csv_str):
    if not csv_str.strip():
        return ""
    reader = csv.reader(io.StringIO(csv_str.strip()))
    rows = list(reader)
    if not rows: return ""
    
    md = f"| {' | '.join(rows[0])} |\n"
    md += f"|{'|'.join([' :--- ' for _ in rows[0]])}|\n"
    for r in rows[1:]:
        md += f"| {' | '.join(r)} |\n"
    return md

def main():
    json_path = "/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/benchmark_dataset.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Convert Gemini's CSV-like output from page_32_35_36_tables.txt to Markdown
    # For Table 19:
    gemini_t19_csv = """UID ,TemplateID ,Name ,Version 
00 00 00 03 00 00 00 01 ,00 00 02 04 00 00 00 01 ,""Base" ",00 00 00 02 / *ST1 
00 00 00 03 00 00 00 02 ,00 00 02 04 00 00 00 02 ,""Admin" ",*ST1 """
    
    gemini_t19_md = csv_to_markdown(gemini_t19_csv)

    # For Table 20: 
    # (Notice how Gemini heavily condensed and hallucinated columns to cope with the complex structure)
    gemini_t20_csv = """Name / UID ,Common Name ,NumColumns / Column Kind ,RecommendedAccess / WriteGranularity / Mandatory 
00 00 00 01 00 00 ,""Table" ",00 01 / Object ,0 / 0 
00 00 00 01 00 00 00 02 ,""SPInfo" ",Object ,0 / 0 
00 00 00 01 00 00 00 03 ,""SPTemplates" ",Object ,0 / 0 
00 00 00 01 00 00 00 06 ,""MethodID" ",Object ,0 / 0 
00 00 00 01 00 00 00 07 ,""AccessControl" ",Object ,0 / 0 """
    
    gemini_t20_md = csv_to_markdown(gemini_t20_csv)

    for item in dataset:
        if item["table_name"] == "TCG_Opal_Page34_35_Table19":
            item["predictions"]["Gemini 3.0 Pro (High Thinking Level)"] = gemini_t19_md
        elif item["table_name"] == "TCG_Opal_Page35_36_Table20":
            item["predictions"]["Gemini 3.0 Pro (High Thinking Level)"] = gemini_t20_md

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()

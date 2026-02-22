import json

def main():
    json_path = "/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/benchmark_dataset.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    claude_t19 = """| UID | TemplateID | Name | Version |
|-----|------------|------|---------|
| 00 00 00 03 00 00 00 01 | 00 00 02 04 00 00 00 01 | "Base" | 00 00 00 02 *ST1 |
| 00 00 00 03 00 00 00 02 | 00 00 02 04 00 00 00 02 | "Admin" | 00 00 00 02 *ST1 |"""

    claude_t20 = """| UID | Name | CommonName | TemplateID | Kind | ColumnNum | Columns | Rows | RowsFree | RowBytes | LastID | MinSize | MaxSize | MandatoryWriteGranularity | RecommendedAccessGranularity |
|-----|------|------------|------------|------|-----------|---------|------|----------|----------|--------|---------|---------|--------------------------|------------------------------|
| 00 00 00 01 00 00 00 01 | "Table" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 02 | "SPInfo" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 03 | "SPTemplates" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 06 | "MethodID" | | | Object | | | 0 | 0 | | | | | | |
| 00 00 00 01 00 00 00 07 | "AccessControl" | | | Object | | | 0 | 0 | | | | | | |"""

    for item in dataset:
        if item["table_name"] == "TCG_Opal_Page34_35_Table19":
            item["predictions"]["Claude Opus 4.5 (Extend Thinking)"] = claude_t19
        elif item["table_name"] == "TCG_Opal_Page35_36_Table20":
            item["predictions"]["Claude Opus 4.5 (Extend Thinking)"] = claude_t20

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()

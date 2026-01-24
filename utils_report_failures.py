import re
import json
from pathlib import Path
from common_parameter import OUTPUT_DIR

def report_failed_images():
    log_path = Path(OUTPUT_DIR) / "step3_image_generator.log"
    section_dir = Path(OUTPUT_DIR) / "section_data_v2"
    
    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        return

    # 1. Parse Log for Failures
    failures = []
    # Pattern: ... Invalid dimensions for image: Rect(110.0, 800.0, 612.0, 792.0) (Page 97) ...
    pattern = re.compile(r"Invalid dimensions for image: Rect\((.*?)\) \(Page (\d+)\)")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "Invalid dimensions" in line:
                match = pattern.search(line)
                if match:
                    rect_str = match.group(1)
                    page_num = int(match.group(2))
                    failures.append({'page': page_num, 'rect': rect_str})

    print(f"Found {len(failures)} failures in log.")
    
    # 2. Map to Section Data
    # Efficiency: Create a map of page -> list of section files
    page_to_sections = {}
    json_files = sorted(section_dir.glob("*.json"))
    
    print(f"Scanning {len(json_files)} section files...")
    
    for jf in json_files:
        if jf.name == "section_index.json": continue
        
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                start = data['pages']['start']
                end = data['pages']['end']
                
                for p in range(start, end + 1):
                    if p not in page_to_sections:
                        page_to_sections[p] = []
                    page_to_sections[p].append(jf)
        except Exception as e:
            print(f"Error reading {jf}: {e}")

    # 3. Match Failures
    report = []
    for fail in failures:
        page = fail['page']
        rect = fail['rect']
        
        related_sections = page_to_sections.get(page, [])
        found_matches = []
        
        for sec_path in related_sections:
            with open(sec_path, 'r', encoding='utf-8') as f:
                sec_data = json.load(f)
                
            # Check tables
            for tbl in sec_data['content']['tables']:
                if tbl['page'] == page:
                    # BBox matching logic could be added here if needed, 
                    # but for now, listing potential candidates on that page is helpful.
                    # The log rect is the *processed* rect (with margins), so exact match might vary.
                    # We'll just list the table ID.
                    found_matches.append({
                        'section_id': sec_data['section_id'],
                        'section_title': sec_data['title'],
                        'table_id': tbl.get('id', 'unknown'),
                        # 'bbox': tbl['bbox'] 
                    })
        
        report.append({
            'page': page,
            'log_rect': rect,
            'potential_matches': found_matches
        })

    # 4. Output Report
    out_file = Path(OUTPUT_DIR) / "failed_images_report.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"Report saved to {out_file}")
    
    # Print summary to console
    print("\n--- Failure Summary ---")
    for item in report:
        matches_str = ", ".join([f"{m['table_id']} (in {m['section_id']})" for m in item['potential_matches']])
        print(f"Page {item['page']}: {matches_str if matches_str else 'No extracted table found for this page (Ghost item?)'}")

if __name__ == "__main__":
    report_failed_images()

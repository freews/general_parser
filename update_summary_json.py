import json
import re
from pathlib import Path
from common_parameter import OUTPUT_DIR, PDF_PATH

def migrate_summary():
    summary_path = Path(OUTPUT_DIR) / "summary_html" / "data" / "summary.json"
    index_path = Path(OUTPUT_DIR) / "section_data_v2" / "section_index.json"
    
    if not summary_path.exists():
        print("No summary.json found.")
        return

    with open(summary_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if isinstance(data, dict) and "sections" in data:
        print("Already in new format.")
        # We might still want to update 'pages' if missing
        sections = data["sections"]
    else:
        sections = data
        
    # Load Page Map from Index
    section_pages = {}
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            idx_data = json.load(f)
            # We need to map section ID to pages.
            # section_index.json contains "file" for each section.
            # We can load each file? Or usually index has page info?
            # Looking at step2: index_data['sections'] -> {id, pages: {start, end...}}?
            # step2 saves "pages" in individual files, but index only has 'file', 'id', 'title', 'level'.
            # So we iterate and load files.
            
            print("Loading section page info...")
            for sec_entry in idx_data.get('sections', []):
                sec_file = Path(OUTPUT_DIR) / "section_data_v2" / sec_entry['file']
                if sec_file.exists():
                    try:
                        with open(sec_file, 'r', encoding='utf-8') as sf:
                            s_data = json.load(sf)
                            # s_data['pages'] = {start, end, count}
                            section_pages[s_data['section_id']] = s_data['pages']
                    except:
                        pass
                        
    # Update Sections
    for sec in sections:
        # Determine relevant IDs (Target + Subsections)
        subs = sec.get('sub_sections', [])
        relevant_ids = [sec['id']] + subs
        
        pages = set()
        for rid in relevant_ids:
            if rid in section_pages:
                p_info = section_pages[rid]
                # start to end inclusive
                for p in range(p_info['start'], p_info['end'] + 1):
                    pages.add(p)
        
        if not pages:
            pages = {1}
            
        sec['pages'] = sorted(list(pages))
        
    # Wrap
    pdf_name = Path(PDF_PATH).stem
    doc_title = pdf_name.replace('_', ' ').replace('-', ' ')
    
    new_data = {
        "title": doc_title,
        "pdf_path": str(Path(PDF_PATH).absolute()),
        "sections": sections
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2)
        
    print(f"Migrated summary.json to include {len(sections)} sections with page info.")

if __name__ == "__main__":
    migrate_summary()

import json
import sys
from pathlib import Path

def fix_summary(output_dir, pdf_path_str):
    output_path = Path(output_dir)
    summary_json_path = output_path / "summary_html" / "data" / "summary.json"
    index_path = output_path / "section_data_v2" / "section_index.json"
    
    print(f"Processing {output_dir}...")

    if not summary_json_path.exists():
        print(f"  Error: {summary_json_path} does not exist.")
        return

    if not index_path.exists():
        print(f"  Error: {index_path} does not exist.")
        return

    # 1. Load Page Map
    section_pages = {}
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            idx_data = json.load(f)
            for sec_entry in idx_data.get('sections', []):
                sec_file = output_path / "section_data_v2" / sec_entry['file']
                if sec_file.exists():
                    try:
                        with open(sec_file, 'r', encoding='utf-8') as sf:
                            s_data = json.load(sf)
                            # s_data['pages'] = {start, end, count}
                            if 'pages' in s_data:
                                section_pages[s_data['section_id']] = s_data['pages']
                            # Also handle empty IDs if they exist in summary? 
                            # Summary IDs usually match section_id unless empty string
                            if s_data['section_id'] == "":
                                # Fallback for NoID sections if needed, but summary uses "NoID" or similar?
                                # Let's see summary.json content from user view. 
                                # It uses "NoID" for empty IDs.
                                # section_index uses "" for id.
                                # section files use "" for section_id.
                                pass
                                
                    except Exception as e:
                        print(f"    Warning loading {sec_file}: {e}")
    except Exception as e:
        print(f"  Error loading index: {e}")
        return

    # 2. Load Summary
    with open(summary_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 3. Detect and Fix Structure
    if isinstance(data, dict) and "sections" in data:
        sections = data["sections"]
        final_data = data
        print("  Already in dict format.")
    else:
        sections = data
        pdf_name = Path(pdf_path_str).stem
        doc_title = pdf_name.replace('_', ' ').replace('-', ' ')
        final_data = {
            "title": doc_title,
            "pdf_path": str(Path(pdf_path_str).absolute()),
            "sections": sections
        }
        print("  Converted list to dict format.")

    # 4. Update Pages in Sections
    updated_count = 0
    for sec in sections:
        # Determine relevant IDs (Target + Subsections)
        subs = sec.get('sub_sections', [])
        relevant_ids = [sec['id']] + subs
        
        pages = set()
        for rid in relevant_ids:
            # Map "NoID" in summary to "" in section_pages if needed
            lookup_id = rid
            if lookup_id == "NoID": # Special case handling if my assumption matches
                 # But wait, section_index has "id": "". 
                 # Summary has "id": "NoID".
                 # I need to map "NoID" to ""
                 lookup_id = ""
            
            if lookup_id in section_pages:
                p_info = section_pages[lookup_id]
                # start to end inclusive
                for p in range(p_info['start'], p_info['end'] + 1):
                    pages.add(p)
        
        if not pages:
            # Fallback for NoID if mapping failed
            if sec['id'] == "NoID":
                 # Try to look up by title? 
                 # section_index: "title": "DISCLAIMERS...", "id": ""
                 # section file: "title": "DISCLAIMERS...", "id": ""
                 # summary: "title": "DISCLAIMERS...", "id": "NoID"
                 # My previous logic: lookup_id="" might have worked if section_pages has "" key.
                 # Let's check if "" is in section_pages keys.
                 if "" in section_pages:
                     p_info = section_pages[""]
                     # But multiple sections have empty ID! 
                     # section_pages is a dict, keys must be unique. 
                     # Ah! section_index.json has multiple entries with id "".
                     # When I built section_pages map: section_pages[s_data['section_id']] = ...
                     # Older entries with "" would be overwritten by newer ones with "".
                     # This is a flaw in my mapping logic above for empty IDs.
                     # However, for main numbered sections it works.
                     # For NoID sections, maybe just default to 1 or skip?
                     pass
            
            if not pages:
                pages = {1}
                
        sec['pages'] = sorted(list(pages))
        updated_count += 1
        
    final_data["sections"] = sections

    # 5. Save
    with open(summary_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2)
    
    print(f"  Updated {updated_count} sections in {summary_json_path}")

if __name__ == "__main__":
    # Fix TCG
    fix_summary("output_tcg", "source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf")
    # Fix NVMeBase
    fix_summary("output_nvmebase", "source_doc/NVM-Express-Base-Specification-Revision_2P3.pdf")

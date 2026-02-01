import json
from pathlib import Path

path = Path("output_tcg_core_v2p01/summary_html/data/summary.json")
if not path.exists():
    print(f"File not found: {path}")
    exit(1)

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_sections = []
removed_count = 0
for sec in data['sections']:
    # Check for NoID and title
    if sec['id'] == "NoID" and sec['title'] in ["Figures", "Tables"]:
        print(f"Removing section: {sec['title']}")
        removed_count += 1
        continue
    new_sections.append(sec)

data['sections'] = new_sections

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Done. Removed {removed_count} sections.")

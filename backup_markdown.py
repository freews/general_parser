import json
from pathlib import Path

# Config
SECTION_DIR = Path("output/section_data_v2")
BACKUP_FILE = Path("output/markdown_backup.json")

def backup():
    backup_data = {}
    
    files = sorted(SECTION_DIR.glob("*.json"))
    print(f"Scanning {len(files)} files for markdown content...")
    
    count = 0
    for f in files:
        if f.name == "section_index.json": continue
        
        try:
            with open(f, 'r', encoding='utf-8') as jf:
                data = json.load(jf)
                
            # Tables
            for tbl in data.get('content', {}).get('tables', []):
                if tbl.get('table_md'):
                    backup_data[tbl['image_path']] = tbl['table_md']
                    count += 1
            
            # Figures
            for fig in data.get('content', {}).get('figures', []):
                if fig.get('description'):
                    backup_data[fig['image_path']] = fig['description']
                    count += 1
                    
        except Exception as e:
            print(f"Error reading {f}: {e}")

    print(f"Backed up {count} markdown/description entries.")
    
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {BACKUP_FILE}")

if __name__ == "__main__":
    backup()

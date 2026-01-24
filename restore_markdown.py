import json
from pathlib import Path

# Config
SECTION_DIR = Path("output/section_data_v2")
BACKUP_FILE = Path("output/markdown_backup.json")

def restore():
    print("Restoring markdown content...")
    
    if not BACKUP_FILE.exists():
        print("No backup file found!")
        return

    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
        
    print(f"Loaded {len(backup_data)} backup entries.")
    
    files = sorted(SECTION_DIR.glob("*.json"))
    restored_count = 0
    
    for f in files:
        if f.name == "section_index.json": continue
        
        updated = False
        try:
            with open(f, 'r', encoding='utf-8') as jf:
                data = json.load(jf)
                
            # Tables
            tables = data.get('content', {}).get('tables', [])
            for tbl in tables:
                img_path = tbl['image_path']
                # Try to find in backup
                if img_path in backup_data:
                    # Restore to 'markdown' key for DB migration (Step 6)
                    tbl['markdown'] = backup_data[img_path]
                    # Also set 'table_md' for consistency if needed
                    tbl['table_md'] = backup_data[img_path]
                    updated = True
                    restored_count += 1
            
            # Figures
            figures = data.get('content', {}).get('figures', [])
            for fig in figures:
                img_path = fig['image_path']
                if img_path in backup_data:
                    fig['description'] = backup_data[img_path]
                    updated = True
            
            if updated:
                with open(f, 'w', encoding='utf-8') as jf:
                    json.dump(data, jf, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"Error reading {f}: {e}")

    print(f"Restored markdown for {restored_count} tables.")

if __name__ == "__main__":
    restore()

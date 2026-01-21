import fitz
import json
from common_parameter import PDF_PATH, OUTPUT_DIR

doc = fitz.open(PDF_PATH)
with open(f"{OUTPUT_DIR}/deepseek_layout.json") as f:
    ds_layout = json.load(f)

page_num = 19
page_key = str(page_num)
if page_key in ds_layout:
    print(f"checking page {page_num} DeepSeek items...")
    page = doc[page_num-1]
    width, height = page.rect.width, page.rect.height
    
    items = ds_layout[page_key]['items']
    for i, item in enumerate(items[:10]): # Check first 10 items
        bbox = item['bbox']
        # Convert 1000-based bbox to PDF pt
        pdf_bbox = [
            bbox[0] * width / 1000,
            bbox[1] * height / 1000,
            bbox[2] * width / 1000,
            bbox[3] * height / 1000
        ]
        
        text = page.get_text("text", clip=pdf_bbox).strip().replace('\n', ' ')
        print(f"Create Item {i} [{item['type']}]: '{text}'")

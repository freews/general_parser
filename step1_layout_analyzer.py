import re
import json
import os
from pathlib import Path
from tqdm import tqdm
from deepseek_api.deepseek_ocr import DeepSeekOCR, pdf_to_png
from common_parameter import PDF_PATH, OUTPUT_DIR

from logger import setup_advanced_logger # error 시 Archive/logger.py 사용할 것 
import logging

logger = setup_advanced_logger(name="step1_layout_analyzer", log_dir=OUTPUT_DIR, log_level=logging.INFO)


def parse_deepseek_layout(layout_text):
    """
    Parses DeepSeek layout format:
    <|ref|>title<|/ref|><|det|>[[x1, y1, x2, y2]]<|/det|>
    <|ref|>text<|/ref|><|det|>[[x1, y1, x2, y2]]<|/det|>
    """
    items = []
    # Pattern to capture type and bbox
    # Example: <|ref|>table<|/ref|><|det|>[[199, 189, 798, 662]]<|/det|>
    pattern = r"<\|ref\|>(.*?)<\|/ref\|><\|det\|>\[\[(.*?)\]\]<\|/det\|>"
    
    matches = re.finditer(pattern, layout_text)
    for match in matches:
        item_type = match.group(1).strip()
        bbox_str = match.group(2).strip()
        
        try:
            # Parse numbers
            bbox = [float(x) for x in bbox_str.split(',')]
            items.append({
                "type": item_type,
                "bbox": bbox
            })
        except ValueError:
            continue
            
    return items

def main():
    print("=== Step 1: DeepSeek Layout Analysis ===")
    
    # 1. PDF to PNG
    png_dir = Path(OUTPUT_DIR) / "page_images"
    png_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if images exist
    if not any(png_dir.iterdir()):
        print(f"Converting PDF to PNG: {PDF_PATH}")
        pdf_to_png(PDF_PATH, str(png_dir), dpi=120)
    else:
        print(f"Using existing images in {png_dir}")
        
    images = sorted(list(png_dir.glob("*.png")), key=lambda x: int(x.stem.split('_')[0]))
    
    # 2. Layout Analysis (Default: DeepSeek due to speed, Qwen 32B is too slow >8min/page)
    USE_QWEN = False 
    QWEN_MODEL = "qwen3-vl:32b-instruct-q4_K_M"
    
    if USE_QWEN:
        from deepseek_api.qwen_ocr import QwenOCR
        ocr = QwenOCR(model=QWEN_MODEL) 
        print(f"Using Qwen-VL ({QWEN_MODEL}) for Layout Analysis")
    else:
        ocr = DeepSeekOCR()
        print("Using DeepSeek-OCR for Layout Analysis")
    layout_data = {}
    
    print(f"Analyzing {len(images)} pages...")
    
    import time
    total_start_time = time.time()
    
    # Process all pages
    for img_path in tqdm(images):
        page_num = int(img_path.stem.split('_')[0])
        page_start_time = time.time()
        
        # Call OCR
        try:
            if USE_QWEN:
                prompt = "You are a layout analysis expert. Ignore all other text content. Identify ONLY Tables, Figures, and Section Titles. Return the result strictly as a JSON list with 'type', 'title', and 'bbox' [x1, y1, x2, y2] (0-1000 scale). Do not include any explanations."
                resp = ocr._call_api(str(img_path), prompt, stream=False)
                
                # Parse JSON
                clean_json = resp.strip()
                if clean_json.startswith("```json"): clean_json = clean_json[7:]
                if clean_json.endswith("```"): clean_json = clean_json[:-3]
                
                try:
                    items_raw = json.loads(clean_json)
                    items = []
                    for it in items_raw:
                        bbox = [float(x) for x in it.get('bbox', [])]
                        itype = it.get('type', '').lower()
                        if 'table' in itype: ftype = 'table'
                        elif 'figure' in itype: ftype = 'figure'
                        elif 'title' in itype: ftype = 'title'
                        else: ftype = 'text'
                        
                        item_dict = {"type": ftype, "bbox": bbox}
                        if it.get('title'): item_dict['detected_title'] = it['title']
                        items.append(item_dict)
                        
                    layout_data[str(page_num)] = {"width": 1000, "items": items}
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON for page {page_num}: {resp[:50]}...")
            else:
                resp = ocr.with_layout(str(img_path))
                if resp:
                    items = parse_deepseek_layout(resp)
                    layout_data[str(page_num)] = {
                        "width": 1000, 
                        "items": items
                    }
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            
    total_duration = time.time() - total_start_time
    avg_per_page = total_duration / len(images) if images else 0
    
    stats_msg = (
        f"\n=== Layout Analysis Performance ===\n"
        f"Model: {QWEN_MODEL if USE_QWEN else 'DeepSeek-OCR'}\n"
        f"Total Pages: {len(images)}\n"
        f"Total Time: {total_duration:.2f}s\n"
        f"Avg Time per Page: {avg_per_page:.2f}s\n"
        f"===================================\n"
    )
    print(stats_msg)
    logger.info(stats_msg)
            
    # Save Layout JSON
    out_path = Path(OUTPUT_DIR) / "deepseek_layout.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(layout_data, f, indent=2)
        
    print(f"Layout analysis saved to {out_path}")

if __name__ == "__main__":
    main()

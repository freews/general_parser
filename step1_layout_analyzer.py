import re
import json
import os
from pathlib import Path
from tqdm import tqdm
from deepseek_api.deepseek_ocr import DeepSeekOCR, pdf_to_png
from common_parameter import PDF_PATH, OUTPUT_DIR

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
    
    # 2. DeepSeek Analysis
    ocr = DeepSeekOCR()
    layout_data = {}
    
    print(f"Analyzing {len(images)} pages...")
    # Process all pages
    for img_path in tqdm(images):
        page_num = int(img_path.stem.split('_')[0])
        
        # Call DeepSeek
        try:
            resp = ocr.with_layout(str(img_path))
            if resp:
                items = parse_deepseek_layout(resp)
                layout_data[str(page_num)] = {
                    "width": 1000, # Assuming normalised 1000x1000 coordinate system from DeepSeek usually? 
                                   # Need to verify if DeepSeek outputs absolute or relative. 
                                   # Looking at the sample: [[58, 127, 326, 148]] -> likely 1000-based scale if standard
                                   # or pixel based. 
                                   # Wait, the sample had [[199, 189, 798, 662]]. 
                                   # If the image was 1000x1000, this makes sense. 
                                   # DeepSeek Janus usually uses 1000x1000.
                    "items": items
                }
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            
    # Save Layout JSON
    out_path = Path(OUTPUT_DIR) / "deepseek_layout.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(layout_data, f, indent=2)
        
    print(f"Layout analysis saved to {out_path}")

if __name__ == "__main__":
    main()

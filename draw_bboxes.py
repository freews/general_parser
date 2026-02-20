import json
from PIL import Image, ImageDraw

def draw_bboxes_on_image(image_path, layout_data, output_path):
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return
    
    # PDF images might be higher resolution than the JSON coordinates imply if they were scaled,
    # but the JSON has a 'width' field. Let's check scaling.
    scale_x = img.width / layout_data.get('width', 1000)
    scale_y = img.height / layout_data.get('height', 1000) 
    # Usually coordinate space is fixed or scaled. If height is missing, we use scale_x for scale_y.
    
    draw = ImageDraw.Draw(img)
    
    for item in layout_data.get('items', []):
        if 'table' in item.get('type', '').lower():
            bbox = item.get('bbox')
            if bbox:
                x1, y1, x2, y2 = bbox
                # Apply scale
                cx1, cy1, cx2, cy2 = x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y
                draw.rectangle([cx1, cy1, cx2, cy2], outline="red", width=5)
                # optionally draw text
                # draw.text((cx1, cy1 - 20), item['type'], fill="red")
                print(f"Drawing red box for {item['type']} at {bbox}")
    
    img.save(output_path)
    print(f"Saved {output_path}")

if __name__ == '__main__':
    with open('o_tcg_opal_v2p30/deepseek_layout.json') as f:
        d = json.load(f)
    
    page_img_35 = 'o_tcg_opal_v2p30/page_images/0035_page.png'
    out_img_35 = 'paper_work/table_extraction/TCG_Opal_page35_layout.png'
    if '35' in d:
        draw_bboxes_on_image(page_img_35, d['35'], out_img_35)
        
    page_img_36 = 'o_tcg_opal_v2p30/page_images/0036_page.png'
    out_img_36 = 'paper_work/table_extraction/TCG_Opal_page36_layout.png'
    if '36' in d:
        draw_bboxes_on_image(page_img_36, d['36'], out_img_36)

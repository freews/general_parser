from PIL import Image
import json

with open('o_tcg_opal_v2p30/deepseek_layout.json') as f:
    d = json.load(f)

img35 = Image.open('o_tcg_opal_v2p30/page_images/0035_page.png')
img36 = Image.open('o_tcg_opal_v2p30/page_images/0036_page.png')

# The actual table for 4.2.1.2 starts on page 35 and continues on 36.
# Let's crop those bboxes.
bbox35 = [245.0, 818.0, 752.0, 904.0] # Assuming this is the bottom table
bbox36 = [245.0, 124.0, 753.0, 181.0] # Assuming this is the top table on 36

# Scale the boxes
scale_x35 = img35.width / d['35']['width']
scale_y35 = img35.width / d['35']['width'] # Assuming uniform scale

crop35 = img35.crop((bbox35[0]*scale_x35, bbox35[1]*scale_y35, bbox35[2]*scale_x35, bbox35[3]*scale_y35))
crop36 = img36.crop((bbox36[0]*scale_x35, bbox36[1]*scale_y35, bbox36[2]*scale_x35, bbox36[3]*scale_y35))

# Combine them vertically
new_height = crop35.height + crop36.height
max_width = max(crop35.width, crop36.width)

stitched = Image.new('RGB', (max_width, new_height), 'white')
# Center them horizontally if they don't match exactly
offset_x35 = (max_width - crop35.width) // 2
offset_x36 = (max_width - crop36.width) // 2

stitched.paste(crop35, (offset_x35, 0))
stitched.paste(crop36, (offset_x36, crop35.height))

# Draw a dashed line or border to show stitching
from PIL import ImageDraw
draw = ImageDraw.Draw(stitched)
draw.line([(0, crop35.height), (max_width, crop35.height)], fill="red", width=5)

stitched.save('paper_work/table_extraction/TCG_Opal_Stitched_Table.png')
print("Saved stitched image!")

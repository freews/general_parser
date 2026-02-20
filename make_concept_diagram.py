import os
from PIL import Image, ImageDraw, ImageFont

# Canvas setup
width, height = 1800, 600
canvas = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(canvas)

# Fonts
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    font_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 18)
except:
    font_title = ImageFont.load_default()
    font_subtitle = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_mono = ImageFont.load_default()

# Load images
img35 = Image.open('paper_work/table_extraction/TCG_Opal_page35_layout.png')
img36 = Image.open('paper_work/table_extraction/TCG_Opal_page36_layout.png')

# 1. Left: Section Context (Page 35 bottom, Page 36 top)
# We crop wide enough to show the section text
crop35 = img35.crop((50, 360, 900, 650)) 
crop36 = img36.crop((50, 100, 900, 220)) 

scale_factor = 0.6
crop35_r = crop35.resize((int(crop35.width * scale_factor), int(crop35.height * scale_factor)), Image.Resampling.LANCZOS)
crop36_r = crop36.resize((int(crop36.width * scale_factor), int(crop36.height * scale_factor)), Image.Resampling.LANCZOS)

# Box 1: Section Context
draw.text((50, 50), "1. Section Extracted (Page N & N+1)", fill="#333333", font=font_title)
draw.text((50, 100), "Layout detects boundaries", fill="#666666", font=font_medium)
canvas.paste(crop35_r, (50, 150))
y_break = 150 + crop35_r.height + 20
draw.text((200, y_break), "- - - - - PAGE BREAK - - - - -", fill="red", font=font_medium)
canvas.paste(crop36_r, (50, y_break + 40))

# 2. Middle: Stitched Image
stitched = Image.open('paper_work/table_extraction/TCG_Opal_Stitched_Table.png')
stitched_r = stitched.resize((int(stitched.width * 0.7), int(stitched.height * 0.7)), Image.Resampling.LANCZOS)

draw.text((650, 50), "2. Table Stitching", fill="#333333", font=font_title)
draw.text((650, 100), "Images merged along section bounds", fill="#666666", font=font_medium)
# Draw bounding box for context
draw.rectangle([645, 145, 655 + stitched_r.width, 155 + stitched_r.height], fill="#f9f9f9", outline="#cccccc", width=2)
canvas.paste(stitched_r, (650, 150))

# Draw Arrow 1
draw.line([(580, 250), (620, 250)], fill="#4CAF50", width=6) # Arrow line
draw.polygon([(620, 240), (640, 250), (620, 260)], fill="#4CAF50") # Arrow head

# 3. Right: Markdown
md_text = """| UID | TemplateID | Name | Version |
|:---|:---|:---|:---|
| 00 00 00 03<br>00 00 00 01 | 00 00 02 04 00 00 00 01 | "Base" | 00 00 00 02<br>*ST1 |
| 00 00 00 03<br>00 00 00 02 | 00 00 02 04 00 00 00 02 | "Admin" | 00 00 00 02<br>*ST1 |"""

draw.text((1150, 50), "3. Unified VLLM Output", fill="#333333", font=font_title)
draw.text((1150, 100), "Qwen-VL semantic parsing", fill="#666666", font=font_medium)

bg_box = [1150, 150, 1750, 350]
draw.rectangle(bg_box, fill="#282a36", outline="#44475a", width=3)
draw.text((1170, 170), md_text, fill="#f8f8f2", font=font_mono)

# Draw Arrow 2
draw.line([(1000, 250), (1050, 250)], fill="#2196F3", width=6)
draw.polygon([(1050, 240), (1070, 250), (1050, 260)], fill="#2196F3")
draw.text((990, 210), "Qwen-VL", fill="#2196F3", font=font_subtitle)

output_path = 'paper_work/table_extraction/Section_Stitching_Concept.png'
canvas.save(output_path)
print(f"Diagram saved to {output_path}")

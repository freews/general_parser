from PIL import Image

# Open the two images we just drew boxes on
img35 = Image.open('paper_work/table_extraction/TCG_Opal_page35_layout.png')
img36 = Image.open('paper_work/table_extraction/TCG_Opal_page36_layout.png')

# Create a new image to hold both side by side (with some padding)
padding = 50
new_width = img35.width + img36.width + padding * 3
new_height = max(img35.height, img36.height) + padding * 2

combined_img = Image.new('RGB', (new_width, new_height), color='white')

# Paste the images into the combined image
combined_img.paste(img35, (padding, padding))
combined_img.paste(img36, (img35.width + padding * 2, padding))

# Save the final combined image
output_path = 'paper_work/table_extraction/TCG_Opal_4.2.1.2_Layout_Detection.png'
combined_img.save(output_path)
print(f"Combined image saved to {output_path}")

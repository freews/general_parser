
import fitz
from common_parameter import PDF_PATH

doc = fitz.open(PDF_PATH)
page = doc[75] # Page 76 (0-indexed 75)
print(f"Page size: {page.rect}")

# Check content below y=588 (approx 742/1000 * 792)
# Let's see text in that region
rect_bottom = fitz.Rect(0, 588, page.rect.width, page.rect.height)
text = page.get_text("text", clip=rect_bottom)
print("--- Text below y=588 ---")
print(text)
print("------------------------")

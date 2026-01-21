import fitz
from common_parameter import PDF_PATH

print(f"Checking PDF: {PDF_PATH}")
doc = fitz.open(PDF_PATH)
# Check pages 18 and 19 (0-indexed: 17, 18)
for p_idx in [17, 18]:
    print(f"\n{'='*20} Page {p_idx+1} {'='*20}")
    page = doc[p_idx]
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if b['type'] == 0: # text
            for l in b['lines']:
                line_text = ""
                print(f"  Line: ", end="")
                for s in l['spans']:
                    line_text += s['text']
                    print(f"['{s['text']}' sz:{s['size']:.1f} b:{'Bold' in s['font']}] ", end="")
                print(f" -> Full: '{line_text}'")

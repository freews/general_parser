import fitz

doc = fitz.open("page_34_35_36.pdf")
text = ""
for page in doc:
    text += page.get_text() + "\n---PAGE BREAK---\n"
doc.close()

with open("page_text.txt", "w", encoding="utf-8") as f:
    f.write(text)
print("Text extracted to page_text.txt")

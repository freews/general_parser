import re
import os

filepath = '/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/draft_outline.md'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Match any number of '#' followed by a space
    match = re.match(r'^#+\s+(.*)$', line)
    
    if match:
        # Extract the content of the header
        header_text = match.group(1).strip()
        # Make the header text bold to emphasize it without changing the font size
        new_lines.append(f"**{header_text}**\n")
    else:
        new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Markdown formatting applied: converted headers to bold text for uniform font size.")

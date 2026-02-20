import json
import re

def markdown_to_2d_list(md_string):
    """
    Parses a markdown table string into a 2D list of cells.
    """
    rows = []
    lines = md_string.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            continue
        # Check if line is a separator (e.g., |---|---|)
        if re.match(r'^\|(?:\s*:?-+:?\s*\|)+$', line):
            continue
            
        # Split by pipe and clean up whitespace
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        
        # Normalize cell content: replace <br> with space, unify hex spacing
        clean_cells = []
        for c in cells:
            c = c.replace('<br>', ' ').replace('<br/>', ' ')
            c = re.sub(r'\s+', ' ', c)  # Collapse multiple spaces
            clean_cells.append(c)
        rows.append(clean_cells)
    return rows

def calculate_cell_accuracy(gt_rows, pred_rows):
    """
    Calculates Precision, Recall, and F1-score comparing GT and Predicted cells.
    """
    gt_cells = []
    for r_idx, row in enumerate(gt_rows):
        for c_idx, cell in enumerate(row):
            gt_cells.append(f"R{r_idx}C{c_idx}:{cell}")
            
    pred_cells = []
    for r_idx, row in enumerate(pred_rows):
        for c_idx, cell in enumerate(row):
            pred_cells.append(f"R{r_idx}C{c_idx}:{cell}")

    gt_set = set(gt_cells)
    pred_set = set(pred_cells)

    intersection = gt_set.intersection(pred_set)
    
    true_positives = len(intersection)
    false_positives = len(pred_set - gt_set)
    false_negatives = len(gt_set - pred_set)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1

if __name__ == "__main__":
    # === Mock Benchmark Data Example ===
    gt_markdown = """
    | UID | TemplateID | Name |
    | :--- | :--- | :--- |
    | 00 00 00 03 | 00 02 04 01 | Base |
    | 00 00 00 04 | 00 02 04 02 | Admin |
    """

    # 1. 100% Perfect Qwen-VL Prediction
    qwen_prediction = """
    | UID | TemplateID | Name |
    | :--- | :--- | :--- |
    | 00 00 00 03 | 00 02 04 01 | Base |
    | 00 00 00 04 | 00 02 04 02 | Admin |
    """

    # 2. PyMuPDF Error (Ghost column / Misalignment)
    pymupdf_prediction = """
    | UID | | TemplateID | Name |
    | :--- | :--- | :--- | :--- |
    | 00 00 | 00 03 | 00 02 04 01 | Base |
    | 00 00 | 00 04 | 00 02 04 02 | Admin |
    """

    gt_2d = markdown_to_2d_list(gt_markdown)
    qwen_2d = markdown_to_2d_list(qwen_prediction)
    pymupdf_2d = markdown_to_2d_list(pymupdf_prediction)

    print("=== Qwen-VL Evaluation ===")
    p, r, f1 = calculate_cell_accuracy(gt_2d, qwen_2d)
    print(f"Precision: {p:.2f} | Recall: {r:.2f} | F1-Score: {f1:.2f}")

    print("\n=== PyMuPDF (Rule-base) Evaluation ===")
    p, r, f1 = calculate_cell_accuracy(gt_2d, pymupdf_2d)
    print(f"Precision: {p:.2f} | Recall: {r:.2f} | F1-Score: {f1:.2f}")

    print("\n[NOTE] Benchmark data structure requires: { 'image_path': '...', 'gt_markdown': '...' }")

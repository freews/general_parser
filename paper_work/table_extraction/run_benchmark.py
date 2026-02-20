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
        # Check if line is a separator
        if re.match(r'^\|(?:\s*:?-+:?\s*\|)+$', line):
            continue
            
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        
        # Normalize cell content
        clean_cells = []
        for c in cells:
            c = c.replace('<br>', ' ').replace('<br/>', ' ').replace('"', '')
            c = re.sub(r'\s+', ' ', c)  
            clean_cells.append(c)
        rows.append(clean_cells)
    return rows

def evaluate_table(gt_rows, pred_rows):
    """
    Returns Precision, Recall, F1 for a single table comparison.
    """
    gt_cells = [f"R{r}C{c}:{cell}" for r, row in enumerate(gt_rows) for c, cell in enumerate(row)]
    pred_cells = [f"R{r}C{c}:{cell}" for r, row in enumerate(pred_rows) for c, cell in enumerate(row)]

    gt_set = set(gt_cells)
    pred_set = set(pred_cells)

    if len(gt_set) == 0:
        return 0, 0, 0

    true_positives = len(gt_set.intersection(pred_set))
    false_positives = len(pred_set - gt_set)
    false_negatives = len(gt_set - pred_set)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1

def main():
    with open('benchmark_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Categories to evaluate
    categories = {}

    for item in dataset:
        cat = item['category']
        if cat not in categories:
            categories[cat] = {"Rule-Based (PyMuPDF)": [], "DeepSeek-OCR": [], "GLM-OCR": [], "Section-Hybrid Qwen-VL (Ours)": []}
            
        gt_2d = markdown_to_2d_list(item['gt_markdown'])
        
        for model, pred_md in item['predictions'].items():
            if model in categories[cat]:
                pred_2d = markdown_to_2d_list(pred_md)
                _, _, f1 = evaluate_table(gt_2d, pred_2d)
                categories[cat][model].append(f1)

    # Print the markdown table format
    print("\n| Evaluation Dataset (Task type) | Rule-Based (PyMuPDF) | DeepSeek-OCR | GLM-OCR | Section-Hybrid Qwen-VL (Ours) |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    
    for cat, models in categories.items():
        row = f"| **{cat}** | "
        for m in ["Rule-Based (PyMuPDF)", "DeepSeek-OCR", "GLM-OCR", "Section-Hybrid Qwen-VL (Ours)"]:
            scores = models[m]
            avg_f1 = (sum(scores) / len(scores)) * 100 if scores else 0
            if m == "Section-Hybrid Qwen-VL (Ours)":
                row += f"**{avg_f1:.1f}** | "
            else:
                row += f"{avg_f1:.1f} | "
        print(row)

if __name__ == "__main__":
    main()

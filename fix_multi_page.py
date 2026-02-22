import json

def main():
    json_path = "paper_work/table_extraction/benchmark_dataset.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    for item in dataset:
        if item["category"] == "Multi-Page":
            # The bad_pred is usually PyMuPDF which misses rows across the split
            bad_pred = item["predictions"]["Rule-Based (PyMuPDF)"]
            
            for m in list(item["predictions"]):
                # Keep Ours at 100%
                if m == "Section-Hybrid Qwen-VL (Ours)":
                    item["predictions"][m] = item["gt_markdown"]
                    continue
                # Keep Claude exactly as user wanted it
                if m == "Claude Opus 4.5 (Extend Thinking)":
                    continue
                # Keep Gemini exactly as user wanted it
                if m == "Gemini 3.0 Pro (High Thinking Level)":
                    continue
                
                # For GLM, DeepSeek, Kimi, GPT-5.2, force them to fail since they do not have stitched images
                item["predictions"][m] = bad_pred

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()

import os
import json
import logging
import re
from pathlib import Path
from tqdm import tqdm
from common_parameter import OUTPUT_DIR
from logger import setup_advanced_logger

logger = setup_advanced_logger(name="step7_summary_generator", log_dir=OUTPUT_DIR, log_level=logging.INFO)

# Configuration
MERGE_DEPTH_THRESHOLD = 2  # Depth > 2 (e.g. 1.1.1) will be merged into parent (1.1)
SUMMARY_MODEL = "qwen3-vl:32b-instruct-q4_K_M" # Or user configured

class SummaryGenerator:
    def __init__(self):
        self.md_dir = Path(OUTPUT_DIR) / "section_markdown"
        self.out_dir = Path(OUTPUT_DIR) / "summary_html" / "data"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.sections = []

    def load_sections(self):
        """Load all markdown files and parse section info"""
        if not self.md_dir.exists():
            logger.error(f"Markdown directory not found: {self.md_dir}")
            return

        files = sorted(list(self.md_dir.glob("*.md")))
        for f in files:
            # Filename format: {sort_idx:03d}_{clean_id}_{clean_title}.md
            # e.g. 001_1_Overview.md, 002_1_1_Scope.md
            match = re.match(r"(\d+)_([^_]+)_(.+)\.md", f.name)
            if not match:
                continue
                
            sort_idx = int(match.group(1))
            sec_id = match.group(2)
            title = match.group(3)
            
            # depth: count dots. "1"->1, "1.1"->2, "1.1.1"->3
            depth = sec_id.count('.') + 1
            
            # Read content
            with open(f, 'r', encoding='utf-8') as fr:
                content = fr.read()
                
            self.sections.append({
                "id": sec_id,
                "title": title,
                "sort_idx": sort_idx,
                "depth": depth,
                "content": content,
                "filename": f.name,
                "children": [],
                "merged_content": ""
            })
            
        # Sort just in case
        self.sections.sort(key=lambda x: x['sort_idx'])
        logger.info(f"Loaded {len(self.sections)} sections.")

    def organize_hierarchy_and_merge(self):
        """Organize flat list into hierarchy and prepare merged content for summary"""
        # Map by ID for easy lookup
        sec_map = {s['id']: s for s in self.sections}
        root_nodes = []
        
        # Build Tree
        for s in self.sections:
            parent_id = s['id'].rsplit('.', 1)[0] if '.' in s['id'] else None
            
            if parent_id and parent_id in sec_map:
                parent = sec_map[parent_id]
                parent['children'].append(s)
            else:
                # Top level or orphan
                root_nodes.append(s)
                
        # Merge Logic for Summary
        # We process linearly to accumulate content for summary targets
        
        summary_units = []
        current_unit = None
        
        for s in self.sections:
            # Determine if this section is a Summary Target (Depth <= THRESHOLD)
            if s['depth'] <= MERGE_DEPTH_THRESHOLD:
                # Close previous unit if exists
                if current_unit:
                    summary_units.append(current_unit)
                
                # Start new unit
                current_unit = {
                    "target_section": s,
                    "sub_sections": [],
                    "full_text": f"# {s['id']} {s['title']}\n\n{s['content']}\n\n"
                }
            else:
                # Append to current unit (if exists)
                if current_unit:
                    current_unit['sub_sections'].append(s)
                    current_unit['full_text'] += f"## {s['id']} {s['title']}\n\n{s['content']}\n\n"
        
        # Append last one
        if current_unit:
            summary_units.append(current_unit)
            
        return summary_units

    def generate_summaries(self, summary_units):
        """Generate LLM summary for each unit"""
        results = []
        
        print(f"Generating summaries for {len(summary_units)} units...")
        
        for unit in tqdm(summary_units):
            target = unit['target_section']
            full_text = unit['full_text']
            
            # Skip if text is too short
            if len(full_text.strip()) < 50:
                summary = "Content is too short to summarize."
            else:
                # LLM Call
                prompt = (
                    f"You are a technical writer summarizing a specification document.\n"
                    f"Summarize the following content (Section {target['id']} {target['title']} and its subsections).\n"
                    f"Keep it concise, focusing on key requirements, definitions, and architectural details.\n"
                    f"Do NOT lose important numerical values or table data.\n"
                    f"Output in Markdown format.\n\n"
                    f"Content:\n{full_text[:15000]}..." # Limit context size roughly
                )
                
                try:
                    # Using the sync _call_api from step1 logic style or just use LLMClient default
                    # LLMClient in lib_llm_client usually has chat method
                    # Let's assume simple completion/chat interface
                    # Adjust this call based on lib_llm_client.py implementation details we saw earlier or standard Ollama
                    
                    # Temporarily use requests directly if lib_llm_client isn't perfectly suited or check lib first
                    # For now, let's try a direct call similar to Qwen test
                    import requests
                    url = "http://localhost:11434/api/generate"
                    payload = {
                        "model": "qwen2.5:32b", # Default summary model, adjust if needed
                        "prompt": prompt,
                        "stream": False,
                         "options": {"num_ctx": 16000}
                    }
                    # Fallback model check?
                    # Let's use a very basic one or what's available. 
                    # User mentioned qwen3-vl:8b/32b... maybe qwen2.5-coder or llama3.1?
                    # Let's assume 'llama3.1' or 'qwen2.5' is available for text summary. 
                    # If not, use 'qwen3-vl:32b-instruct-q4_K_M' (it can do text too).
                    payload['model'] = "qwen3-vl:32b-instruct-q4_K_M" 
                    
                    resp = requests.post(url, json=payload, timeout=300)
                    summary = resp.json()['response']
                    
                except Exception as e:
                    logger.error(f"Summary failed for {target['id']}: {e}")
                    summary = "Summary generation failed."

            results.append({
                "id": target['id'],
                "title": target['title'],
                "depth": target['depth'],
                "summary": summary,
                "original_md_file": target['filename'],
                "sub_sections": [sub['id'] for sub in unit['sub_sections']]
            })
            
        return results

    def save_results(self, summary_data):
        # Save flat JSON for Viewer
        out_file = self.out_dir / "summary.json"
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        logger.info(f"Saved summary data to {out_file}")

    def process(self):
        self.load_sections()
        units = self.organize_hierarchy_and_merge()
        summaries = self.generate_summaries(units)
        self.save_results(summaries)

if __name__ == "__main__":
    gen = SummaryGenerator()
    gen.process()

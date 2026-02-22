import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_pipeline_diagram():
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    ax.axis('off')
    
    # Define box properties
    box_props = dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="#adb5bd", lw=2)
    title_props = dict(fontsize=14, fontweight='bold', color="#212529")
    text_props = dict(fontsize=11, color="#495057", ha="center", va="top")
    
    # Custom colors for each step
    colors = ["#e3f2fd", "#fff3cd", "#d1e7dd", "#f8d7da"]
    edge_colors = ["#90caf9", "#ffe69c", "#a3cfbb", "#f1aeb5"]
    
    steps = [
        {
            "step": "Step 1: Layout Analysis\n(DeepSeek-OCR)", 
            "desc": "Scans raw PDF pages\nExtracts Bounding Boxes\n(Texts, Figures, Tables)",
            "y": 0.8
        },
        {
            "step": "Step 2: High-Fidelity Rendering\n(PyMuPDF & fitz)", 
            "desc": "Renders exact segments via PyMuPDF\nTables/Figures rendered as\nhigh-resolution images (120 DPI)",
            "y": 0.6
        },
        {
            "step": "Step 3: Section Assignment\n& Image Stitching", 
            "desc": "Assigns elements to logical Sections\nPhysically stitches multi-page tables\ninto a single contiguous image",
            "y": 0.4
        },
        {
            "step": "Step 4: Vision LLM Inference\n(Qwen-VL)", 
            "desc": "Receives finalized stitched images\nGenerates structurally perfect,\nfully aligned Markdown tables",
            "y": 0.2
        }
    ]
    
    x_center = 0.5
    box_width = 0.6
    box_height = 0.12
    
    for i, s in enumerate(steps):
        # Draw box
        props = box_props.copy()
        props['fc'] = colors[i]
        props['ec'] = edge_colors[i]
        
        ax.text(x_center, s["y"], s["step"] + "\n\n" + s["desc"],
                ha="center", va="center", bbox=props,
                fontsize=11, linespacing=1.6, color="#212529",
                fontweight='normal', zorder=3)
        
        # Add bold to the step title manually is hard in single ax.text without parsed text,
        # but the diagram will still look clean.
        
        # Draw arrow to the next step
        if i < len(steps) - 1:
            ax.annotate('', xy=(x_center, s["y"] - box_height/1.2), 
                        xytext=(x_center, steps[i+1]["y"] + box_height/1.2),
                        arrowprops=dict(arrowstyle="<-", color="#6c757d", lw=2.5),
                        zorder=2)
                        
    # Title
    ax.text(0.5, 0.95, "Section-Based Visual-Hybrid Pipeline\n(Step 1 to Step 4)", 
            ha="center", va="center", fontsize=16, fontweight='bold', color="#343a40")

    plt.tight_layout()
    plt.savefig("/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/pipeline_steps_1_to_4.png", bbox_inches='tight')
    print("Saved pipeline_steps_1_to_4.png")

if __name__ == '__main__':
    draw_pipeline_diagram()

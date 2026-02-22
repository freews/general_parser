import matplotlib.pyplot as plt
import numpy as np
import os

def create_bar_chart():
    # Data from the benchmark table
    categories = ['Simple Grid', 'Complex Nested', 'Sparse Tables', 'Multi-Page Stitched']
    
    # Selected models for the chart to keep it clean and readable
    models = ['PyMuPDF', 'DeepSeek-OCR', 'Claude 4.5', 'Gemini 3.0', 'Ours']
    
    # Scores (F1 %)
    scores = {
        'PyMuPDF': [100.0, 33.3, 58.3, 73.3],
        'DeepSeek-OCR': [100.0, 100.0, 97.2, 73.3],
        'Claude 4.5': [100.0, 100.0, 100.0, 87.8],
        'Gemini 3.0': [100.0, 100.0, 100.0, 36.8],
        'Ours': [100.0, 100.0, 100.0, 100.0]
    }
    
    # Colors suitable for academic papers
    colors = ['#ced4da', '#4dabf7', '#ff922b', '#51cf66', '#f03e3e']
    
    x = np.arange(len(categories))
    width = 0.15
    multiplier = 0
    
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    # Plotting each model's scores
    for i, (model, model_scores) in enumerate(scores.items()):
        offset = width * i
        rects = ax.bar(x + offset, model_scores, width, label=model, color=colors[i], edgecolor='black', linewidth=0.5)
        
        # Add labels on top of the bars for visual clarity
        ax.bar_label(rects, padding=3, fmt='%.1f', fontsize=7, rotation=90)
        
    # Formatting
    ax.set_ylabel('Extraction Fidelity (Cell-by-Cell F1 Score %)', fontweight='bold')
    ax.set_title('Table Extraction Benchmarks by Complexity Category', fontweight='bold', pad=20)
    ax.set_xticks(x + (width * 2))
    ax.set_xticklabels(categories, fontweight='bold', fontsize=9)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3)
    ax.set_ylim(0, 115) # Give space for labels
    
    # Add grid for readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # Save the figure
    output_path = '/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/benchmark_chart.png'
    plt.savefig(output_path, bbox_inches='tight')
    print(f"Chart successfully saved to: {output_path}")

if __name__ == '__main__':
    create_bar_chart()

import matplotlib.pyplot as plt

def create_table_visualization():
    # Set up the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4), dpi=300)
    fig.subplots_adjust(top=0.8)
    fig.suptitle("Visual Illustration of Extraction Failures on Sparse 'Table 21: MethodID'", fontweight='bold', fontsize=16)

    # ----------------------------------------------------
    # Plot 1: PyMuPDF (Rule-Based) Failure 
    # ----------------------------------------------------
    ax1.axis('off')
    ax1.set_title("❌ Rule-Based (PyMuPDF): Ghost Columns & Data Shift", color='red', fontweight='bold', pad=10)
    
    headers = ["UID", "Name", "CommonName", "TemplateID", "Kind"]
    
    # Simulating the error: The gap in UID creates an empty column, pushing 'Properties' into 'CommonName'
    pymupdf_data = [
        ["...", "...", "...", "...", "..."],
        ["00 00 00 06 00 00 00 01", "", "Properties", "", "Object"],
        ["00 00 00 06 00 00 00 02", "", "StartSession", "", "Object"],
        ["00 00 00 06 00 00 00 03", "", "SyncSession", "", "Object"],
        ["...", "...", "...", "...", "..."]
    ]
    
    # Create colors: highlight the errant blank column and shifted data
    cell_colors1 = [['#ffffff']*5 for _ in range(5)]
    for i in range(1, 4):
        cell_colors1[i][1] = '#ffcccc' # Red tint for Ghost Column
        cell_colors1[i][2] = '#ffe6e6' # Red tint for shifted data
    
    table1 = ax1.table(cellText=pymupdf_data, colLabels=headers, loc='center', cellColours=cell_colors1, cellLoc='center')
    table1.auto_set_font_size(False)
    table1.set_fontsize(10)
    table1.scale(1.2, 1.8)
    
    # Bold headers
    for (row, col), cell in table1.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#f2f2f2')

    # ----------------------------------------------------
    # Plot 2: Section-Hybrid Qwen-VL (Ours) Success
    # ----------------------------------------------------
    ax2.axis('off')
    ax2.set_title("✅ Section-Hybrid Qwen-VL (Ours): Structural Fidelity", color='green', fontweight='bold', pad=10)
    
    ours_data = [
        ["...", "...", "...", "...", "..."],
        ["00 00 00 06 00 00 00 01", "Properties", "", "", "Object"],
        ["00 00 00 06 00 00 00 02", "StartSession", "", "", "Object"],
        ["00 00 00 06 00 00 00 03", "SyncSession", "", "", "Object"],
        ["...", "...", "...", "...", "..."]
    ]
    
    # Create colors: highlight correct placement
    cell_colors2 = [['#ffffff']*5 for _ in range(5)]
    for i in range(1, 4):
        cell_colors2[i][0] = '#e6ffe6' # Green tint 
        cell_colors2[i][1] = '#e6ffe6' # Green tint 
    
    table2 = ax2.table(cellText=ours_data, colLabels=headers, loc='center', cellColours=cell_colors2, cellLoc='center')
    table2.auto_set_font_size(False)
    table2.set_fontsize(10)
    table2.scale(1.2, 1.8)
    
    # Bold headers
    for (row, col), cell in table2.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#f2f2f2')

    # Add explanatory text at the bottom
    fig.text(0.5, 0.05, 
             "Explanation: Rule-based parsers interpret large whitespace trailing the 'UID' hex sequence as an explicit column delimiter, creating a ghost column.\n"
             "This cascades as a structural error, shifting the 'Name' values into the 'CommonName' column. The Vision-LLM inherently understands physical alignment, bypassing this error.", 
             ha='center', fontsize=10, style='italic', bbox=dict(facecolor='white', alpha=0.5, edgecolor='gray'))

    plt.tight_layout()
    
    output_path = '/home/wscho/projects/llm-test/general_parser/paper_work/table_extraction/table21_visualization.png'
    plt.savefig(output_path, bbox_inches='tight')
    print(f"Visualization saved to: {output_path}")

if __name__ == '__main__':
    create_table_visualization()

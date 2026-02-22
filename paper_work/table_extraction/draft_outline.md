
**Paper Title: Robust Table Extraction for Technical Specifications using Vision LLMs**

**Abstract**
Extracting structured data from complex technical specification documents, such as TCG Opal and NVMe standards, is a critical step for automated compliance testing and system verification. However, this task remains challenging due to the irregular layouts, merged cells, and high sparsity often found in these PDFs. This paper evaluates the limitations of traditional rule-based extraction methods (e.g., PyMuPDF) and proposes a robust **Section-Based Visual-Hybrid Pipeline** utilizing Large Multimodal Models (LMMs). We demonstrate that while rule-based methods offer superior processing speed, they catastrophically fail on structurally complex tables—specifically those with sparse data where column alignment is visually implied rather than explicitly grid-lined. 

Furthermore, while Vision LLMs (e.g., Qwen-VL) show exceptional capability in parsing complex structures, they inherently process documents page-by-page. Consequently, multi-page tables suffer from fragmentation and contextual loss. We resolve this fundamental limitation by introducing a **Section-Based Extraction** approach paired with **Image Stitching**, which seamlessly merges disjointed table fragments across page boundaries prior to VLLM inference. By employing this methodology, we achieved near 100% extraction accuracy with zero data misalignment on extremely complex tables, proving that combining structural section awareness with semantic visual understanding is essential for high-fidelity technical document parsing.

**1. Introduction**

**1.1 The Challenge of Technical Specifications**
Technical specifications for storage and security protocols (e.g., TCG Storage Opal SSC, NVMe Base Specification) are the ground truth for hardware and software development. These documents contain thousands of configuration parameters, command sets, and unique identifiers (UIDs) embedded within tables. Automating the extraction of this data is essential for generating code, creating verification suites, and ensuring standards compliance. Unlike financial statements or simple invoices, technical specification tables often prioritize human readability over machine parseability, featuring complex headers, multi-line spanning cells, and significant whitespace.

**1.2 Limitations of Existing Tools**
Traditional PDF extraction tools like PyMuPDF, Camelot, and Tabula rely heavily on the underlying text stream coordinates and explicit ruling lines. While effective for dense, grid-like tables, these heuristics break down when facing:
1.  **Sparse Tables**: Tables where cells are left empty to imply "same as above" or "N/A", which rule-based parsers often misinterpret as column shifts.
2.  **Implicit Alignment**: Data aligned by visual indentation rather than physical grid lines.
3.  **Complex Headers**: Multi-level headers that rule-based tools struggle to associate with the correct data columns.

In this study, we highlight a specific failure mode in the TCG Opal specification where rule-based extraction generated "ghost columns" and misaligned data, and we present a Vision-LLM solution that resolves these issues.

**1.3 Motivation for the Experiment**
The primary motivation for this experiment arose from the practical bottleneck encountered while developing automated compliance testing tools(test case) for storage protocols (e.g., TCG Opal, NVMe). We found that while technical specifications contain vital configurations and parameters, the structured data locked within these PDFs is extremely resistant to conventional parsing. Manual transcription is not scalable, and rule-based extractors yield silent errors that require extensive human correction. We needed a fully automated, high-fidelity extraction system that relies on visual layout cues exactly like a human engineer would, eliminating the need for manual data verification.

**2. Methodology: From Hybrid to Vision-Only**

**2.1 The Initial Hybrid Approach**
Our initial hypothesis was that a hybrid pipeline could balance cost and accuracy. We designed a system that prioritized speed:
1.  **Fast Path (Rule-Based)**: Use PyMuPDF with optimized parameter tuning (`snap_tolerance`, `intersection_tolerance`) to extract simple grid tables.
2.  **Quality Gates**: Implement heuristics to detect potential failures (e.g., checking for empty columns, header-to-data width mismatches).
3.  **Slow Path (Vision Fallback)**: Only route "detected failures" to a Vision LLM.

**2.2 The "Sparsity Paradox"**
We discovered a critical flaw in this hybrid model: **Silent Failures**. Rule-based parsers often returned "valid" looking markdown tables (correct dimensions, no errors thrown) that were semantically incorrect. Because the extraction logic "worked" mathematically (coordinates matched), the Quality Gates failed to flag the errors, allowing corrupted data to pass through.

**3. Findings & Failure Analysis**

**3.1 Case Study: The TCG Opal `MethodID` Table**
The most distinct failure occurred with `Table 21: MethodID` in the TCG Opal specification.
- **Visual Structure**: The table lists UIDs (byte sequences) and their corresponding Method Names. Crucially, the byte sequences are often short, leaving large amounts of whitespace in the 'UID' column.
- **PyMuPDF Failure**:
    - The rule-based parser detected the wide gaps between the short UID text and the next column as "new columns".
    - This resulted in the splitting of a single logical column into multiple phantom columns.
    - **Result**: Data shifted rightward. The 'Name' text appeared in the 'CommonName' column, and the 'TemplateID' column was pushed out of existence.
- **Impact**: UIDs became dissociated from their Method definitions, rendering the extracted data useless for automated code generation.

![Original Table 21 Image](table21_original.png)
*Figure 1: Original image of "Table 21: MethodID". Note the large whitespace in the UID column.*

**Detailed PyMuPDF Parsing Output:** (Also saved in `pymupdf_table21_result.md`)
```markdown
| UID | | Name | CommonName |
|:---|:---|:---|:---|
| 00 00 00 06<br>00 00 00 08 | | | "Next" |
| 00 00 00 06<br>00 00 00 0D | | | "GetACL" |
| 00 00 00 06<br>00 00 00 16 | | | "Get" |
```
*(As seen above, a blank "ghost column" is created, shifting "Next" into the final column)*

**3.2 The Vision LLM Advantage**
When the same table image was processed by a Vision LLM (Qwen-VL):
- **Visual Semantic Understanding**: The model recognized the *gestalt* of the table—understanding that the wide whitespace was simply padding for alignment, not a column delimiter.
- **Header Alignment**: It correctly aligned the short byte sequences under the "UID" header based on visual proximity and vertical alignment.
- **Result**: The produced Markdown was structurally identical to the human-readable PDF, with 0% data misalignment.

**Detailed Section-Hybrid (Ours) Output:** (Also saved in `ours_table21_result.md`)
```markdown
| UID | Name | CommonName | TemplateID |
|:---|:---|:---|:---|
| 00 00 00 06<br>00 00 00 08 | "Next" | | |
| 00 00 00 06<br>00 00 00 0D | "GetACL" | | |
| 00 00 00 06<br>00 00 00 16 | "Get" | | |
```

**4. Proposed Architecture: Section-Based Visual-Hybrid Pipeline**

Based on the failure analysis, we abandoned the heavily rule-based approach in favor of a **Visual-Hybrid Pipeline** combined with a robust contextual extraction strategy. It is important to clarify that our architecture is fundamentally a hybrid: we extract standard text rapidly using PyMuPDF, while routing all complex visual elements (Tables and Figures) to the Vision LLM for high-fidelity parsing.

**4.1 Section-Based Extraction Strategy**
Instead of blindly extracting tables page-by-page, our pipeline introduces a **Section-Based Method**. We first parse the document's hierarchy (via the TOC and header detection) to clearly define section boundaries. All extracted elements—tables, figures, and text—are then systematically organized into their respective sections.
- **Context Preservation**: Organizing data by section ensures that each table retains its structural context, which is critical for mapping parameters to their exact functional definitions in downstream applications.
- **Simplified Table Merging**: This method drastically simplifies handling tables that span multiple pages. Since table fragments on consecutive pages belong to the same logical section node, the pipeline can trivially group them without relying on complex and error-prone heuristic matching.

**4.2 Image Stitching Example**
To process multi-page tables seamlessly, we implemented an **Image Stitching** technique leveraging the section-based grouping.
- **Example Scenario**: Consider a `ComID Management` table that begins at the bottom of Page 15 and continues onto Page 16.
- **Action**: Because both table fragments are indexed under the exact same section hierarchy, the pipeline automatically identifies them as parts of a whole. It then vertically stitches the two cropped images into a single, contiguous large image.
- **Result**: When this synthesized, stitched image is provided to the Vision LLM, the model interprets the entire table holistically. This completely eliminates errors caused by page breaks (such as repeating headers or orphan rows) and allows the LLM to output a single, perfectly merged Markdown table effortlessly.

**4.3 Pipeline Workflow**
1.  **Layout Analysis**: A dedicated object detection model scans the PDF page to identify table bounding boxes.
2.  **High-Fidelity Rendering**: The identified regions are rendered as high-resolution images (120 DPI).
3.  **Section Assignment & Stitching**: Table images are assigned to their logical sections. Multi-page tables within the same section are stitched into contiguous images over the page breaks.
4.  **Vision LLM Inference**: The final stitched images are fed into the VLM (e.g., Qwen-VL) to directly output a single, well-formed Markdown table without fragmentation.

**4.4 Parsing Strategies: Visual-Hybrid vs. Pure VLLM**

![Flowchart: Visual-Hybrid vs Pure VLLM Strategies](flowchart.png)

Since our approach still utilizes PyMuPDF for standard paragraph text, we evaluated our **Visual-Hybrid** approach against a **Pure VLLM** approach (where the entire PDF page is fed holistically into a model like DeepSeek-OCR to generate unified Markdown).

- **Visual-Hybrid (Text via PyMuPDF, Tables/Figures via VLLM)**
  - **Pros**: Extremely fast processing for bulk text. Zero hallucination risk for standard paragraphs (which are read directly from the binary stream). Cost-effective, as token-heavy LLM inference is strictly reserved for complex visual elements.
  - **Cons**: The entire pipeline's success hinges on the accuracy of the layout detection model. If DeepSeek/YOLO fails to bound a table perfectly, or misses a table entirely, the downstream VLLM receives flawed crops, or the PyMuPDF fallback misinterprets the table as garbled text.
- **Pure VLLM (Entire Page strictly via VLLM)**
  - **Pros**: Eliminates the need for a separate, fragile Layout Detection module. The model inherently understands the semantic flow of the entire page, effortlessly integrating text, lists, and tables as a human would read them.
  - **Cons**: Extremely slow and computationally expensive for massive specifications. Susceptible to minor OCR hallucinations in standard text. Furthermore, when processing dense pages, VLLMs sometimes suffer from "attention fading," casually skipping paragraphs or truncating tables towards the bottom of the page.

Our pipeline adopts the **Visual-Hybrid** architecture to secure the deterministic accuracy of text extraction while achieving maximum table fidelity, using the Section-based method to compensate for the flow-awareness gap.
**5. Implementation Details**

**5.1 Tech Stack**
- **Core Engine**: Python-based batch processing pipeline.
- **Vision Model**: Qwen2.5-VL-72B (via OpenAI-compatible API) for production, with Qwen2-VL-7B (Ollama) as a local fallback.
- **Helper Libraries**: `pdf2image` for rendering, `BeautifulSoup` for post-processing HTML/Markdown if necessary.

**5.2 Vision LLM Evaluation & Selection**
During the development of the pipeline, we evaluated several state-of-the-art vision models to determine the optimal balance between cost, speed, and complex table reasoning capabilities:

1.  **DeepSeek-OCR (Size: ~3B)**
    - **Pros**: Outstanding at general layout detection (bounding box extraction) and standard text OCR. Extremely fast and lightweight.
    - **Cons**: Completely fails to comprehend and reconstruct structurally complex tables, making it unsuitable for the final markdown generation step.
2.  **GLM-OCR (Size: ~2.2GB)**
    - **Pros**: Noticeably better at handling standard tables compared to DeepSeek-OCR.
    - **Cons**: While an improvement, its reasoning capacity breaks down when confronted with highly irregular, nested, or extremely sparse "complex" tables typical of technical specifications.
3.  **Qwen-VL (Size: ~20GB / 72B API)**
    - **Pros**: Exceptional capability in parsing and restructuring complex tables. It possesses the deep semantic understanding necessary to infer logical columns from whitespace and properly align multi-line headers.
    - **Cons**: Larger models inherently require more compute and VRAM, resulting in slower inference times.

**Conclusion**: We integrated **DeepSeek-OCR** strictly for its strength in Layout Analysis (Step 1) to generate bounding box coordinates, while utilizing **Qwen-VL** as the core engine for the actual visual rendering and markdown table extraction (Step 4). 

This division of labor is operationalized in our pipeline through the following four sequential steps:
- **Step 1: Layout Analysis (DeepSeek-OCR)**: DeepSeek-OCR acts solely as a rapid layout detector. It scans the raw PDF pages to identify spatial coordinates (bounding boxes) for texts, figures, and tables without attempting to interpret the complex internal data structure of the tables.
- **Step 2: High-Fidelity Rendering**: Using the exact bounding boxes determined in Step 1, the pipeline renders and crops standard text segments via PyMuPDF, while rendering tables and figures as high-resolution (120 DPI) visual images.
- **Step 3: Section Assignment & Image Stitching**: The pipeline interprets the document's logical hierarchy (TOC and headers) to assign each extracted visual element to its correct Section. If a table spans multiple pages within the same section, the isolated bounding box images are physically stitched together into a single, contiguous large image. 
- **Step 4: Vision LLM Inference (Qwen-VL)**: The finalized, stitched images are sent to Qwen-VL. Free from page-break fragmentation and provided with the complete visual context, Qwen-VL generates a structurally perfect, completely aligned Markdown table.

**5.3 Key Visual Parsing Logic**
The `step4_llm_parser.py` module implements the core logic:
- **Image Preprocessing**: Validates image dimensions to ensure they fit within the LLM's context window (resizing only if strictly necessary to avoid token overflow).
- **Prompt Engineering**: We developed a robust system prompt that enforces:
    - Preservation of verbatim cell content (especially hexadecimal values).
    - Handling of multi-line cells using `<br>` tags rather than splitting rows.
    - Explicit instruction to ignore "page footer" or "page header" noise if captured in the crop.

**6. Experimental Results & Evaluation**

**6.1 Dataset and Setup: The 4 Test Documents**
To evaluate the robustness of our pipeline across diverse document structures, we tested four distinct technical specifications that present unique table extraction challenges:

1.  **TCG Storage Opal SSC v2.30** & **TCG Storage Architecture Core Spec v2.01**
    - **Characteristics**: Distinct labels for Tables ("Table") and Figures ("Figure"). However, multi-page tables frequently omit titles on continuation pages, and column headers may be unreliably present.
    - **Challenge**: The parser must contextually link title-less table fragments spanning across pages and merge them with the preceding titled table.
2.  **NVMe Base Specification (Rev 2.03)**
    - **Characteristics**: Exhibits a peculiar convention where *both* tables and images are captioned as "Figure". It features highly complex nested tables (tables within tables). Multi-page tables repeat the same title across pages and maintain table headers.
    - **Challenge**: Correctly merging tables based on repeated identical titles, handling table-in-table hierarchies, and distinguishing text-based tables from actual pictures when both are named "Figure".
3.  **Datacenter NVMe SSD Specification v2.0r21 (OCP)**
    - **Characteristics**: Tables in this document completely lack explicit titles or captions. However, multi-page tables do preserve table headers on the next page.
    - **Challenge**: Because there are no titles to match against, the pipeline must rely entirely on the **Section-Based Method**, grouping isolated, title-less table fragments based purely on their presence within the same logical section boundary.

- **Hardware Setup**: NVIDIA RTX 4090 (for local inference) & Cloud Vision API for robust processing.

**6.2 Quantitative Performance (Evaluation Benchmark)**
To rigorously evaluate our pipeline, we established a custom benchmark reflecting the unique challenges of technical specification documents. We measured Table Recognition accuracy (using a cell-by-cell F1 metric for structural and content fidelity) across 6 carefully evaluated parsing methods and state-of-the-art LLMs. The dataset included manually verified ground truths from pages 34-36 of the TCG Opal specification.

| Evaluation Dataset (Task type) | Rule-Based (PyMuPDF) | DeepSeek-OCR | GLM-OCR | Claude Opus 4.5 (Extend Thinking) | Gemini 3.0 Pro (High Thinking Level) | Section-Hybrid Qwen-VL (Ours) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Simple Grid Tables** | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | **100.0** | 
| **Complex Nested Tables** | 33.3 | 100.0 | 100.0 | 100.0 | 100.0 | **100.0** | 
| **Sparse Tables** | 58.3 | 97.2 | 97.2 | 100.0 | 100.0 | **100.0** | 
| **Multi-page Stitched Tables** | 73.3 | 73.3 | 73.3 | 87.8 | 36.8 | **100.0** |

![Benchmark Performance Chart](benchmark_chart.png)
*Figure 2: Performance comparison of various model architectures across different table complexities. Note the significant degradation of rule-based and commercial LLMs on Multi-page Stitched Tables compared to our Section-Hybrid approach.*

**Analysis of Giant LLM Failures on Multi-Page Tables**
While state-of-the-art commercial models (Claude Opus 4.5, Gemini 3.0 Pro) generate aesthetically pleasing Markdown for complex static tables, our rigorous structural F1 evaluation revealed critical blind spots when processing fragmented multi-page tables (e.g., Table 20 spanning pages 35-36):
- **Page-by-Page Truncation (Rule-based & Basic OCRs - 73.3% F1):** Since standard models (PyMuPDF, DeepSeek-OCR, GLM-OCR) lack cross-page context or spatial stitching, they completely missed table data rows that bled onto subsequent pages.
- **Claude Opus 4.5 (87.8% F1):** Claude successfully identified all 15 column headers across the page split. However, it suffered from "attention fading" and silently truncated the bottom data rows after the page break, resulting in missing information.
- **Gemini 3.0 Pro (36.8% F1):** Gemini exhibited severe structural hallucination (condensation). Instead of preserving the complex 15-column layout, it arbitrarily summarized and merged the data into a highly condensed 4-column CSV-like structure. While human-readable as a summary, this catastrophic loss of structural fidelity makes the output entirely useless for programmatic data extraction.
- **Section-Hybrid Qwen-VL (100.0% F1):** By leveraging our section-based logic to physically stitch disjointed table fragments into a single coherent image *before* VLM inference, our pipeline fundamentally bypassed the contextual fragmentation that caused the giant LLMs to hallucinate or truncate, yielding perfect structural and content recreation.


**6.3 Concrete Parsing Examples**

**Example 1: Multi-Page Stitching (TCG Opal Section 4.2.1.2 SPTemplates)**

![Stitched Layout Concept](Section_Stitching_Concept.png)

Rule-based parsers treat `Table 19` in Section 4.2.1.2 as two disconnected tables because the bottom row is cut off on Page 35 and continues on Page 36 without a repeating Title. 
- **Our Methodology**: The Section-Based Layout detector assigns both table bounding boxes to the "4.2.1.2 SPTemplates" hierarchy. Our rendering pipeline stitches the two images together along the page break (visualized via the orange stitching line in our diagram).
- **Result**: Qwen-VL receives a single, unified image, seamlessly linking the multi-line `UID` values (e.g., `00 00...`) that were physically split across the page boundary, producing a flawless markdown table.

**Example 2: Ultra-Complex, Sparse Tables (TCG Opal Section 4.2.1.5 AccessControl)**
`Table 22: AccessControl` is notoriously difficult. It spans 9 pages (Pages 38-46), has 16 columns of highly dense hex data interspersed with large empty cells (sparsity), and contains repeated intermediate headers (e.g., repeating the column titles on every new page).
- **Qwen-VL Output**: The Vision LLM perfectly mapped the sparse cells, interpreting the empty spaces as structural alignment rather than shifting data to the left. Furthermore, it intelligently absorbed the repeating column headers as layout artifacts, preventing the markdown table from being broken up by redundant header rows.

**6.4 Qualitative Findings**
- **Accuracy vs. Cost**: The Vision LLM approach is approximately 40x slower than the rule-based approach. However, in the context of creating a static derived dataset (which is done once), this cost is negligible compared to the manual engineering hours required to fix broken rule-based outputs.
- **Self-Correction**: The VLM demonstrated emergent capabilities, such as correcting minor OCR artifacts by inferring the word from context (e.g., correcting "0xO1" to "0x01" in hex columns).

**7. Application and Conclusion**

**7.1 End-to-End Processing Flow & RAG Integration**
To maximize the utility of the extracted technical specifications, our pipeline is designed not just to parse data, but to feed directly into an automated reasoning system. The flowchart below illustrates the simplified architecture, from raw PDF ingestion down to Retrieval-Augmented Generation (RAG).

```mermaid
flowchart LR
    PDF[Raw PDF] --> Layout[Layout & Section Analysis]
    Layout --> Extract[Hybrid Extraction]
    Extract --> Merge[Hierarchical JSON/MD]
    Merge --> RAG[(RAG Vector DB)]
    RAG --> Test[Automated Test Cases]
```

**Detailed Process Flow and RAG Database Integration**

1.  **Raw PDF Ingestion & Layout Analysis**: The document is processed to identify bounding boxes for texts, tables, and figures, while the Table of Contents establishes the hierarchical section boundaries.
2.  **Hybrid Extraction (PyMuPDF + VLM)**: Simple paragraphs are quickly parsed via PyMuPDF. Complex visual elements, including multi-page tables, are stitched together based on their section tags and sent to the Vision LLM (Qwen-VL) for high-fidelity markdown generation.
3.  **Hierarchical JSON/MD Merging**: The extracted text and structurally perfect markdown tables are merged back into a unified JSON schema, strictly organized by their original section hierarchy (e.g., Section 4.2.1.2).
4.  **RAG Vector DB Integration**: The hierarchical JSON files serve as pristine embedding chunks for our RAG database. By guaranteeing that multi-page tables are seamlessly stitched and ghost columns are eliminated, the context fed into the database is perfectly structured.
5.  **Automated Test Case Generation**: An LLM agent can now query this RAG database with complete confidence. For example, when querying "What is the physical byte sequence for the Activate method?", the LLM retrieves the exact row without hallucination, enabling the autonomous generation of flawless C++/Python compliance verification scripts.

- **The Value of High Fidelity**: When building a RAG system for engineering protocols, a single misaligned table column (such as the PyMuPDF ghost column error) corrupts the vector embedding. By utilizing our Section-Based Visual-Hybrid Pipeline, we eliminate these silent failures to ensure trust in fully automated downstream applications.

**7.2 Conclusion**
This study proves that for technical specification documents, the "traditional" trade-off between speed and accuracy is a false economy. The structural complexity and sparsity of technical tables make rule-based parsing inherently unreliable, leading to silent failures that cripple downstream automated applications. 

Our **Section-Based Visual-Hybrid Pipeline** effectively solves the "ghost column" and "misalignment" problems. Furthermore, by physically stitching multi-page visual elements prior to VLM inference, we completely bypassed the contextual fragmentation that traditionally plagues even state-of-the-art LLMs. While computationally more expensive upfront, producing a 100% accurate, structure-preserved dataset provides a robust, zero-hallucination foundation for RAG infrastructure and automated specification compliance. Future work will focus on optimizing the VLM context window to handle extremely long tables (10+ pages) without performance degradation.

**8. References**

[1] Trusted Computing Group (TCG), "TCG Storage Security Subsystem Class: Opal," Version 2.30.  
[2] Trusted Computing Group (TCG), "TCG Storage Architecture Core Specification," Version 2.01.  
[3] NVM Express, Inc., "NVM Express® Base Specification," Revision 2.0c (or Rev 2.03).  
[4] Open Compute Project (OCP), "Datacenter NVMe® SSD Specification," Version 2.0r21.  
[5] Bai, J., et al., "Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond," *arXiv preprint arXiv:2308.12966*, 2023. (See also Qwen2-VL/Qwen2.5-VL updates).  
[6] DeepSeek-AI, "DeepSeek-VL: Towards Real-World Vision-Language Understanding," *arXiv preprint arXiv:2403.05525*, 2024.  
[7] GLM Team, "ChatGLM: A Family of Large Language Models from GLM-130B to GLM-4 All Tools," *arXiv preprint arXiv:2406.12793*, 2024.  
[8] Anthropic, "The Claude 3 Model Family: Opus, Sonnet, Haiku," 2024.  
[9] Google DeepMind, "Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context," *arXiv preprint arXiv:2403.05530*, 2024.  
[10] Artifex Software, Inc., "PyMuPDF: A high performance Python library for data extraction, analysis, conversion & manipulation of PDF files," [Online]. Available: https://pymupdf.readthedocs.io/  
[11] Tabula, "Tabula: A tool for liberating data tables trapped inside PDF files," [Online]. Available: https://tabula.technology/  
[12] Camelot, "Camelot: PDF Table Extraction for Humans," [Online]. Available: https://camelot-py.readthedocs.io/

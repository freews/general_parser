import os
import sqlite3
import json
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Configuration
DB_PATH = "library.db"
IMAGE_DIR = "section_images"

MARKDOWN_DIR = "section_markdown"

HOST = "0.0.0.0"
PORT = 8000

app = FastAPI(
    title="SSD Engineering Library Viewer",
    description="API for accessing parsed SSD specification data",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path  # Add this import as it was used in glob

# -----------------------------------------------------------------------------
# Database Connection
# -----------------------------------------------------------------------------
def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail=f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------
class SectionSummary(BaseModel):
    id: int
    section_index: int
    pid: str
    title: str
    level: int
    page_range: str

class Attachment(BaseModel):
    id: int
    type: str
    unique_id: Optional[str] = None
    title: Optional[str] = None
    page_num: int
    bbox: Optional[Any] = None
    image_url: Optional[str] = None
    markdown_content: Optional[str] = None

class SectionDetail(SectionSummary):
    text_content: Optional[str] = None
    attachments: List[Attachment] = []



@app.get("/api/sections/{section_id}/markdown")
def get_section_markdown(section_id: int):
    """Get the rendered markdown content from the file system."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT section_index, title FROM sections WHERE id = ?", (section_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Section not found")

    section_index = row['section_index']
    
    # Find the corresponding markdown file: {index:03d}_*.md
    # Using glob to find the file
    md_files = list(sorted(Path(MARKDOWN_DIR).glob(f"{section_index:03d}_*.md")))
    
    if not md_files:
        # Fallback: try finding by title if index fails, or just return DB text
        # But for now, let's just return a message or the DB text
        return {"content": f"# {row['title']}\n\n*Markdown file not found for index {section_index:03d}.*"}
        
    md_file = md_files[0]
    try:
        content = md_file.read_text(encoding='utf-8')
        # Fix image paths: "../section_images/" -> "/images/"
        content = content.replace("../section_images/", "/images/")
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading markdown file: {str(e)}")


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSD Library Viewer</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .container { display: flex; height: 100vh; }
        .sidebar { 
            width: 300px; 
            background: #f0f2f5; 
            border-right: 1px solid #ddd; 
            overflow-y: auto; 
            display: flex; 
            flex-direction: column;
        }
        .sidebar-header { padding: 20px; background: #fff; border-bottom: 1px solid #ddd; position: sticky; top: 0; }
        .sidebar-header h2 { margin: 0; font-size: 1.2rem; color: #333; }
        .search-box { width: 100%; padding: 8px; margin-top: 10px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
        .section-list { list-style: none; padding: 0; margin: 0; }
        .section-item { 
            padding: 10px 20px; 
            cursor: pointer; 
            border-bottom: 1px solid #eee; 
            font-size: 0.9rem;
            color: #444;
        }
        .section-item:hover { background: #e6e8eb; }
        .section-item.active { background: #007bff; color: white; }
        .section-item .pid { font-size: 0.8em; opacity: 0.7; margin-bottom: 2px; }
        
        .main-content { flex: 1; overflow-y: auto; padding: 40px; background: #fff; }
        .markdown-body { max-width: 900px; margin: 0 auto; line-height: 1.6; color: #24292e; }
        .markdown-body img { max-width: 100%; border: 1px solid #eee; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .markdown-body table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        .markdown-body th, .markdown-body td { border: 1px solid #dfe2e5; padding: 6px 13px; }
        .markdown-body tr:nth-child(2n) { background-color: #f6f8fa; }
        
        /* Loading overlay */
        .loading { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); z-index: 1000; justify-content: center; align-items: center; }
        .loading.visible { display: flex; }
    </style>
</head>
<body>

<div class="container">
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>SSD Library</h2>
            <input type="text" id="search" class="search-box" placeholder="Search sections...">
        </div>
        <ul class="section-list" id="sectionList">
            <!-- Sections will be loaded here -->
        </ul>
    </div>
    <div class="main-content">
        <div class="markdown-body" id="content">
            <h1>Welcome</h1>
            <p>Select a section from the sidebar to view its content.</p>
        </div>
    </div>
</div>
<div class="loading" id="loading">Loading...</div>

<script>
    let allSections = [];

    async function fetchSections() {
        const response = await fetch('/api/sections');
        allSections = await response.json();
        renderSidebar(allSections);
    }

    function renderSidebar(sections) {
        const list = document.getElementById('sectionList');
        list.innerHTML = '';
        sections.forEach(sec => {
            const li = document.createElement('li');
            li.className = 'section-item';
            li.onclick = () => loadSection(sec.id, li);
            li.innerHTML = `
                <div class="pid">${sec.pid || ''}</div>
                <div>${sec.title}</div>
            `;
            list.appendChild(li);
        });
    }

    async function loadSection(id, element) {
        // Highlight active
        document.querySelectorAll('.section-item').forEach(el => el.classList.remove('active'));
        if(element) element.classList.add('active');

        document.getElementById('loading').classList.add('visible');
        
        try {
            const response = await fetch(`/api/sections/${id}/markdown`);
            const data = await response.json();
            document.getElementById('content').innerHTML = marked.parse(data.content);
        } catch (e) {
            document.getElementById('content').innerHTML = `<p style="color:red">Error loading section: ${e.message}</p>`;
        } finally {
            document.getElementById('loading').classList.remove('visible');
        }
    }

    document.getElementById('search').addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allSections.filter(s => 
            s.title.toLowerCase().includes(term) || 
            (s.pid && s.pid.toLowerCase().includes(term))
        );
        renderSidebar(filtered);
    });

    // Init
    fetchSections();
</script>

</body>
</html>
    """


@app.get("/api/sections", response_model=List[SectionSummary])
def get_sections():
    """Get a list of all sections, ordered by sequence."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT id, section_index, section_pid as pid, title, level, page_range 
        FROM sections 
        ORDER BY section_index
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        SectionSummary(
            id=row['id'],
            section_index=row['section_index'],
            pid=row['pid'],
            title=row['title'],
            level=row['level'],
            page_range=row['page_range']
        ) for row in rows
    ]

@app.get("/api/sections/{section_id}", response_model=SectionDetail)
def get_section_detail(section_id: int):
    """Get full details for a specific section, including text and attachments."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch section info
    cursor.execute("""
        SELECT id, section_index, section_pid as pid, title, level, page_range, text_content 
        FROM sections 
        WHERE id = ?
    """, (section_id,))
    section_row = cursor.fetchone()
    
    if not section_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Fetch attachments
    cursor.execute("""
        SELECT id, type, unique_id, title, page_num, bbox, image_path, markdown_content 
        FROM attachments 
        WHERE section_id = ?
    """, (section_id,))
    att_rows = cursor.fetchall()
    conn.close()
    
    attachments = []
    for row in att_rows:
        # Construct image URL if image_path exists
        img_url = None
        if row['image_path']:
             img_url = f"/images/{row['image_path']}"
             
        # Parse bbox json if needed
        bbox_val = row['bbox']
        if isinstance(bbox_val, str):
            try:
                bbox_val = json.loads(bbox_val)
            except:
                pass

        attachments.append(Attachment(
            id=row['id'],
            type=row['type'],
            unique_id=row['unique_id'],
            title=row['title'],
            page_num=row['page_num'],
            bbox=bbox_val,
            image_url=img_url,
            markdown_content=row['markdown_content']
        ))

    return SectionDetail(
        id=section_row['id'],
        section_index=section_row['section_index'],
        pid=section_row['pid'],
        title=section_row['title'],
        level=section_row['level'],
        page_range=section_row['page_range'],
        text_content=section_row['text_content'],
        attachments=attachments
    )

@app.get("/api/search", response_model=List[SectionSummary])
def search_sections(q: str = Query(..., min_length=2)):
    """Search for sections containing the query string in title or text."""
    conn = get_db_connection()
    cursor = conn.cursor()
    search_term = f"%{q}%"
    
    query = """
        SELECT id, section_index, section_pid as pid, title, level, page_range 
        FROM sections 
        WHERE title LIKE ? OR text_content LIKE ? 
        ORDER BY section_index
        LIMIT 50
    """
    cursor.execute(query, (search_term, search_term))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        SectionSummary(
            id=row['id'],
            section_index=row['section_index'],
            pid=row['pid'],
            title=row['title'],
            level=row['level'],
            page_range=row['page_range']
        ) for row in rows
    ]

# -----------------------------------------------------------------------------
# Static Files (Images)
# -----------------------------------------------------------------------------
if os.path.exists(IMAGE_DIR):
    app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")
    print(f"Mounted '{IMAGE_DIR}' at '/images'")
else:
    print(f"Warning: Image directory '{IMAGE_DIR}' not found. Images will not be served.")

if __name__ == "__main__":
    print(f"Starting server at http://{HOST}:{PORT}")
    print(f"Database: {DB_PATH}")
    uvicorn.run(app, host=HOST, port=PORT)

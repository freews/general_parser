import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="SSD ENG Library")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "../output/library.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class SectionNode(BaseModel):
    id: int
    section_index: int
    section_pid: str
    title: str
    level: int
    children: List['SectionNode'] = []

class Attachment(BaseModel):
    id: int
    type: str # 'table' | 'figure'
    unique_id: str
    title: Optional[str]
    page_num: int
    bbox: str
    image_path: str
    markdown_content: Optional[str]

class SectionDetail(BaseModel):
    id: int
    title: str
    section_pid: str
    text_content: Optional[str]
    attachments: List[Attachment]

@app.get("/api/sections")
def get_sections():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, section_index, section_pid, title, level FROM sections ORDER BY section_index")
    rows = cursor.fetchall()
    conn.close()
    
    # Build Tree
    root_nodes = []
    node_map = {}
    
    # First pass: create all nodes
    for row in rows:
        node = {
            "id": row['id'],
            "section_index": row['section_index'],
            "section_pid": row['section_pid'],
            "title": row['title'],
            "level": row['level'],
            "children": []
        }
        node_map[row['id']] = node
        
    # Second pass: build hierarchy (Basic stack based or parent lookback approach)
    # Since we have levels 1, 2, 3... and they are ordered by index.
    # Level N is a child of the nearest preceding Level N-1.
    
    stack = [] # Stores nodes: [Level 1, Level 2, ...]
    
    for row in rows:
        node = node_map[row['id']]
        current_level = node['level']
        
        # Pop stack until we find a parent (level < current_level)
        while stack and stack[-1]['level'] >= current_level:
            stack.pop()
            
        if not stack:
            # Root node (Level 1 usually)
            root_nodes.append(node)
        else:
            # Child node
            parent = stack[-1]
            parent['children'].append(node)
            
        stack.append(node)
        
    return root_nodes

@app.get("/api/section/{section_id}")
def get_section_detail(section_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get Section Info
    cursor.execute("SELECT * FROM sections WHERE id = ?", (section_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Get Attachments
    cursor.execute("SELECT * FROM attachments WHERE section_id = ?", (section_id,))
    att_rows = cursor.fetchall()
    
    attachments = []
    for att in att_rows:
        attachments.append({
            "id": att['id'],
            "type": att['type'],
            "unique_id": att['unique_id'],
            "title": att['title'],
            "page_num": att['page_num'],
            "bbox": att['bbox'],
            "image_path": att['image_path'],
            "markdown_content": att['markdown_content']
        })
    
    conn.close()
    
    return {
        "id": row['id'],
        "title": row['title'],
        "section_pid": row['section_pid'],
        "text_content": row['text_content'],
        "attachments": attachments
    }

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")
# Mount output images (to serve tables/figures)
# Assuming images are in ../output
# We need to serve from parent dir's output. 
# CAUTION: Serving parent directory via StaticFiles might be restricted or require absolute path.
output_dir = os.path.abspath("../output")
app.mount("/output", StaticFiles(directory=output_dir), name="output_files")


if __name__ == "__main__":
    print("Starting SSD ENG Library Server...")
    print("Go to http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

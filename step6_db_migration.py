import sqlite3
import json
import os
import re
from pathlib import Path
from datetime import datetime
from common_parameter import OUTPUT_DIR, PDF_PATH


from utils_logger import setup_advanced_logger
import logging

logger = setup_advanced_logger(name="step6_db_migration", dir=OUTPUT_DIR, log_level=logging.INFO)

# Configuration
DB_PATH = f"{OUTPUT_DIR}/library.db"
SECTION_DATA_DIR = f"{OUTPUT_DIR}/section_data_v2"
DOC_NAME = f"{OUTPUT_DIR}.db" 


def init_db():
    """Initialize the SQLite database with the required schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Documents Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. Sections Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        section_index INTEGER,  -- 0, 1, 2... for ordering
        section_pid TEXT,       -- "1.1", "4.2.1" (can be empty for Front matter)
        title TEXT,
        level INTEGER,          -- 1, 2, 3...
        start_page INTEGER,
        end_page INTEGER,
        text_content TEXT,      -- The full text content of the section
        page_range TEXT,        -- "5-8" string representation
        FOREIGN KEY (document_id) REFERENCES documents (id)
    )
    ''')
    
    # 3. Attachments Table (Tables and Figures)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id INTEGER,
        type TEXT CHECK(type IN ('table', 'figure')),
        unique_id TEXT,         -- "Table_3_1"
        title TEXT,
        page_num INTEGER,
        bbox TEXT,              -- JSON string "[x1, y1, x2, y2]"
        image_path TEXT,
        markdown_content TEXT,  -- LLM parsed markdown for tables
        FOREIGN KEY (section_id) REFERENCES sections (id)
    )
    ''')
    
    conn.commit()
    return conn

def migrate_data():
    """Migrate JSON data to SQLite."""
    conn = init_db()
    cursor = conn.cursor()
    
    # 1. Register Document
    cursor.execute("INSERT OR IGNORE INTO documents (name, description) VALUES (?, ?)", 
                   (DOC_NAME, "TCG Storage Security Subsystem Class: Opal"))
    cursor.execute("SELECT id FROM documents WHERE name = ?", (DOC_NAME,))
    doc_id = cursor.fetchone()[0]
    
    # Clear existing data for this document to avoid duplicates during re-runs
    cursor.execute("DELETE FROM attachments WHERE section_id IN (SELECT id FROM sections WHERE document_id = ?)", (doc_id,))
    cursor.execute("DELETE FROM sections WHERE document_id = ?", (doc_id,))
    conn.commit()
    
    print(f"Migrating data for Document ID: {doc_id} ({DOC_NAME})...")
    
    # 2. Iterate over JSON files
    json_files = sorted(Path(SECTION_DATA_DIR).glob("*.json"))
    
    count_sections = 0
    count_attachments = 0
    
    for json_file in json_files:
        if json_file.name == "section_index.json":
            continue
            
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # [Fix] Access fields directly from root, not data['section']
        # Structure: {"section_index": ..., "content": {"text": ...}, "pages": {"start": ...}}
        
        cursor.execute('''
        INSERT INTO sections (document_id, section_index, section_pid, title, level, start_page, end_page, text_content, page_range)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id,
            data['section_index'],
            data['section_id'],
            data['title'],
            data['level'],
            data['pages']['start'],
            data['pages']['end'],
            data['content']['text'],
            f"{data['pages']['start']}-{data['pages']['end']}"
        ))
        
        section_db_id = cursor.lastrowid
        count_sections += 1
        
        # Insert Tables
        for table in data.get('content', {}).get('tables', []):
            cursor.execute('''
            INSERT INTO attachments (section_id, type, unique_id, title, page_num, bbox, image_path, markdown_content)
            VALUES (?, 'table', ?, ?, ?, ?, ?, ?)
            ''', (
                section_db_id,
                table.get('table_id', table.get('id')),  # Fallback to 'id'
                table.get('title'),
                table['page'],
                json.dumps(table['bbox']),
                table.get('image_path'),                 # Handle missing image_path
                table.get('markdown', table.get('table_md')) # Fallback to table_md
            ))
            count_attachments += 1
            
        # Insert Figures
        for figure in data.get('content', {}).get('figures', []):
            cursor.execute('''
            INSERT INTO attachments (section_id, type, unique_id, title, page_num, bbox, image_path, markdown_content)
            VALUES (?, 'figure', ?, ?, ?, ?, ?, ?)
            ''', (
                section_db_id,
                figure.get('figure_id', figure.get('id')), # Fallback to 'id'
                figure.get('title'),
                figure['page'],
                json.dumps(figure['bbox']),
                figure.get('image_path'),                  # Handle missing image_path
                figure.get('description')
            ))
            count_attachments += 1

    conn.commit()
    conn.close()
    print(f"Migration Complete!")
    print(f"  - Sections: {count_sections}")
    print(f"  - Attachments: {count_attachments}")
    print(f"  - Database: {DB_PATH}")

if __name__ == "__main__":
    migrate_data()

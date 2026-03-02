import sqlite3
import os
import chromadb
import argparse
import glob
from pathlib import Path
from tqdm import tqdm
import logging
from logger import setup_advanced_logger
from common_parameter import GLOBAL_DB_DIR, VECTOR_DB_DIR
from lib_llm_client import LLMEmbeddingClient

logger = setup_advanced_logger(name="step9_rag_indexer", log_dir=GLOBAL_DB_DIR, log_level=logging.INFO)

def chunk_text(text: str, max_len: int = 1500, overlap: int = 150) -> list[str]:
    """텍스트를 max_len 길이로 overlap을 두고 분할"""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_len
        chunks.append(text[start:end])
        start += max_len - overlap
    return chunks

def build_indexer_for_db(input_dir: str, collection, embed_client):
    db_path = f"{input_dir}/library.db"
    if not os.path.exists(db_path):
        logger.error(f"DB not found at {db_path}. Skipping.")
        return

    logger.info(f"--- Processing DB: {db_path} ---")
    db_prefix = os.path.basename(os.path.normpath(input_dir))
    
    # Connect SQLite
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if table exists before querying
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sections';")
    if not cursor.fetchone():
        logger.error(f"Table 'sections' not found in DB: {db_path}. Have you run step6_db_migration.py on this OUTPUT_DIR ({input_dir})?")
        conn.close()
        return

    logger.info("Fetching Sections with Document Info...")
    cursor.execute("""
        SELECT s.*, d.name as doc_name 
        FROM sections s
        JOIN documents d ON s.document_id = d.id
    """)
    sections = cursor.fetchall()
    
    logger.info("Fetching Attachments with Document Info...")
    cursor.execute("""
        SELECT a.*, s.document_id, d.name as doc_name
        FROM attachments a
        JOIN sections s ON a.section_id = s.id
        JOIN documents d ON s.document_id = d.id
    """)
    attachments = cursor.fetchall()
    
    # 1. Prepare chunks
    documents_to_embed = []
    metadata_list = []
    ids_list = []
    
    logger.info("Processing sections...")
    for sec in sections:
        content = sec['text_content']
        if not content or len(content.strip()) < 10:
            continue
            
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            documents_to_embed.append(chunk)
            metadata_list.append({
                "source_type": "section",
                "document_id": sec['document_id'],
                "doc_name": str(sec['doc_name']),
                "section_id": sec['id'],
                "section_pid": str(sec['section_pid']) if sec['section_pid'] else "",
                "title": str(sec['title']) if sec['title'] else "",
                "page_range": str(sec['page_range']) if sec['page_range'] else ""
            })
            ids_list.append(f"{db_prefix}_sec_{sec['id']}_chunk_{i}")
            
    logger.info("Processing attachments...")
    for att in attachments:
        content = att['markdown_content']
        if not content or len(content.strip()) < 10:
            continue
            
        # 표나 그림은 구조를 유지하는 것이 좋으므로 너무 길지 않다면 통째로 넣고,
        # 길다면 분할합니다.
        chunks = chunk_text(f"Title: {att['title']}\n\n{content}")
        for i, chunk in enumerate(chunks):
            documents_to_embed.append(chunk)
            metadata_list.append({
                "source_type": f"attachment_{att['type']}",
                "document_id": att['document_id'],
                "doc_name": str(att['doc_name']),
                "section_id": att['section_id'],
                "unique_id": str(att['unique_id']) if att['unique_id'] else "",
                "title": str(att['title']) if att['title'] else "",
                "page_num": int(att['page_num']) if att['page_num'] else 0
            })
            ids_list.append(f"{db_prefix}_att_{att['id']}_chunk_{i}")

    # 2. Add to ChromaDB in batches
    BATCH_SIZE = 50
    logger.info(f"Total chunks to embed: {len(documents_to_embed)}")
    
    for i in tqdm(range(0, len(documents_to_embed), BATCH_SIZE)):
        batch_docs = documents_to_embed[i:i+BATCH_SIZE]
        batch_metas = metadata_list[i:i+BATCH_SIZE]
        batch_ids = ids_list[i:i+BATCH_SIZE]
        
        # 임베딩 생성
        embeddings = embed_client.get_embeddings(batch_docs)
        
        if embeddings and len(embeddings) == len(batch_docs):
            collection.upsert(
                documents=batch_docs,
                embeddings=embeddings,
                metadatas=batch_metas,
                ids=batch_ids
            )
        else:
            logger.error(f"Failed to get embeddings for batch starting at {i}. Skipping.")

    logger.info(f"Finished processing {input_dir}\n")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Build RAG Index across multiple parsed directories")
    parser.add_argument("-i", "--input", nargs='+', required=True, 
                        help="One or more input directories (e.g., o_tcg_opal_v2p30 o_nvme_base_v2p03) or 'all' for all o_* folders")
    args = parser.parse_args()
    
    # Resolve 'all' or wildcards into actual directories
    input_dirs = []
    for val in args.input:
        if val.lower() == 'all':
            input_dirs.extend(glob.glob("o_*"))
        elif '*' in val:
            input_dirs.extend(glob.glob(val))
        else:
            input_dirs.append(val)
            
    # Remove duplicates
    input_dirs = list(dict.fromkeys(input_dirs))
    
    if not input_dirs:
        logger.error("No valid input directories found.")
        return

    logger.info(f"Target directories to index: {input_dirs}")
    logger.info(f"Initializing global ChromaDB at {VECTOR_DB_DIR}...")
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    collection = chroma_client.get_or_create_collection(
        name="tcg_documents",
        metadata={"hnsw:space": "cosine"}
    )
    
    embed_client = LLMEmbeddingClient()
    
    import time
    start = time.time()
    
    for d in input_dirs:
        if os.path.isdir(d):
            build_indexer_for_db(d, collection, embed_client)
        else:
            logger.warning(f"Directory {d} does not exist. Skipping.")
            
    logger.info(f"Total Indexing Time: {time.time() - start:.2f} seconds")

if __name__ == "__main__":
    main()

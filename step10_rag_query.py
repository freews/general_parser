import argparse
import chromadb
import logging
from logger import setup_advanced_logger
from common_parameter import OUTPUT_DIR, VECTOR_DB_DIR
from lib_llm_client import LLMEmbeddingClient, LLMQueryClient

logger = setup_advanced_logger(name="step10_rag_query", log_dir=OUTPUT_DIR, log_level=logging.INFO)

def run_query(question: str, top_k: int = 5, db_path: str = VECTOR_DB_DIR):
    logger.info(f"Connecting to ChromaDB at {db_path}")
    chroma_client = chromadb.PersistentClient(path=db_path)
    try:
        collection = chroma_client.get_collection(name="tcg_documents")
    except Exception as e:
        logger.error(f"Collection 'tcg_documents' not found in {db_path}. Please run step9_rag_indexer.py first to build this DB.")
        return
    
    embed_client = LLMEmbeddingClient()
    query_client = LLMQueryClient()
    
    logger.info("Generating embedding for the query...")
    q_embeds = embed_client.get_embeddings([question])
    if not q_embeds:
        logger.error("Failed to generate embedding for the query.")
        return
        
    q_embed = q_embeds[0]
    
    logger.info(f"Retrieving top {top_k} relevant contexts...")
    results = collection.query(
        query_embeddings=[q_embed],
        n_results=top_k
    )
    
    if not results['documents'] or not results['documents'][0]:
        logger.warning("No relevant contexts found.")
        return
    
    contexts = results['documents'][0]
    metadatas = results['metadatas'][0]
    
    # 1. Build context string
    context_str_parts = []
    for i, (ctx, meta) in enumerate(zip(contexts, metadatas), 1):
        doc_name = meta.get('doc_name', 'Unknown Document')
        source = meta.get('source_type', 'unknown')
        title = meta.get('title', 'Unknown Title')
        
        if source == 'section':
            sec_pid = meta.get('section_pid', '')
            source_info = f"Document: [{doc_name}] | Section {sec_pid}: {title}"
        elif source.startswith('attachment_'):
            type_name = source.split('_')[1]
            source_info = f"Document: [{doc_name}] | {type_name.capitalize()} in Section {meta.get('section_id')}: {title}"
        else:
            source_info = f"Document: [{doc_name}] | Source: {title}"
            
        context_str_parts.append(f"--- Context {i} ({source_info}) ---\n{ctx}\n")
        
    context_str = "\n".join(context_str_parts)
    
    # 2. RAG Prompt
    system_prompt = """You are a helpful and knowledgeable technical assistant for the NVMe/TCG specification documents.
Use the provided extracted document contexts to answer the user's question accurately.
If the answer cannot be found in the contexts, state clearly that you don't know based on the provided documents.
When answering, explicitly mention the section or table/figure title you refer to.
Do NOT use outside knowledge if it contradicts the contexts."""

    user_prompt = f"""Question: {question}

Contexts from the Document:
{context_str}

Please provide a detailed and accurate answer based ONLY on the contexts above."""
    
    logger.info("Generating RAG answer via LLM...")
    answer = query_client.generate_response(system_prompt=system_prompt, user_prompt=user_prompt)
    
    print("\n" + "="*80)
    print(f"QUESTION: {question}")
    print("="*80)
    print(f"\nANSWER:\n{answer}")
    print("\n" + "-"*80)
    print("SOURCES USED:")
    for meta in metadatas:
        doc_name = meta.get('doc_name', 'Unknown Document')
        title = meta.get('title', 'Unknown Title')
        if meta.get('source_type') == 'section':
             print(f"- [{doc_name}] Section {meta.get('section_pid', '')}: {title} (Page {meta.get('page_range', '')})")
        else:
             print(f"- [{doc_name}] Attachment {meta.get('unique_id', '')}: {title} (Page {meta.get('page_num', '')})")
    print("="*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the RAG system")
    parser.add_argument("query", type=str, nargs="?", help="The question to ask", default="What is Opal SSC?")
    parser.add_argument("--top_k", type=int, default=5, help="Number of contexts to retrieve")
    parser.add_argument("--db_path", type=str, default=VECTOR_DB_DIR, help="Path to the global DB directory to query")
    args = parser.parse_args()
    
    run_query(args.query, args.top_k, db_path=args.db_path)

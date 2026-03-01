import os

# 환경 변수에서 설정을 읽어옵니다. (배치 실행 지원)
# 기본값은 테스트용 또는 마지막 설정값으로 유지합니다.
PDF_PATH = os.getenv("PDF_PATH", "source_doc/Datacenter NVMe SSD Specification v2.0r21.pdf")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "o_tcg_opal_v2p30")


TABLE_DPI = 120  # Table Image DPI

# LLM Configuration
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3-vl:30b-a3b-instruct-q4_K_M")

# RAG & Global Database Configuration
# 여러 문서를 하나의 DB/ChromaDB에 통합하여 검색하기 위한 경로 설정
GLOBAL_DB_DIR = os.getenv("GLOBAL_DB_DIR", "global_db")
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", f"{GLOBAL_DB_DIR}/chroma_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


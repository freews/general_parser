import ast
import chromadb
import os
import sys

# 프로젝트 내 로컬 LLM 임베딩 클라이언트 활용
from lib_llm_client import LLMEmbeddingClient

from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

# 임베딩 함수 어댑터 클래스 (ChromaDB의 EmbeddingFunction 인터페이스에 맞춤)
class LocalLLMEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.client = LLMEmbeddingClient()
        
    def name(self) -> str:
        return "local_llm_embedding"
        
    def __call__(self, input: Documents) -> Embeddings:
        # LLMEmbeddingClient의 get_embeddings 사용
        return self.client.get_embeddings(input)
        
    def embed_documents(self, input: Documents) -> Embeddings:
        return self.__call__(input)
        
    def embed_query(self, input: Documents) -> Embeddings:
        return self.__call__(input)

# 기존의 무거운 SentenceTransformer 대신 로컬 LLM 기반 임베딩 사용
sentence_transformer_ef = LocalLLMEmbeddingFunction()

def parse_python_file(file_path):
    """
    AST를 이용해 대상 파이썬 파일의 클래스와 함수 단위로 Docstring과 시그니처를 추출합니다.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    tree = ast.parse(file_content)
    api_docs = []

    for node in ast.walk(tree):
        # 클래스 내의 메소드들을 추출하기 위해 ClassDef도 순회합니다
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            class_doc = ast.get_docstring(node) or "No document"
            
            # 클래스 자체 설명 인덱싱
            api_docs.append({
                "id": f"{class_name}",
                "text": f"[Source: {file_path}]\nClass: {class_name}\nDescription: {class_doc}\n",
                "metadata": {
                    "source": file_path,
                    "type": "class",
                    "name": class_name
                }
            })

            # 클래스 안의 메소드들 추출
            for body_node in node.body:
                if isinstance(body_node, ast.FunctionDef):
                    docstring = ast.get_docstring(body_node) or "No document"
                    args = [arg.arg for arg in body_node.args.args]
                    args_str = ", ".join(args)
                    signature = f"def {body_node.name}({args_str}):"
                    
                    chunk_content = (
                        f"[Source: {file_path}]\n"
                        f"Class: {class_name}\n"
                        f"API Signature: {signature}\n"
                        f"Description: {docstring}\n"
                    )
                    
                    api_docs.append({
                        "id": f"{class_name}_{body_node.name}",
                        "text": chunk_content,
                        "metadata": {
                            "source": file_path,
                            "type": "method",
                            "class_name": class_name,
                            "name": body_node.name
                        }
                    })
                    
        # 모듈 전역 함수인 경우 (Class 바깥에 있는 함수)
        elif isinstance(node, ast.FunctionDef) and not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if node in getattr(parent, 'body', [])):
            # 간단하게 전역 함수 처리 (위 조건은 완벽한 부모-자식 트리 순회는 아님)
            # 여기서는 편의상 Method 위주로 봅니다.
            pass
            
    return api_docs

def build_code_rag(db_path, target_py_file):
    print(f"[{target_py_file}] 파일 파싱 시작...")
    api_docs = parse_python_file(target_py_file)
    
    if not api_docs:
        print("파싱할 클래스/함수가 없습니다.")
        return

    print(f"총 {len(api_docs)} 개의 API(클래스/메소드) 식별 완료. DB 인덱싱 시작...")
    
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)
    
    # company_api_docs 컬렉션 생성 (기존에 있으면 가져옴)
    collection = client.get_or_create_collection(
        name="company_api_docs", 
        embedding_function=sentence_transformer_ef
    )
    
    # Batch 형태로 밀어넣기 처리 (너무 많으면 쪼개서 넣어야 함)
    BATCH_SIZE = 100
    for i in range(0, len(api_docs), BATCH_SIZE):
        batch = api_docs[i:i+BATCH_SIZE]
        
        documents = [doc['text'] for doc in batch]
        metadatas = [doc['metadata'] for doc in batch]
        ids = [doc['id'] for doc in batch]
        
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f" -> {i+1} ~ {i+len(batch)} 인덱싱 완료")
        
    print(f"\n✅ 완료! RAG DB 저장 위치: {os.path.abspath(db_path)}")
    print(f"총 {len(api_docs)}개의 항목을 색인했습니다.")
    
    # 잘 들어갔는지 샘플 1개 검색 테스트해보기
    print("\n[DB 검색 테스트] 'flush' 기능 검색 중...")
    results = collection.query(
        query_texts=["How to send flush command?"],
        n_results=1
    )
    
    if results['documents'] and results['documents'][0]:
        print("\n--- 검색 결과 Top 1 ---")
        print(results['documents'][0][0])
        print("-----------------------")

if __name__ == "__main__":
    build_code_rag(db_path="./api_rag_db", target_py_file="nvme.py")

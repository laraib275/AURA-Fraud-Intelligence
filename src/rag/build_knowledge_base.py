from pathlib import Path
from .document_loader import load_documents
from .chunker import chunk_documents
from .retriever import TfidfRetriever

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"
INDEX_PATH = PROJECT_ROOT / "data" / "rag" / "tfidf_retriever.pkl"

def main():
    documents = load_documents(str(KNOWLEDGE_DIR))
    chunks = chunk_documents(documents)
    retriever = TfidfRetriever()
    retriever.fit(chunks)
    retriever.save(str(INDEX_PATH))
    print(f"Loaded documents : {len(documents)}")
    print(f"Created chunks   : {len(chunks)}")
    print(f"Saved index      : {INDEX_PATH}")

if __name__ == "__main__":
    main()

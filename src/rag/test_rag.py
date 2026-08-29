from pathlib import Path
import json
from .retriever import TfidfRetriever
from .rag_pipeline import RAGPipeline

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = PROJECT_ROOT / "data" / "rag" / "tfidf_retriever.pkl"

def main():
    retriever = TfidfRetriever.load(str(INDEX_PATH))
    pipeline = RAGPipeline(retriever)
    investigation = {
        "risk_band": "CRITICAL",
        "recommended_action": "IMMEDIATE INVESTIGATION",
        "fraud_probability": 0.0033,
        "amount": 1474.78,
        "investigation_reasons": [
            "Transaction amount is substantially above customer history",
            "Previously unseen merchant for this customer",
        ],
        "top_risk_factors": [{"feature": "transactions_prev_1h", "value": 2}],
        "graph_analysis": {
            "graph_reasons": ["Customer is connected to high-risk transaction(s)"]
        },
    }
    print(json.dumps(pipeline.retrieve_for_investigation(investigation), indent=2))
    print("\n--- RAG CONTEXT ---\n")
    print(pipeline.build_context(investigation))

if __name__ == "__main__":
    main()

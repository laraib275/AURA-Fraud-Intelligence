from typing import Dict, List
from .retriever import TfidfRetriever

class RAGPipeline:
    def __init__(self, retriever: TfidfRetriever):
        self.retriever = retriever

    def build_query(self, investigation: Dict) -> str:
        parts = []
        for key in ("risk_band", "recommended_action", "fraud_probability", "amount"):
            value = investigation.get(key)
            if value is not None:
                parts.append(f"{key}: {value}")
        parts.extend(str(x) for x in investigation.get("investigation_reasons", []))
        for factor in investigation.get("top_risk_factors", []):
            if factor.get("feature"):
                parts.append(f"{factor['feature']}: {factor.get('value')}")
        graph = investigation.get("graph_analysis") or {}
        if isinstance(graph, dict):
            parts.extend(str(x) for x in graph.get("graph_reasons", []))
        return " ".join(parts)

    def retrieve_for_investigation(self, investigation: Dict, top_k: int = 5) -> List[Dict]:
        return self.retriever.retrieve(self.build_query(investigation), top_k)

    def build_context(self, investigation: Dict, top_k: int = 5) -> str:
        results = self.retrieve_for_investigation(investigation, top_k)
        if not results:
            return "No relevant knowledge was retrieved."
        return "\n\n".join(
            f"[Knowledge {i}]\nSource: {r['source']}\nTitle: {r['title']}\n"
            f"Relevance: {r['score']:.4f}\nContent:\n{r['text']}"
            for i, r in enumerate(results, 1)
        )

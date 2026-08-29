from pathlib import Path
from typing import List, Dict
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TfidfRetriever:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True, stop_words="english", ngram_range=(1, 2), max_features=30000
        )
        self.matrix = None
        self.chunks: List[Dict[str, str]] = []

    def fit(self, chunks: List[Dict[str, str]]) -> None:
        if not chunks:
            raise ValueError("No chunks supplied to retriever.")
        self.chunks = chunks
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in chunks])

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.matrix is None:
            raise RuntimeError("Retriever has not been fitted.")
        if not query.strip():
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        ranked = scores.argsort()[::-1][:top_k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in ranked]

    def save(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str) -> "TfidfRetriever":
        with Path(path).open("rb") as f:
            return pickle.load(f)

from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks

def chunk_documents(documents: List[Dict[str, str]], chunk_size: int = 900, overlap: int = 150) -> List[Dict[str, str]]:
    result = []
    for doc in documents:
        for index, chunk in enumerate(chunk_text(doc["text"], chunk_size, overlap)):
            result.append({
                "chunk_id": f'{doc["title"]}_{index}',
                "source": doc["source"],
                "title": doc["title"],
                "text": chunk,
            })
    return result

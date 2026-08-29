from pathlib import Path
from typing import List, Dict

SUPPORTED_EXTENSIONS = {".md", ".txt"}

def load_documents(root_dir: str) -> List[Dict[str, str]]:
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Knowledge base not found: {root}")
    documents = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append({"source": str(path), "title": path.stem, "text": text})
    return documents

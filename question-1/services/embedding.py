import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict

# Load model lazily
_model = None
def get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else ("mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu")
        _model = SentenceTransformer('BAAI/bge-small-zh-v1.5', device=device)
    return _model

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += (chunk_size - overlap)
    return chunks

class VectorStore:
    def __init__(self):
        # Maps doc_id -> list of chunk embeddings (numpy arrays)
        self.doc_embeddings: Dict[str, np.ndarray] = {}
        # Maps doc_id -> list of chunk texts
        self.doc_chunks: Dict[str, List[str]] = {}

    def add_document(self, id: str, text: str):
        chunks = chunk_text(text)
        if not chunks:
            return
        self.doc_chunks[id] = chunks
        
        # Batch encode chunks
        model = get_model()
        # SentenceTransformers encode returns numpy arrays by default
        embeddings = model.encode(chunks, normalize_embeddings=True)
        self.doc_embeddings[id] = embeddings

    def search(self, query: str) -> Dict[str, float]:
        """Returns map of doc_id -> max chunk similarity score"""
        if not self.doc_embeddings:
            return {}
            
        model = get_model()
        query_emb = model.encode([query], normalize_embeddings=True)[0]
        
        results = {}
        for doc_id, chunk_embs in self.doc_embeddings.items():
            # compute dot product for all chunks
            similarities = np.dot(chunk_embs, query_emb)
            max_sim = np.max(similarities)
            results[doc_id] = float(max_sim)
        return results

vec_store = VectorStore()

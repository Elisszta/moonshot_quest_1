import torch
from sentence_transformers import CrossEncoder
from typing import List, Dict

_model = None
def get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else ("mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu")
        _model = CrossEncoder('BAAI/bge-reranker-base', device=device)
    return _model

def rerank(query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Reranks a list of documents utilizing cross-encoder.
    """
    if not documents:
        return []
    
    docs_to_rerank = documents[:top_k]
    model = get_model()
    
    sentence_pairs = [
        [query, f"{doc.get('title', '')}\n{doc.get('title', '')}\n{doc.get('title', '')}\n{doc.get('text', '')[:800]}"]
        for doc in docs_to_rerank
    ]
    scores = model.predict(sentence_pairs)
    
    for idx, doc in enumerate(docs_to_rerank):
        doc["score"] = float(scores[idx])
        
    docs_to_rerank.sort(key=lambda x: x["score"], reverse=True)
    return docs_to_rerank

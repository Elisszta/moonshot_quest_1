import os
from pydantic import BaseModel
from typing import List, Dict
from services.html_parser import parse_html

from services.embedding import vec_store

class Document(BaseModel):
    id: str
    title: str
    text: str

class DocumentStore:
    def __init__(self):
        self.documents: Dict[str, Document] = {}

    def add_document(self, id: str, html_content: str) -> Document:
        parsed = parse_html(html_content)
        doc = Document(id=id, title=parsed["title"], text=parsed["text"])
        self.documents[id] = doc
        
        # Populate Phase 2 embedding store
        vec_store.add_document(id, parsed["text"])
        
        return doc

        
    def get_all(self) -> List[Document]:
        return list(self.documents.values())

# Global store instance
store = DocumentStore()

def load_initial_data(data_dir: str = "data"):
    if not os.path.exists(data_dir):
        return
    for filename in os.listdir(data_dir):
        if filename.endswith(".html"):
            doc_id = filename.replace(".html", "")
            with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as f:
                store.add_document(doc_id, f.read())

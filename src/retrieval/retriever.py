"""
FinGuard-India Phase 7: Regulatory Retrieval System (RAG)
Chunks extracted regulations, computes SentenceTransformer embeddings (all-MiniLM-L6-v2),
builds a persistent FAISS index, and provides a top-k semantic search engine
returning full regulatory context with official legal citations.
"""

import json
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_DIR = os.path.join("data", "processed", "faiss_index")
INDEX_FILE = os.path.join(INDEX_DIR, "regulations.index")
METADATA_FILE = os.path.join(INDEX_DIR, "chunks_metadata.pkl")

class RegulatoryRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.metadata = []

    def _load_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    def build_index(self, regulations_json_path: str):
        self._load_model()
        with open(regulations_json_path, "r", encoding="utf-8") as f:
            clauses = json.load(f)

        chunks = []
        chunk_metas = []

        for i, c in enumerate(clauses):
            # Chunk representation combining document, section, and statutory text
            chunk_text = f"Regulator: {c['regulator']}\nDocument: {c['document']}\nSection: {c['section']} ({c.get('heading', '')})\nStatutory Text: {c['text']}"
            chunks.append(chunk_text)
            
            chunk_metas.append({
                "chunk_id": f"CHUNK_{i:03d}",
                "regulator": c["regulator"],
                "document": c["document"],
                "filename": c.get("filename", ""),
                "section": c["section"],
                "heading": c.get("heading", ""),
                "page": c.get("page", 1),
                "text": c["text"],
                "source_url": c.get("source_url", "")
            })

        print(f"Embedding {len(chunks)} regulatory chunks...")
        embeddings = self.model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        dimension = embeddings.shape[1]

        # Inner Product for normalized cosine similarity
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self.metadata = chunk_metas

        os.makedirs(INDEX_DIR, exist_ok=True)
        faiss.write_index(self.index, INDEX_FILE)
        with open(METADATA_FILE, "wb") as f:
            pickle.dump(self.metadata, f)

        print(f"FAISS index built and saved successfully ({len(chunks)} chunks, dim={dimension}).")

    def load_index(self):
        self._load_model()
        if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
            raise FileNotFoundError("FAISS index or metadata not found. Run build_index() first.")
        self.index = faiss.read_index(INDEX_FILE)
        with open(METADATA_FILE, "rb") as f:
            self.metadata = pickle.load(f)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        self._load_model()
        if self.index is None:
            self.load_index()

        query_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self.index.search(query_emb, top_k)

        results = []
        for rank, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                res = dict(self.metadata[idx])
                res["score"] = float(scores[0][rank])
                results.append(res)
        return results

if __name__ == "__main__":
    reg_json = os.path.join("data", "processed", "regulations.json")
    retriever = RegulatoryRetriever()
    retriever.build_index(reg_json)
    
    # Test query
    sample_q = "What is the penalty or rule for an insider trading on unreleased financial numbers?"
    print(f"\n--- Testing Semantic Search Query: '{sample_q}' ---")
    hits = retriever.search(sample_q, top_k=2)
    for h in hits:
        print(f"-> [Score: {h['score']:.4f}] {h['document']} | {h['section']}")
        print(f"   Excerpt: {h['text'][:140]}...\n")

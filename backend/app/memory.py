# memory.py
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import os
import json
from typing import List, Tuple

MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast embeddings
EMB_DIM = 384

class Memory:
    def __init__(self, index_path="faiss.index", meta_path="meta.json"):
        self.embed_model = SentenceTransformer(MODEL_NAME)
        self.index_path = index_path
        self.meta_path = meta_path
        self.dim = EMB_DIM

        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.meta = []  # list of dicts: {id, text, speaker, ts}
            self._persist()

    def _persist(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)

    def embed(self, texts: List[str]) -> np.ndarray:
        return self.embed_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def add(self, text: str, speaker: str, ts: float):
        vec = self.embed([text])
        idx = len(self.meta)
        self.index.add(vec)
        self.meta.append({"id": idx, "text": text, "speaker": speaker, "ts": ts})
        self._persist()

    def search(self, query: str, top_k=5) -> List[Tuple[dict, float]]:
        qv = self.embed([query])
        if self.index.ntotal == 0:
            return []
        D, I = self.index.search(qv, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(D[0], I[0]):
            meta = self.meta[idx]
            results.append((meta, float(score)))
        return results

    def all_text(self):
        return [m["text"] for m in self.meta]

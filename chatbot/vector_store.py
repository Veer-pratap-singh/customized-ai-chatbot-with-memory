import os
import pickle
import numpy as np
import faiss

class VectorStore:
    def __init__(self, index_path="chatbot/documents/vector_store.index", metadata_path="chatbot/documents/vector_store.pkl"):
        # We can detect if we are running from inside the chatbot directory or from the root directory
        # to ensure the paths resolve correctly.
        if os.path.exists("chatbot/documents") or os.path.exists("chatbot"):
            self.index_path = "chatbot/documents/vector_store.index"
            self.metadata_path = "chatbot/documents/vector_store.pkl"
        else:
            self.index_path = "documents/vector_store.index"
            self.metadata_path = "documents/vector_store.pkl"
            
        self.index = None
        self.metadata = []

    def create_index(self, vectors):
        if not vectors:
            return
        # Extract embeddings
        embeddings = np.array([v["embedding"] for v in vectors]).astype("float32")
        dimension = embeddings.shape[1]
        
        # Build FAISS index
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata = []
        for v in vectors:
            meta = {k: val for k, val in v.items() if k != "embedding"}
            self.metadata.append(meta)

    def save(self):
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)

    def search(self, query_embedding, top_k=3, where=None):
        if self.index is None or not self.metadata:
            return []
        
        # Reshape query embedding
        query = np.array([query_embedding]).astype("float32")
        distances, indices = self.index.search(query, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx].copy()
            meta["distance"] = float(distances[0][i])
            results.append(meta)
        return results

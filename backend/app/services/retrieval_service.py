import os
import json
import logging
import numpy as np
from typing import List, Dict, Any
from app.config.settings import get_settings

logger = logging.getLogger("omnivision")
settings = get_settings()

class RetrievalService:
    def __init__(self):
        self.kb_dir = settings.KNOWLEDGE_BASE_DIR
        self.active_packs = settings.ACTIVE_KNOWLEDGE_PACKS
        self.index = None
        self.metadata = {}
        self._load_indices()

    def _load_indices(self):
        try:
            import faiss
        except ImportError:
            logger.warning("FAISS not installed. Retrieval disabled.")
            return

        logger.info(f"Loading Knowledge Packs: {self.active_packs}")
        
        # In v1.0, we just load the first active pack for simplicity
        # A robust implementation would merge faiss indices if multiple packs are specified.
        if not self.active_packs:
            return
            
        pack_name = self.active_packs[0]
        pack_path = os.path.join(self.kb_dir, pack_name)
        index_path = os.path.join(pack_path, "index.faiss")
        meta_path = os.path.join(pack_path, "metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.index = faiss.read_index(index_path)
            with open(meta_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded {pack_name} with {self.index.ntotal} entries.")
        else:
            logger.warning(f"Knowledge pack {pack_name} not found at {pack_path}.")

    def search(self, query_vector: List[float], k: int = 1) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Retrieval skipped: No FAISS index loaded.")
            return []
            
        try:
            logger.debug(f"Searching FAISS index for Top-{k} matches...")
            # Convert to numpy array of float32 (required by FAISS)
            query_np = np.array([query_vector], dtype=np.float32)
            
            distances, indices = self.index.search(query_np, k)
            
            results = []
            for i in range(k):
                idx = str(indices[0][i])
                score = float(distances[0][i])
                if idx in self.metadata:
                    results.append({
                        "entity": self.metadata[idx].get("entity", "Unknown"),
                        "fact": self.metadata[idx].get("fact", ""),
                        "score": score
                    })
                    
            logger.debug(f"Retrieved: {results}")
            return results
        except Exception as e:
            logger.error(f"FAISS search failed: {str(e)}")
            return []

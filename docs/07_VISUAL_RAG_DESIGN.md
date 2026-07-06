# 07_VISUAL_RAG_DESIGN.md
Version 1.0
Status: LOCKED

## 1. Introduction
This document details the Visual Retrieval-Augmented Generation (RAG) architecture of OmniVision. While traditional text-based RAG retrieves documents based on text queries, OmniVision retrieves contextual knowledge based on the visual semantics of an uploaded image using CLIP embeddings. This enables the platform to enrich generic image captions with specific, domain-aware factual information.

## 2. Knowledge Pack Framework
To ensure scalability and domain adaptability, the knowledge base is not a monolithic file. It is structured as modular **Knowledge Packs**.

### 2.1 Directory Structure
```text
knowledge_base/
├── heritage_pack/
│   ├── index.faiss            # Pre-computed FAISS vector index
│   └── metadata.json          # Text entries mapped to vector IDs
├── wildlife_pack/
│   ├── index.faiss
│   └── metadata.json
└── custom_pack/
    ├── index.faiss
    └── metadata.json
```

### 2.2 Activation Strategy
At application startup, the `RetrievalService` reads the `ACTIVE_KNOWLEDGE_PACKS` environment variable (e.g., `["heritage_pack", "wildlife_pack"]`). It loads the respective `.faiss` indices and merges them into a single in-memory FAISS index. This allows administrators to seamlessly swap domains without modifying Python code.

## 3. Embedding Architecture
To perform semantic searches, OmniVision relies on **OpenAI's CLIP (Contrastive Language-Image Pretraining)** model (`clip-vit-base-patch32`). 

### 3.1 Why CLIP?
CLIP is trained on aligned image-text pairs, meaning an image of the "Taj Mahal" and the text "Taj Mahal" exist closely in the same high-dimensional vector space. By encoding the user's uploaded image into a 512-dimensional vector, we can search against text-based facts in our knowledge base.

### 3.2 L2 Normalization
For accurate cosine similarity comparisons using FAISS's `IndexFlatIP` (Inner Product), both the pre-computed text embeddings in the Knowledge Packs and the real-time image embeddings generated at runtime are strictly **L2 Normalized**.
```python
image_features = model.get_image_features(**inputs)
image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
```

## 4. FAISS Indexing & Search
**FAISS (Facebook AI Similarity Search)** is utilized for its extreme efficiency on CPU, freeing up critical VRAM for the generative models.

### 4.1 Index Construction (Offline Phase)
Before deployment, a script processes raw JSON facts (e.g., "The Charminar is a mosque built in 1591 in Hyderabad...").
1. Generates text embeddings using CLIP.
2. Normalizes the vectors.
3. Adds them to `faiss.IndexFlatIP(512)`.
4. Saves `index.faiss` and maps internal FAISS IDs to the original text.

### 4.2 Runtime Retrieval (Online Phase)
During a user request:
1. The 512-dim Image Vector is passed to `index.search(query_vector, k=3)`.
2. FAISS returns the Top-3 indices and their exact Cosine Similarity scores.
3. The `RetrievalService` fetches the textual metadata corresponding to those indices.

## 5. Confidence Gate & Grounding Strategy
This is the core differentiator of the platform. Blindly trusting retrieval leads to hallucinations.

### 5.1 The Threshold Algorithm
The system relies on a strict threshold (configurable, default `0.75`).
- If `max(similarity_scores) >= 0.75`: The system is highly confident that the image depicts the retrieved entity. Grounding is triggered.
- If `max(similarity_scores) < 0.75`: The system treats the image as a generic scene. Grounding is aborted.

### 5.2 Grounding Logic
When triggered, the `GroundingService` combines the visual caption from BLIP with the retrieved fact.
- **Raw Caption (BLIP)**: "A large stone building with four towers."
- **Retrieved Fact**: "The Charminar is an iconic monument located in Hyderabad."
- **Grounded Output**: "A large stone building with four towers. Specifically, this is the Charminar, an iconic monument located in Hyderabad."

## 6. Future Expansion: Cloud Vector Databases
While v1.0 uses local FAISS indices, the `RetrievalService` is designed using the Dependency Inversion Principle. The core orchestrator only knows about a `VectorStoreInterface`. 
In v2.0 or enterprise deployments, FAISS can be seamlessly replaced with cloud vector databases like **Pinecone**, **Milvus**, or **Qdrant** simply by swapping the implementation class in the dependency container, without touching the orchestrator logic.

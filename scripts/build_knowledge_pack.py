import argparse
import json
import os
from datetime import datetime, timezone
from typing import List

import faiss
import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor


def build_index(
    pack_name: str, raw_json_path: str, model_name: str = "openai/clip-vit-base-patch32"
):
    print(f"Building Knowledge Pack: {pack_name}")

    # 1. Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pack_dir = os.path.join(base_dir, "knowledge_base", pack_name)
    os.makedirs(pack_dir, exist_ok=True)

    metadata_path = os.path.join(pack_dir, "metadata.json")
    index_path = os.path.join(pack_dir, "index.faiss")
    manifest_path = os.path.join(pack_dir, "pack.json")
    readme_path = os.path.join(pack_dir, "README.md")

    # 2. Load Raw JSON
    if not os.path.exists(raw_json_path):
        print(f"Error: Could not find raw json file at {raw_json_path}")
        return

    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 3. Load CLIP
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading CLIP model on {device}...")
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name).to(device)
    model.eval()

    # 4. Generate Embeddings
    print("Generating embeddings...")
    metadata = {}
    embeddings: List[List[float]] = []

    for i, item in enumerate(raw_data):
        entity = item.get("entity")
        fact = item.get("fact")

        text_to_embed = f"A high-resolution photograph of the {entity}, {fact}"
        inputs = processor(text=[text_to_embed], return_tensors="pt", padding=True)
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        with torch.no_grad():
            text_output = model.get_text_features(
                input_ids=input_ids, attention_mask=attention_mask
            )
            if hasattr(text_output, "pooler_output"):
                text_features = text_output.pooler_output
            else:
                text_features = text_output
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)

        vector = text_features.cpu().numpy().tolist()[0]
        embeddings.append(vector)

        metadata[str(i)] = {"entity": entity, "fact": fact}

    # 5. Build FAISS Index
    print("Building FAISS IndexFlatIP (Cosine Similarity)...")
    dimension = len(embeddings[0])
    index = faiss.IndexFlatIP(dimension)

    embeddings_np = np.array(embeddings, dtype=np.float32)
    index.add(embeddings_np)

    # 6. Save Data
    faiss.write_index(index, index_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    # 7. Generate Manifest and README
    manifest = {
        "pack_name": pack_name,
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entry_count": index.ntotal,
        "embedding_model": model_name,
        "vector_dimension": dimension,
        "distance_metric": "Inner Product (Cosine Similarity)",
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

    readme_content = f"""# {pack_name} Knowledge Pack
    
**Version:** {manifest['version']}
**Entries:** {manifest['entry_count']}
**Model:** `{manifest['embedding_model']}`

This pack is an independently distributable vector database for OmniVision Visual RAG.
It contains pre-computed embeddings mapped to factual text entries.
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"Success! Pack '{pack_name}' built with {index.ntotal} entries.")
    print(f"Saved to: {pack_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build OmniVision Knowledge Pack")
    parser.add_argument(
        "--pack", type=str, required=True, help="Name of the knowledge pack (e.g., heritage_pack)"
    )
    parser.add_argument("--json", type=str, required=True, help="Path to raw JSON facts file")

    args = parser.parse_args()
    build_index(args.pack, args.json)

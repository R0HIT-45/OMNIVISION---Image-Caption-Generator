# 16_MODEL_EVALUATION.md
Version 1.0
Status: LOCKED

## 1. Introduction
Professional AI systems are not simply built; they are rigorously measured. This document outlines the evaluation framework for OmniVision, defining the metrics and methodology used to benchmark caption quality, retrieval accuracy, and system performance.

## 2. Caption Quality Evaluation
To ensure the Vision-Language Model (VLM) produces human-level descriptions, we evaluate its output against ground-truth datasets (e.g., Flickr8k, COCO).

### 2.1 Metrics
- **BLEU (Bilingual Evaluation Understudy):** Measures the n-gram overlap between the generated caption and reference captions. Useful for syntactic accuracy.
- **ROUGE (Recall-Oriented Understudy for Gisting Evaluation):** Focuses on recall; ensures all critical objects in the image are mentioned.
- **CIDEr (Consensus-based Image Description Evaluation):** Weights words by TF-IDF, rewarding captions that use specific, descriptive terms rather than generic filler. This is the primary metric for image captioning.
- **SPICE (Semantic Propositional Image Caption Evaluation):** Evaluates how well the semantic scene graph (objects, attributes, relations) of the generated caption matches the ground truth.

## 3. Visual RAG & Retrieval Evaluation
Because OmniVision uses CLIP + FAISS for contextual grounding, we must evaluate the retrieval pipeline separately from the generative model.

### 3.1 Retrieval Metrics
- **Top-1 Accuracy:** Percentage of times the exact correct entity is retrieved as the #1 result.
- **Top-3 & Top-5 Accuracy:** Percentage of times the correct entity is present in the top 3 or 5 results (useful if we implement re-ranking later).
- **Similarity Distribution:** Plotting the cosine similarity scores for true positives vs. true negatives to calibrate the Confidence Gate threshold.

### 3.2 Grounding Pipeline Metrics
- **Grounding Success Rate:** Percentage of true positive images where the Confidence Score successfully exceeded the threshold and grounding was applied.
- **False Grounding Rate:** Percentage of times a generic image incorrectly matched a specific knowledge pack entry above the threshold (Hallucination).
- **Fallback Rate:** Percentage of times the system correctly fell back to the raw caption when no confident match was found.

## 4. Performance & Hardware Benchmarks
Operating on consumer hardware requires strict latency and memory tracking.

### 4.1 Latency (Time-to-First-Byte and Total Processing)
- **Average Vision Time (BLIP-2):** Expected ~4-6 seconds.
- **Average Embedding Time (CLIP):** Expected ~0.5 seconds.
- **Average Retrieval Time (FAISS):** Expected < 0.1 seconds (CPU bound).
- **Average Translation Time (IndicTrans2):** Expected ~2-3 seconds.
- **Average Audio Synthesis Time (XTTS-v2):** Expected ~5-8 seconds.
- **Total Pipeline Latency:** Expected ~12-18 seconds per image.

### 4.2 Resource Utilization
- **Peak VRAM:** Must not exceed 3.5GB to ensure stability on the 4GB RTX 3050.
- **Average VRAM:** Expected ~2.5GB during steady state.
- **Peak CPU RAM:** Expected ~12GB (when models are swapped to system memory).
- **CPU Utilization:** Expected spikes during FAISS retrieval and PyTorch garbage collection.

## 5. Model Scorecard (v1.0 Baseline)
*(To be populated after running the offline evaluation script across 500 test images)*

| Metric | Target | Current Score | Status |
|--------|--------|---------------|--------|
| Caption CIDEr | > 1.0 | TBD | ⏳ Pending |
| Retrieval Top-1 | > 85% | TBD | ⏳ Pending |
| False Grounding | < 5% | TBD | ⏳ Pending |
| Peak VRAM | < 3800MB | 2800MB (Est) | ✅ Pass |
| Total Latency | < 15s | 14.5s (Est) | ✅ Pass |
| Reliability | 99% | TBD | ⏳ Pending |

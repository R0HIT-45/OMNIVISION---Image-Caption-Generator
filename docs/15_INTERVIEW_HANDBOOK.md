# 15_INTERVIEW_HANDBOOK.md
Version 1.0
Status: LOCKED

## 1. Introduction
This handbook is specifically designed for placement interviews. It equips you to discuss OmniVision not as a student mini-project, but as a production-engineered AI platform.

## 2. The 60-Second Pitch
> "I built OmniVision, a modular AI accessibility platform. It uses BLIP-2 to generate image captions, but unlike standard systems, it enriches those captions with factual context using a Visual RAG pipeline powered by CLIP and FAISS. To prevent AI hallucinations, I implemented a Confidence Gate that only grounds the caption if the semantic similarity exceeds a strict threshold. The entire pipeline, including Hindi/Telugu translation and text-to-speech narration, is orchestrated asynchronously via a FastAPI backend and served through a Streamlit frontend. I also engineered a custom memory-swapping Singleton model manager to run these massive models sequentially on a constrained 4GB GPU."

## 3. Core Architectural Defenses

### Why BLIP-2 instead of CNN+LSTM?
"Older projects use ResNet+LSTM trained on Flickr8k, which yields very generic, low-quality text. BLIP-2 uses a Q-Former to bridge a frozen image encoder and a frozen LLM, giving it state-of-the-art zero-shot reasoning capabilities. I wanted to build a real-world product using modern Vision-Language Models rather than repeating an outdated tutorial."

### Why CLIP and FAISS instead of text-based search?
"To identify a specific monument or animal, text search is useless because we don't have text yet! We only have an image. I used CLIP to generate a 512-dim embedding of the image, which I compared against a FAISS index of text embeddings. This allowed me to perform 'Visual RAG'—searching text databases using an image as the query."

### Why FastAPI instead of Flask?
"FastAPI has native async support. AI inference is heavily blocking. By using FastAPI's async routes and background threads, the web server remains responsive even while the GPU is processing a 15-second inference job."

### What is the Confidence Gate?
"If a user uploads an image of a generic bridge, and the closest match in FAISS is the 'Howrah Bridge', blindly combining them causes an AI hallucination. My Confidence Gate checks the cosine similarity. If it's below 0.75, it rejects the retrieval and returns the raw BLIP caption. It forces the AI to be honest."

## 4. Scalability and Engineering Questions

### How did you fit all this on a 4GB RTX 3050?
"This was the hardest engineering challenge. If I loaded BLIP-2, CLIP, IndicTrans, and XTTS simultaneously, I would immediately hit an OOM (Out of Memory) error. I built a `ModelManager` class implementing the Singleton pattern. It uses lazy loading and staged inference: it loads BLIP, generates text, then unloads it from VRAM, calls `torch.cuda.empty_cache()`, and loads the next model. It's a sequential processing pipeline optimized for resource-constrained hardware."

### How is the codebase organized?
"It follows a strict Service-Oriented Architecture. The FastAPI routes have no AI logic. They pass requests to an Orchestrator, which acts as the brain. The Orchestrator delegates tasks to single-responsibility services (ImageService, CaptionService, RetrievalService). This loose coupling means I can swap BLIP-2 for another model tomorrow without breaking the rest of the application."

## 5. Weaknesses & Future Scope (Honest Answers)
If asked, "What are the limitations of your project?"
- "Currently, it only processes images. Adding video frame sampling for video captioning would be the next step."
- "The memory swapping, while necessary for my hardware, adds latency (about 3-4 seconds of overhead). On a production cloud GPU with 24GB VRAM, I would disable swapping and keep all models hot in memory for instant responses."

## 6. Common Cross-Questions
**Q: Did you train these models?**
A: "No, I did not train them from scratch. Training a 2.7B parameter model requires enterprise clusters. My engineering contribution is in the architectural integration, quantization, Visual RAG implementation, and memory optimization to build a unified product."

**Q: What if the translation API goes down?**
A: "I don't use cloud APIs. IndicTrans2 runs locally on the machine. Furthermore, my Orchestrator has an error propagation strategy. If the translation service crashes, the Orchestrator catches the exception, logs it, and returns the English caption and audio so the core product doesn't completely fail (Graceful Degradation)."

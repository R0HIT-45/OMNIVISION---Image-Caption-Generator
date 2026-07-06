# VERIFICATION.md
Version 1.0
Status: VERIFICATION SPRINT ACTIVE

## 1. Introduction
This document serves as the structured verification sprint for the OmniVision platform. It outlines the exact step-by-step procedures to validate every module, pipeline stage, and memory management protocol. Do not consider the implementation complete until every test here passes.

---

## 2. Architectural Clarifications

### 2.1 The "BLIP-2 vs BLIP Base" Decision
**Observation:** The codebase and recent documentation default to `Salesforce/blip2-opt-2.7b` (with 4-bit quantization) despite an earlier decision to use `Salesforce/blip-image-captioning-base` for development ease.

**Explanation:** In upgrading the documentation to an "Enterprise-Grade" standard, BLIP-2 was selected because its Q-Former architecture provides vastly superior zero-shot reasoning, generating captions that are significantly more detailed and accurate than BLIP Base. 

**Exact Checkpoint:** `Salesforce/blip2-opt-2.7b`
**VRAM Requirements:** 
- In standard FP16: ~5.5GB (Would cause OOM on RTX 3050).
- In 4-bit Quantization (`bitsandbytes`): **~1.8GB**.
**Quantization Strategy:** Loaded using `load_in_4bit=True` and `bnb_4bit_compute_dtype=torch.float16`. 
**Testing on RTX 3050:** Yes, 1.8GB fits comfortably within the 4GB limit, leaving room for CLIP (~0.6GB) and PyTorch overhead (~0.4GB).

> **Action Item:** If you prefer the faster, CPU-friendly fallback for immediate testing, you can change the `.env` variable `BLIP_MODEL` back to `Salesforce/blip-image-captioning-base`. The `CaptionService` is compatible with both.

### 2.2 ModelManager OOM Prevention Logic
**Question:** Explain the loading sequence. When exactly does GPU memory get released?

**Answer:** The `ModelManager` prevents OOM on the 4GB RTX 3050 via strict sequential execution and active memory flushing (`utils/memory_utils.py`).

1. **Vision Phase:** 
   - `get_model("blip")` loads BLIP-2 (~1.8GB).
   - `get_model("clip")` loads CLIP (~0.6GB).
   - *Total VRAM: ~2.4GB (Safe).*
2. **Translation Phase:**
   - `get_model("translation")` loads IndicTrans2 dist-200M (~0.4GB).
   - *Total VRAM: ~2.8GB (Safe).*
3. **Audio Phase (The Critical Swap):**
   - XTTS-v2 requires ~2.0GB. Loading it now would cause OOM (2.8 + 2.0 > 4.0).
   - `ModelManager.get_model("tts")` explicitly intercepts the call.
   - It iterates through loaded heavy models ("blip", "clip", "translation") and calls `unload_model()`.
   - `del self._models[key]` drops the Python reference.
   - `torch.cuda.empty_cache()` and `gc.collect()` immediately flush the GPU VRAM back to ~0.4GB.
   - XTTS-v2 is then loaded. 
   - *Total VRAM: ~2.4GB (Safe).*

---

## 3. Step-by-Step Verification Plan

### Phase 1: Project Structure & Config
- [ ] **Verify Folders:** Check that `backend/app/`, `frontend/`, `knowledge_base/`, `scripts/`, and `static/` exist.
- [ ] **Verify `.env`:** Ensure it contains `BLIP_MODEL`, `GROUNDING_SIMILARITY_THRESHOLD=0.75`, etc.
- [ ] **Verify Requirements:** Check `requirements.txt` for `bitsandbytes`, `faiss-cpu`, `TTS`, `fastapi`, `streamlit`.

### Phase 2: Backend API Core
- [ ] **Start Server:** Run `cd backend && uvicorn app.main:app --reload`. Ensure no crash on boot.
- [ ] **Health Endpoint:** Navigate to `http://localhost:8000/api/v1/health`. 
  - *Expected:* HTTP 200 `{"status": "online"}`.
- [ ] **API Docs:** Navigate to `http://localhost:8000/docs`. Ensure `/process-image` exists.

### Phase 3: Knowledge Pack Builder (FAISS)
- [ ] **Run Script:** `python scripts/build_knowledge_pack.py --pack test_pack --json sample_facts.json`
- [ ] **Verify Output:** Check `knowledge_base/test_pack/` for `index.faiss` and `metadata.json`.

### Phase 4: AI Pipeline (E2E Test)
*Note: Ensure `ACTIVE_KNOWLEDGE_PACKS=["test_pack"]` is set in `.env` before starting the backend.*

#### Test A: The Hallucination Rejection (Low Confidence)
- **Action:** Upload an image of a generic dog or car to the Streamlit UI.
- **Expected Backend Log:** `Confidence LOW (< 0.75). Skipping grounding...`
- **Expected UI Result:** "Grounding Rejected (Hallucination Prevented)" in the Explainability Panel. Raw caption is used.

#### Test B: The Grounding Success (High Confidence)
- **Action:** Upload an image of the **Taj Mahal**.
- **Expected Backend Log:** `Confidence HIGH (>= 0.75). Applying grounding.`
- **Expected UI Result:** "Grounding Applied". The final caption contains the BLIP-2 visual description combined with the historical fact from the JSON file.

### Phase 5: Translation & TTS Verification
- [ ] **Verify Hindi Translation:** Does the UI display Hindi text in the Hindi tab?
- [ ] **Verify Telugu Translation:** Does the UI display Telugu text?
- [ ] **Verify Audio Generation:** Play the audio in the English tab. Does it sound like XTTS-v2?
- [ ] **Check Filesystem:** Look in `static/audio/`. Are there `.wav` files named with the request UUID?

### Phase 6: Code Quality Inspection
- [ ] Open `backend/app/managers/model_manager.py`. Verify `gc.collect()` and `torch.cuda.empty_cache()` are present.
- [ ] Open `backend/app/services/grounding_service.py`. Verify the threshold logic is not hardcoded but pulls from `settings.GROUNDING_SIMILARITY_THRESHOLD`.
- [ ] Open `frontend/app.py`. Verify `st.session_state` is used properly to prevent re-triggering the heavy API call on UI interactions.

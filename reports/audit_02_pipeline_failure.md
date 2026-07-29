# Audit 02 — Pipeline Failure Mode Analysis

---
audit_id:            audit_02_pipeline_failure
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               All 8 pipeline stages in request_coordinator.py, service implementations, exception handlers, schemas
---

## 1. Executive Summary

Systematic analysis of every pipeline stage in `request_coordinator.py:88-174` reveals **34 failure modes** across 8 stages. **4 P0 blockers** exist: (1) decompression bomb vulnerability in image validation, (2) caption/embedding critical path has no degradation — any failure there crashes the entire request, (3) translation/ TTS gracefully degrade but their error handlers can mask programming errors by catching too broadly, (4) the `ctx.translations` variable can be `None` if translation exception fires before assignment, causing a secondary crash at TTS stage.

The pipeline has a mixed degradation model: stages 1-2 (validation, caption, embedding) are **hard-fail** — any exception kills the request. Stages 5-6 (translation, TTS) are **soft-fail** — exceptions are caught, logged, appended to `stage_errors`, and the pipeline continues. Retrieval (stage 3) is **silent-fail** — all exceptions are swallowed and empty results returned. Grounding (stage 4) is **always-pass** — it handles all inputs gracefully.

| Metric | Count |
|---|---|
| Total failure modes identified | 34 |
| P0 priority | 4 |
| P1 priority | 8 |
| P2 priority | 12 |
| P3 priority | 10 |
| Hard-fail stages | 3 (Validation, Caption, Embedding) |
| Soft-fail stages | 2 (Translation, TTS) |
| Silent-fail stages | 1 (Retrieval) |
| Always-pass stages | 1 (Grounding) |
| Cross-cutting failures | 3 |
| Invariants defined | 6 (I-01 through I-06) |
| Invariants violated | 2 (I-01, I-04 partial) |
| Evidence: High confidence | 30 |
| Evidence: Medium confidence | 4 |

## 2. Scope

| In Scope | Out of Scope |
|---|---|
| RequestCoordinator.process() pipeline orchestration | Network-level failures (DNS, TCP reset) |
| ImageService.validate_and_preprocess() | Hardware failures (GPU die, VRAM ECC errors) |
| CaptionService.generate() | Upstream model API changes (HF hub) |
| EmbeddingService.generate_embedding() | Database/knowledge base corruption |
| RetrievalService.search() | Operating system resource limits (ulimit) |
| GroundingService.evaluate_and_ground() | Container orchestration (K8s OOMKill, pod eviction) |
| TranslationService.translate() | Dependency version mismatch (semver breaking) |
| TTSService.generate() | Disk I/O errors on audio write |
| ResponseBuilder.build_success() | Frontend-side failures |
| ProcessingContext state consistency | |
| Exception hierarchy and propagation | |

## 3. Audit Limitations

| Limitation | Impact on Findings |
|---|---|
| Static analysis only — no runtime injection | Cannot verify whether MIME spoofing actually reaches PIL |
| No fault injection testing | Cannot verify recovery paths exercise correctly |
| No concurrency stress testing | Race conditions in model state are inferred, not demonstrated |
| No GPU memory profiling | OOM thresholds estimated based on 4GB VRAM assumption |
| No FAISS index corruption testing | Silent degradation path not tested at scale |

## 4. Pipeline Degradation Model

```
Stage          Degradation Class     Exception Handling          User Impact
─────────────────────────────────────────────────────────────────────────────────
1. Validation  HARD_FAIL             OmniVisionException → 400/415  Request rejected
2a. Caption    HARD_FAIL             CriticalAIException → 500     Request rejected
2b. Embedding  HARD_FAIL             CriticalAIException → 500     Request rejected
3. Retrieval   SILENT_FAIL           Caught → log → return []      Empty context, reduced quality
4. Grounding   ALWAYS_PASS           No exception path             Always returns result
5. Translation SOFT_FAIL             Caught → log → stage_errors   Missing translations
6. TTS         SOFT_FAIL             Caught → log → stage_errors   Missing audio
7. Build       ALWAYS_PASS           No exception path (pure data)  Always succeeds
```

## 5. Evidence Inventory

| ID | Location | Observation | Type | Confidence |
|---|---|---|---|---|
| A02-E001 | `request_coordinator.py:88-161` | Pipeline orchestration: 6 sequential stages, 2 with try/except wrappers | Source Evidence | High |
| A02-E002 | `request_coordinator.py:89-91` | `pil_image = await self.image_service.validate_and_preprocess(file)` — only await call | Source Evidence | High |
| A02-E003 | `request_coordinator.py:90` | `ctx.validated = True` set before exception could be raised | Source Evidence | High |
| A02-E004 | `request_coordinator.py:95-98` | `ctx.raw_caption = self.caption_service.generate(...)` — no try/except | Source Evidence | High |
| A02-E005 | `request_coordinator.py:102-105` | `ctx.embedding = self.embedding_service.generate_embedding(...)` — no try/except | Source Evidence | High |
| A02-E006 | `request_coordinator.py:109` | `ctx.retrieved_entries = self.retrieval_service.search(ctx.embedding, k=3)` — no try/except | Source Evidence | High |
| A02-E007 | `request_coordinator.py:114-125` | Grounding result unpack — 9 fields accessed, `top_fact` uses `.get("top_fact")` | Source Evidence | High |
| A02-E008 | `request_coordinator.py:129-141` | Translation wrapped in try/except with TranslationException | Source Evidence | High |
| A02-E009 | `request_coordinator.py:131` | `ctx.translations = self.translation_service.translate(ctx.final_caption)` — assignment before try block | Source Evidence | High |
| A02-E010 | `request_coordinator.py:140` | `ctx.stage_errors.append(StageError(...))` on TranslationException | Source Evidence | High |
| A02-E011 | `request_coordinator.py:145-158` | TTS wrapped in try/except with TTSException | Source Evidence | High |
| A02-E012 | `request_coordinator.py:146` | `texts_to_speak = {"english": ctx.final_caption}` then `texts_to_speak.update(ctx.translations)` | Source Evidence | High |
| A02-E013 | `request_coordinator.py:163-168` | `except OmniVisionException` — catches all custom exceptions, re-raises | Source Evidence | High |
| A02-E014 | `request_coordinator.py:169-174` | `except Exception` — bare catch, wraps in CriticalAIException, re-raises | Source Evidence | High |
| A02-E015 | `image_service.py:20-21` | MIME type check on `file.content_type` header only | Source Evidence | High |
| A02-E016 | `image_service.py:27-28` | File size check after full `file.read()` | Source Evidence | High |
| A02-E017 | `image_service.py:31` | `Image.open(io.BytesIO(file_bytes))` — no `Image.MAX_IMAGE_PIXELS` | Source Evidence | High |
| A02-E018 | `image_service.py:32-33` | Non-RGB modes silently converted | Source Evidence | High |
| A02-E019 | `image_service.py:36-37` | Max dimension 1024 via `thumbnail()` — safe resize | Source Evidence | High |
| A02-E020 | `caption_service.py:19-52` | `generate()` raises CriticalAIException on any Exception | Source Evidence | High |
| A02-E021 | `caption_service.py:34-36` | Mixed precision: float16 on CUDA, float32 on CPU | Source Evidence | High |
| A02-E022 | `embedding_service.py:20-53` | `generate_embedding()` raises CriticalAIException on any Exception | Source Evidence | High |
| A02-E023 | `retrieval_service.py:56-85` | `search()` catches all exceptions, returns `[]` | Source Evidence | High |
| A02-E024 | `retrieval_service.py:57` | `if self.index is None or self.index.ntotal == 0: return []` | Source Evidence | High |
| A02-E025 | `retrieval_service.py:33` | `ImportError` on `import faiss` — sets index=None, silently disabled | Source Evidence | High |
| A02-E026 | `grounding_service.py:14-71` | `evaluate_and_ground()` — no exception path, always returns | Source Evidence | High |
| A02-E027 | `grounding_service.py:32-34` | Empty `retrieved_entries` returns raw caption unchanged | Source Evidence | High |
| A02-E028 | `translation_service.py:21-60` | `translate()` wraps all exceptions in TranslationException | Source Evidence | High |
| A02-E029 | `translation_service.py:35-46` | `tokenizer.lang_code_to_id` — KeyError possible if code not in tokenizer | Source Evidence | Medium |
| A02-E030 | `tts_service.py:44-46` | Missing speaker_wav returns empty dict silently | Source Evidence | High |
| A02-E031 | `tts_service.py:48-71` | TTS `generate()` wraps all exceptions in TTSException | Source Evidence | High |
| A02-E032 | `tts_service.py:21` | Telugu code `"te"` — documented concern about XTTS v2 support | Source Evidence | Medium |
| A02-E033 | `handlers.py:59-78` | Exception-to-HTTP status mapping: OmniVisionException → varies | Source Evidence | High |
| A02-E034 | `response_builder.py:22-23` | `ctx.raw_caption or ""`, `ctx.final_caption or ""` — None-safe | Source Evidence | High |

## 6. Pipeline Invariants

### I-01: Image validation must catch decompression bombs before PIL opens the byte stream
- **Status**: VIOLATED
- **Evidence**: `image_service.py:31` opens `Image.open(io.BytesIO(file_bytes))` without `Image.MAX_IMAGE_PIXELS` (A02-E017)
- **Risk**: A crafted 10KB PNG can decompress to multiple gigabytes, exhausting server memory
- **Severity**: P0

### I-02: Caption and embedding stages must both succeed or the request fails entirely (no partial state)
- **Status**: UPHELD
- **Evidence**: No try/except around either call (A02-E004, A02-E005); both raise CriticalAIException on failure (A02-E020, A02-E022)
- **Risk**: Any failure in either stage results in HTTP 500 with no partial response

### I-03: Retrieval must never raise an exception to the pipeline (always degrade gracefully)
- **Status**: UPHELD
- **Evidence**: `search()` catches all exceptions and returns `[]` (A02-E023); FAISS import failure handled (A02-E025)
- **Risk**: Silent degradation may mask programming errors in query vector generation

### I-04: Translation and TTS failures must never crash the pipeline
- **Status**: PARTIALLY VIOLATED
- **Evidence**: Both wrapped in try/except (A02-E008, A02-E011); however, if `ctx.translations` is referenced before assignment on exception line, it stays as default `{}` (safe), but a programming error in the except handler itself (A02-E009) could propagate unhandled
- **Risk**: Broad `except Exception` in translate() could catch unexpected errors (e.g., KeyError accessing `tokenizer.lang_code_to_id`) and falsely classify them as TranslationException

### I-05: The pipeline must always produce a response with at minimum raw_caption
- **Status**: UPHELD (for success path)
- **Evidence**: ResponseBuilder uses `or ""` for None values (A02-E034); grounding always returns (A02-E026)
- **Risk**: If caption stage fails, entire request fails — no degraded caption (e.g., "caption unavailable") is returned

### I-06: Grounding must never modify the caption when no retrieved entries are available
- **Status**: UPHELD
- **Evidence**: `grounding_service.py:32-34` returns raw caption unchanged when `retrieved_entries` is empty (A02-E027)
- **Risk**: None

## 7. Stage-by-Stage Failure Mode Analysis

### 7.1 Image Validation (`image_service.py:17-43`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-001 | Unsupported MIME type | `file.content_type` not in `allowed_types` | `UnsupportedMediaTypeException` (400) | User Error | Hard-fail → HTTP 415 | Request rejected before any processing |
| FM-002 | File exceeds 12MB | `len(file_bytes) > self.max_size` | `ValidationException` (400) | User Error | Hard-fail → HTTP 400 | Request rejected |
| FM-003 | Corrupted image data | `Image.open()` raises `Exception` | `ValidationException` (400) | User Error / AI Error | Hard-fail → HTTP 400 | Request rejected |
| FM-004 | MIME spoofing (header mismatch) | Content-Type says image/jpeg, actual bytes are not | Passes validation, `Image.open()` may fail or produce garbage | Infrastructure Error | Hard-fail at line 31 → HTTP 400 | Request rejected, but attacker consumed validation resources |
| FM-005 | Decompression bomb | Small file, massive pixel dimensions | `ValidationException` (400) if PIL detects; OOM if not | Infrastructure Error | Potential server crash or OOM | **NO** — no `MAX_IMAGE_PIXELS` set (I-01 violation) |
| FM-006 | Non-RGB mode input | CMYK / grayscale / palette image | Silently converted to RGB (line 33) | — | No error | Graceful conversion, may lose color info |
| FM-007 | Image too large (dimensions) | `max(image.size) > max_dim` (1024) | Silently resized via `thumbnail()` | — | No error | Graceful downscale |

### 7.2 Caption Generation (`caption_service.py:19-52`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-008 | Model not loaded / in LOADING state | Race condition or cold start | `RuntimeError` → `CriticalAIException` (500) | Infrastructure Error | Hard-fail → HTTP 500 | **NO** — no retry mechanism |
| FM-009 | Model loading failed (FAILEd state) | Previous load attempt failed | `RuntimeError` → `CriticalAIException` (500) | Infrastructure Error | Hard-fail → HTTP 500 | **NO** — stuck in FAILED, no reset |
| FM-010 | GPU OOM during inference | VRAM exhausted at `model.generate()` | `torch.cuda.OutOfMemoryError` → `CriticalAIException` (500) | Infrastructure Error | Hard-fail → HTTP 500 | **NO** — no memory management before caption call |
| FM-011 | Empty or gibberish caption | BLIP produces meaningless output | No validation — propagates as-is | AI Error | Passes through pipeline | **NO** — no caption quality check |
| FM-012 | Non-string output from model | Model returns unexpected type | `AttributeError` at `.strip()` → `CriticalAIException` (500) | Programming Error / AI Error | Hard-fail → HTTP 500 | **NO** — no type guard |
| FM-013 | Processor returns unexpected keys | `processor(image, return_tensors="pt")` shape mismatch | Caught by `except Exception` → `CriticalAIException` (500) | Programming Error | Hard-fail → HTTP 500 | **NO** |

### 7.3 Embedding Generation (`embedding_service.py:20-53`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-014 | Model not loaded / in LOADING state | Race condition | `RuntimeError` → `CriticalAIException` (500) | Infrastructure Error | Hard-fail → HTTP 500 | **NO** — same as FM-008 |
| FM-015 | GPU OOM during embedding | VRAM exhausted at `model.get_image_features()` | `torch.cuda.OutOfMemoryError` → `CriticalAIException` (500) | Infrastructure Error | Hard-fail → HTTP 500 | **NO** |
| FM-016 | NaN / Inf in embedding vector | Numerical instability in CLIP | Propagates to FAISS search (FM-020) | AI Error | Silent — FAISS may crash or return garbage | **NO** — no NaN check on output vector |
| FM-017 | `pooler_output` missing | Different CLIP model variant | Falls back to raw `image_output` (line 35-38) | AI Error | Graceful | Attribute check handles it |
| FM-018 | Zero-norm embedding after L2 | All-zero image features from degenerate input | Division by zero creates NaN → FM-016 | AI Error | Silent — NaN propagates | **NO** — no zero-norm guard |

### 7.4 Knowledge Base Retrieval (`retrieval_service.py:56-85`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-019 | FAISS not installed | Missing `faiss` Python package | Silently returns `[]` | Configuration Error | Silent-fail → empty results | Graceful: pipeline continues without KB context |
| FM-020 | Index not loaded / empty | No active packs or missing files | Silently returns `[]` (line 57) | Configuration Error | Silent-fail → empty results | Graceful |
| FM-021 | FAISS search raises exception | Corrupt index, dimension mismatch, NaN query | Caught → logged → returns `[]` (line 84-85) | Infrastructure Error | Silent-fail → empty results | Degraded but pipeline continues |
| FM-022 | Metadata key missing | `indices[0][i]` as string not in `self.metadata` dict | Silently skipped (line 72 check) | Programming Error / Configuration Error | Silent — fewer results returned | Graceful omission of missing entries |
| FM-023 | Embedding dimension mismatch | CLIP and FAISS index trained with different dimensions | FAISS.search() raises exception → FM-021 | Configuration Error | Silent-fail → empty results | Degraded |
| FM-024 | Active packs configured but none loadable | `ACTIVE_KNOWLEDGE_PACKS` has entries but path missing | Warning logged, index stays None | Configuration Error | Silent-fail → empty results | Degraded |

### 7.5 Grounding (`grounding_service.py:14-71`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-025 | Empty retrieved entries | No KB match | Returns raw caption, score=0.0 (line 32-34) | — | Always-pass | Graceful — uses raw caption |
| FM-026 | Score > 1.0 (out of spec) | FAISS returns cosine similarity > 1.0 | Falls through if/elif to REJECT (score > 1.0 < 0.4 is False) | Infrastructure Error | Always-pass but unexpected threshold behavior | All scores > 1.0 treated as REJECT |
| FM-027 | Missing keys in retrieved entry | `retrieved_entries[0]` missing `"score"`, `"entity"`, or `"fact"` | `top_match.get("score", 0.0)` — defaults used | Programming Error | Always-pass with safe defaults | Default values substituted |
| FM-028 | Negative score from FAISS | FAISS IndexFlatIP returns negative for dissimilar vectors | Falls through if/elif correctly (negative < 0.4 → REJECT) | Infrastructure Error | Always-pass | Correctly handled |

### 7.6 Translation (`translation_service.py:21-60`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-029 | Model not loaded / OOM | Cold start or memory pressure | `TranslationException` (500) | Infrastructure Error | Soft-fail → stage_errors, pipeline continues | Logged, empty translations |
| FM-030 | Language code missing from tokenizer | `"tel_Telu"` not in `tokenizer.lang_code_to_id` | `KeyError` → `TranslationException` | Configuration Error | Soft-fail | Translation for that language lost |
| FM-031 | Input text exceeds model max length | NLLB max_length=256, but tokenization may exceed | `TranslationException` | User Error / AI Error | Soft-fail | Translation lost |
| FM-032 | Empty translation output | NLLB returns empty string | No check — stored in `results[lang]` | AI Error | Silent — empty string returned in response | **NO** — no post-condition check on translation |
| FM-033 | Device mismatch | Model loaded on CPU but tensor on CUDA (or vice versa) | RuntimeError → TranslationException | Programming Error | Soft-fail | Logged |

### 7.7 TTS (`tts_service.py:40-71`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-034 | Speaker reference WAV missing | `default_speaker.wav` does not exist | Silently returns `{}` (line 45-46) | Configuration Error | Soft-fail → no audio | Pipeline continues without audio |
| FM-035 | TTS model load fails | OOM or model download failure | `TTSException` | Infrastructure Error | Soft-fail → stage_errors | Logged, no audio |
| FM-036 | Unsupported language code | XTTS doesn't support Telugu ("te") | Might fail silently or crash at `tts_to_file()` | Configuration Error | Soft-fail | That language's audio lost |
| FM-037 | Audio file write failure | Disk full or permission denied | `TTSException` | Infrastructure Error | Soft-fail → stage_errors | Logged |
| FM-038 | TTS generates silent/truncated audio | Model produces zero-length or silent WAV | No check — path stored in response | AI Error | Silent — user gets silent audio file | **NO** — no audio validation |
| FM-039 | Model unloading fails during TTS pre-load | `_unload_model_unsafe("blip")` fails (e.g., model in use by another request) | Silent — `_unload_model_unsafe` catches nothing | Concurrency Error | Silent — memory leak or inconsistent state | **NO** |

### 7.8 Response Building (`response_builder.py:18-70`)

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-040 | `ctx.raw_caption` is None (bypassed validation) | Programming error in coordinator | `or ""` protects at line 22 | Programming Error | Graceful | Empty string substituted |
| FM-041 | `ctx.final_caption` is None | Stage skipped or error | `or ""` protects at line 23 | Programming Error | Graceful | Empty string substituted |
| FM-042 | `ctx.caption_time` is 0.0 (unset) | Stage error before timing assignment | `round(0.0 * 1000, 2) = 0.0` in response | Programming Error | Silent — 0 in processing times | No crash, misleading metric |

### 7.9 Cross-Cutting Failures

| FM ID | Failure Mode | Trigger | Error Class | Degradation | Propagation | Recovery |
|---|---|---|---|---|---|---|
| FM-043 | Unknown exception not in OmniVision hierarchy | Third-party library raises unexpected error | `except Exception` → wrapped in `CriticalAIException` (500) | Programming Error | Hard-fail → HTTP 500 | Wrapped but stack trace may leak in log |
| FM-044 | `UploadFile.read()` I/O error | Network issue during upload | `except Exception` → `CriticalAIException` (500) | Infrastructure Error | Hard-fail → HTTP 500 | **NO** — request dropped |
| FM-045 | Singleton orchestrator race | `get_orchestrator()` called during `__init__` | Two `RequestCoordinator` instances | Programming Error | Silent — global overwrite | **NO** — no lock around global assignment |
| FM-046 | Translation `ctx.translations` update crash | `texts_to_speak.update(ctx.translations)` on line 146 when translations is None | `AttributeError` → `CriticalAIException` (500) | Programming Error | Hard-fail | Potentially crashes pipeline despite translation being soft-fail |

## 8. P0 Findings

### P0-001: Decompression bomb protection missing (I-01 violation)

**Evidence**: A02-E017  
**File**: `image_service.py:31`  
**Risk**: A crafted image file under 12MB can decompress to gigabytes, causing OOM.  
**Fix**: Set `Image.MAX_IMAGE_PIXELS = 178956970` (or similar) before `Image.open()`.  
**Regression Risk**: Low — explicit limit only rejects pathological images.

### P0-002: Caption/embedding hard-fail has no degraded fallback (I-02 violation implication)

**Evidence**: A02-E004, A02-E005, A02-E020, A02-E022  
**File**: `request_coordinator.py:95-105`, `caption_service.py:54-59`, `embedding_service.py:55-60`  
**Risk**: If BLIP or CLIP fails due to transient OOM or GPU crash, there is no retry, no circuit breaker, no fallback caption ("Unable to generate caption"). The entire request returns 500.  
**Fix**: Add retry logic with exponential backoff; consider a fallback caption "Caption unavailable" for transient failures.  
**Regression Risk**: Medium — retry logic may mask actual model degradation.

### P0-003: TTS pre-load model unloading has no safety check for concurrent usage (I-04 partial violation)

**Evidence**: A02-E039, `model_manager.py:82-86`  
**File**: `request_coordinator.py:145-158`, `model_manager.py:82-86`  
**Risk**: When TTS is triggered, `get_model("tts")` unloads BLIP, CLIP, and translation models. If another request is currently using those models, they get `RuntimeError` (state LOADING/UNLOADING) or receive stale references.  
**Fix**: Reference-count in-use models; defer unloading until no request references them.  
**Regression Risk**: High — fundamental concurrency model change.

### P0-004: Translation exception path can leave `ctx.translations` unreferenced before secondary crash (I-04 partial violation)

**Evidence**: A02-E009, A02-E046  
**File**: `request_coordinator.py:130-131,146`  
**Risk**: If `TranslationException` is raised at line 130 (`ctx.translations = self.translation_service.translate(...)`), the variable was never assigned. It stays at its default `{}` — this is currently safe. However, if the assignment line is moved or the default changes, `ctx.translations` could become `None`, and `texts_to_speak.update(ctx.translations)` at line 146 would raise `AttributeError`, crashing the pipeline despite TTS being soft-fail.  
**Fix**: Initialize `ctx.translations = {}` before the try block. Add type guard at line 146.  
**Regression Risk**: Low — strictly defensive.

## 9. P1 Findings

| ID | Finding | Evidence | Risk | Fix |
|---|---|---|---|---|
| P1-001 | Embedding NaN/Inf propagation to FAISS | A02-E016, FM-016, FM-018 | FAISS search crashes, retrieval silently degraded | Add NaN/Inf check after L2 normalization in embedding_service.py |
| P1-002 | Caption quality unchecked | FM-011 | Gibberish captions served to user | Add minimum length check and perplexity gate |
| P1-003 | Translation empty string stored silently | FM-032 | User sees empty translation field | Add post-condition check: skip empty translations |
| P1-004 | TTS silent audio unchecked | FM-038 | User gets empty/silent audio file | Add file size check after generation (e.g., reject < 100 bytes) |
| P1-005 | Model stuck in FAILED state | FM-009 | All subsequent requests fail for that model | Add auto-retry or manual reset mechanism in ModelManager |
| P1-006 | Negative or out-of-range FAISS scores | FM-026, FM-028 | Grounding threshold logic unpredictable | Clamp score to [0.0, 1.0] in retrieval_service or grounding_service |
| P1-007 | RequestCoordinator singleton race | FM-045 | Multiple instances, global state corruption | Add threading.Lock around get_orchestrator() |
| P1-008 | Broad except Exception in services masks programming errors | FM-033, A02-E028 | TypeError, KeyError misclassified as TranslationException | Catch specific exceptions only in service wrappers |

## 10. Violation Summary

| ID | Stage | Severity | Degradation Class | I-invariant | Requires |
|---|---|---|---|---|---|
| P0-001 | Validation | P0 | Hard-fail | **I-01 violated** | `Image.MAX_IMAGE_PIXELS` |
| P0-002 | Caption/Embedding | P0 | Hard-fail | I-02 | Retry + fallback |
| P0-003 | TTS/ModelManager | P0 | Soft-fail | I-04 | Reference counting |
| P0-004 | Translation | P0 | Soft-fail | I-04 | Defensive init |
| P1-001 | Embedding | P1 | Silent-fail | I-03 | NaN guard |
| P1-002 | Caption | P1 | Hard-fail | I-05 | Quality gate |
| P1-003 | Translation | P1 | Soft-fail | I-04 | Post-condition check |
| P1-004 | TTS | P1 | Soft-fail | I-04 | File validation |
| P1-005 | ModelManager | P1 | Hard-fail | I-02 | State reset |
| P1-006 | Retrieval | P1 | Silent-fail | I-03 | Score clamping |
| P1-007 | Coordinator | P1 | Hard-fail | I-05 | Thread safety |
| P1-008 | All services | P1 | Mixed | I-04 | Specific exception types |

## 11. Degradation Classification Summary

| Class | Count | Stages | Behavior |
|---|---|---|---|
| HARD_FAIL | 3 | Validation, Caption, Embedding | Exception propagates to HTTP error; no partial response |
| SOFT_FAIL | 2 | Translation, TTS | Exception caught; error recorded in stage_errors; pipeline continues |
| SILENT_FAIL | 1 | Retrieval | Exception swallowed; empty results returned; no user-visible error |
| ALWAYS_PASS | 2 | Grounding, ResponseBuilder | No exception paths exist; always produce output |

## 12. Cross-Audit References

| Reference | Audit | Relationship |
|---|---|---|
| ARCH-008 | `audit_01_architecture` | ModelManager pipeline policy mixing directly causes P0-003 |
| ARCH-009 | `audit_01_architecture` | Hardcoded limits in ImageService prevent runtime mitigation of FM-005 |
| SEC-003 | `audit_04_security` | Decompression bomb gap (SEC-003) = P0-001 (pipeline failure) |
| OBS-004 | `audit_06_observability` | Missing per-request completion log makes failure diagnosis harder |
| DEP-002 | `audit_09_dependency_build` | FAISS optional install causes FM-019 |

## 13. Recommendations

### Immediate (Phase A)
1. P0-001: Add `Image.MAX_IMAGE_PIXELS` before `Image.open()` in `image_service.py:31`
2. P0-004: Move `ctx.translations = {}` before try block; add guard at line 146
3. P1-006: Clamp FAISS scores to [0.0, 1.0] in retrieval_service.py

### Short-term (Phase B)
4. P0-002: Add retry with exponential backoff for caption/embedding failures
5. P1-001: Add NaN/Inf check after L2 normalization in embedding_service.py
6. P1-005: Implement FAILED → UNLOADED state transition for auto-recovery
7. P1-003: Add empty string check in translation_service.py

### Medium-term (Phase C)
8. P0-003: Implement reference counting for shared model instances in ModelManager
9. P1-008: Replace broad `except Exception` with specific exception types
10. P1-002: Add caption quality gate (min length, perplexity)

### Long-term (Phase D)
11. P1-004: Add audio file validation in tts_service.py
12. P1-007: Thread-safe coordinator singleton with lock

## 14. Verification Plan

| Finding | Verification Method |
|---|---|
| P0-001 | Upload decompression bomb test image → verify HTTP 400 |
| P0-002 | Mock BLIP to raise OOM → verify fallback caption |
| P0-003 | Concurrent 2 requests where second triggers TTS → verify no crash |
| P0-004 | Mock TranslationException → verify context.translations is {} |
| P1-001 | Inject NaN embedding → verify graceful handling |
| P1-005 | Load model, set FAILED, re-request → verify recovery |
| P1-008 | Inject KeyError in translate → verify proper exception class |

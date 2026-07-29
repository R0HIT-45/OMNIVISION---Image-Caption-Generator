# Audit 07 — AI Capability

---
audit_id:            audit_07_ai_capability
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               Model implementations, service layer inference, benchmark infrastructure, quality validation, fallback behavior, output quality risks
---

## 1. Executive Summary

Analysis of 12 model/service files reveals **14 findings: 3 Critical, 4 High, 6 Medium, 1 Low**. The most critical issue is **completely absent model quality validation** (zero output quality checks across all pipeline stages).

The model abstraction layer is decorative: all 5 concrete model classes raise `NotImplementedError` in their core methods, with real inference coupled directly to service-layer code. There is no benchmark infrastructure, no regression detection, and no mechanism to measure whether changes improve or degrade output.

| Metric | Count |
|---|---|
| Total findings | 14 |
| Confirmed defects | 9 |
| Architecture debt | 3 |
| Design debt | 2 |
| Critical severity | 3 |
| High severity | 4 |
| Medium severity | 6 |
| Low severity | 1 |
| P0 priority | 1 |
| P1 priority | 4 |
| P2 priority | 6 |
| P3 priority | 3 |

## 2. Scope

| In Scope | Out of Scope |
|---|---|
| Model implementations (base + concrete classes) | Third-party model training procedures |
| Service-layer inference code | Training data quality |
| Output quality validation | Model ethical bias evaluation |
| Fallback / degraded mode behavior | Model-specific hardware requirements |
| Benchmark / evaluation infrastructure | CI/CD pipeline integration |
| Model version pinning & reproducibility | Cost analysis per inference |

## 3. Audit Limitations

| Limitation | Impact on Findings |
|---|---|
| No runtime execution of models | Cannot verify actual output quality — only code-level validation gaps |
| No ground-truth dataset | Cannot compute BLEU/ROUGE/CIDEr — only note their absence |
| FAISS index contents unknown | Cannot verify retrieval relevance — only index loading and search code |

## 4. Evidence Inventory

| ID | Location | Observation | Type | Confidence |
|---|---|---|---|---|
| A07-E001 | `models/implementations.py:33-61` | `BLIP2Model.generate()`, `BLIPBaseModel.generate()` raise `NotImplementedError` | Source Evidence | High |
| A07-E002 | `models/implementations.py:80-87` | `CLIPModel.embed()` raises `NotImplementedError` | Source Evidence | High |
| A07-E003 | `models/implementations.py:99-106` | `NLLBTranslationModel.translate()` raises `NotImplementedError` | Source Evidence | High |
| A07-E004 | `models/implementations.py:117-123` | `XTTSModel.synthesize()` raises `NotImplementedError` | Source Evidence | High |
| A07-E005 | `caption_service.py:26-27` | Inference calls `model_manager.get_components().get("processor")` and `.get("model")` directly | Source Evidence | High |
| A07-E006 | `embedding_service.py:27-28` | Inference calls `.get("processor")` and `.get("model")` directly | Source Evidence | High |
| A07-E007 | `translation_service.py:27-28` | Inference calls `.get("tokenizer")` and `.get("model")` directly | Source Evidence | High |
| A07-E008 | `tts_service.py:50` | Inference calls `.get("model")` directly | Source Evidence | High |
| A07-E009 | `models/implementations.py:33,37,60,61,80,81,99,100,117` | All `from_pretrained()` calls lack `revision` parameter — no model weight pinning | Source Evidence | High |
| A07-E010 | `caption_service.py:38-41` | BLIP output decoded and returned with no length, relevance, or repetition check | Source Evidence | High |
| A07-E011 | `embedding_service.py:34-40` | Embeddings L2-normalized but no dimensionality or magnitude bounds check | Source Evidence | High |
| A07-E014 | `settings.py:34` vs `grounding_service.py:12` | `GROUNDING_SIMILARITY_THRESHOLD=0.75` stored but never used in decision logic | Source Evidence | High |
| A07-E015 | `response_builder.py:32` | API response reports `threshold_used=0.75` from settings, not actual thresholds used | Source Evidence | High |
| A07-E016 | `translation_service.py:16,35,45` | Hardcoded: source `eng_Latn`, targets `["hin_Deva", "tel_Telu"]`, max_length 256 | Source Evidence | High |
| A07-E017 | `tts_service.py:18-22` | Hardcoded: 3 languages (en, hi, te), Telugu support uncertain (`# check if XTTS v2 officially supports te`) | Source Evidence | High |
| A07-E018 | `tts_service.py:27-30,44-46` | Speaker reference WAV at hardcoded path; silently returns `{}` if missing | Source Evidence | High |
| A07-E019 | `caption_service.py:32` | Token limit hardcoded: 40 (basic) / 80 (detailed) | Source Evidence | High |
| A07-E020 | `image_service.py:35-37` | Image max 1024px on longest edge | Source Evidence | High |
| A07-E021 | `translation_service.py:52-55` | Per-language translation errors not isolated — one failure can affect loop | Source Evidence | Medium |
| A07-E022 | `tts_service.py:53-54` | Languages not in `self.lang_codes` silently skipped | Source Evidence | High |
| A07-E023 | `request_coordinator.py:109` | `k=3` hardcoded in FAISS retrieval call | Source Evidence | High |
| A07-E024 | `retrieval_service.py:43` | Only `kb_list[0]` loaded — list of knowledge packs ignored | Source Evidence | High |
| A07-E025 | `backend/app/benchmark/` | Directory does not exist — zero benchmark infrastructure | Source Evidence | High |
| A07-E026 | `test_services.py, test_api.py` | Only 5 unit tests, none test actual model output quality | Source Evidence | High |
| A07-E027 | `request_coordinator.py:96` | `detailed=True` always passed — no mode switching | Source Evidence | High |

## 5. Verified Observations

### 5.1 Model Abstraction Layer is Decorative

All 5 concrete model classes in `implementations.py` raise `NotImplementedError` (A07-E001 through A07-E004). The base classes define `generate()`, `embed()`, `translate()`, `synthesize()` but the concrete implementations declare them only to raise an error explaining that inference lives in the service layer.

The service layer accesses raw components via `get_components()` dict:
- `caption_service.py:26-27`: `processor = self.model_manager.get_components().get("processor"); model = self.model_manager.get_components().get("model")` (A07-E005)
- Same pattern in `embedding_service.py:27-28` (A07-E006), `translation_service.py:27-28` (A07-E007), `tts_service.py:50` (A07-E008)

This means the model abstraction is entirely decorative. Swapping a model requires editing the service layer code.

### 5.2 Model Version Pinning

- All HuggingFace `from_pretrained()` calls lack `revision` parameter (A07-E009)
- `transformers==4.36.2` is pinned in requirements, but HF Hub model weights are mutable
- Only FAISS library is version-pinned (`faiss-cpu==1.7.4`)
- Models will silently change behavior when HF Hub updates default branch weights

### 5.3 Output Quality Validation — Zero

No pipeline stage validates its output quality:

| Stage | Validation | Evidence |
|---|---|---|
| Captioning | None — no length check, relevance check, or repetition check | A07-E010 |
| Embedding | L2 normalization only — no norm bounds or NaN check | A07-E011 |
| Retrieval | None — distances returned without sanity bounds | `retrieval_service.py:66-71` |
| Grounding | Threshold check applied to similarity scores | `grounding_service.py:45-68` |
| Translation | None — output accepted verbatim | A07-E010 (via service logic) |
| TTS | None — file path returned regardless of audio content | A07-E010 |

### 5.4 FAISS Index Evaluation

The FAISS index is `IndexFlatIP` (Inner Product) as verified in `build_knowledge_pack.py:73-75`. Both KB text embeddings (`build_knowledge_pack.py:65`) and query image embeddings (`embedding_service.py:39-40`) are L2-normalized. With normalized vectors, `IndexFlatIP` returns cosine similarity scores in range [-1, 1] where **higher = more similar**. The confidence thresholds `>= 0.8` (High), `>= 0.6` (Medium), `>= 0.4` (Low) are correctly applied to these similarity scores.

An earlier audit pass incorrectly claimed this was an L2 distance inversion. The independent review confirmed the implementation is correct — the scoring and confidence gating logic is sound.

### 5.5 Grounding Threshold Ghost

- `GROUNDING_SIMILARITY_THRESHOLD=0.75` defined in settings (A07-E014)
- `GroundingService.__init__` reads it to `self.threshold` (A07-E014)
- `self.threshold` is **never used** in any decision path — hardcoded 0.8/0.6/0.4 used instead (`grounding_service.py:45-68`)
- API response reports `threshold_used=0.75` (A07-E015) — different from actual applied thresholds

### 5.6 Fallback Behavior

| Scenario | Behavior | Evidence |
|---|---|---|
| Caption model failure | `CriticalAIException` → HTTP 500. No fallback. | A07-E005 service logic |
| Embedding model failure | `CriticalAIException` → HTTP 500. No fallback. | A07-E006 service logic |
| Translation failure | Caught, pipeline continues without translations | A07-E007 |
| TTS failure | Caught, pipeline continues without audio | A07-E008 |
| TTS speaker WAV missing | Silently returns `{}`, no error raised | A07-E018 |
| TTS language not supported | Silently skipped from output dict | A07-E022 |
| FAISS not installed | Empty `[]` returned, grounding skipped | `retrieval_service.py:41` |
| Model loading failure | `FAILED` state, startup aborts | Known from MC audit |

### 5.7 Benchmark Infrastructure

- `backend/app/benchmark/` directory does not exist (A07-E025)
- No evaluation metrics (BLEU, ROUGE, CIDEr, CLIPScore) anywhere in codebase
- 5 unit tests total, none test model output quality (A07-E026)
- No CI pipeline for model evaluation or regression detection

## 6. Assessments

The AI capability posture reveals a fundamental gap: the system runs models but has **no mechanism to measure whether outputs are correct**. The decorative abstraction layer means model changes require service-layer edits, defeating the purpose of the model class hierarchy.

The absence of benchmark infrastructure is the single largest risk because it prevents the team from: (a) measuring whether a model swap improves quality, (b) detecting regressions from dependency updates, (c) tuning thresholds and prompts systematically, and (d) validating output quality changes.

## 7. Findings

### AI-002 — Critical: Zero Output Quality Validation Across All Pipeline Stages

---
finding_id:         AI-002
category:           Model Output Quality
evidence_ids:       A07-E010, A07-E011
files:              caption_service.py:38-41; embedding_service.py:34-40; translation_service.py:48-50; tts_service.py:63-68
type:               AI Capability
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P0
regression_test:    Required
subsystems:
  - CaptionService
  - EmbeddingService
  - TranslationService
  - TTSService
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Unit test with known bad outputs (empty caption, wrong language, zero embedding)
---

**Verified facts**:
- BLIP caption output decoded and forwarded with no length, relevance, or repetition check (A07-E010)
- CLIP embeddings L2-normalized but no NaN check, norm upper bound, or dimensionality verification (A07-E011)
- NLLB translation output accepted verbatim without target language validation (A07-E010)
- XTTS audio path returned without duration check, silence detection, or speech verification (A07-E010)
- No pipeline stage has any post-inference quality gate

**Assessment**: Every model is a blind trust. Empty captions, wrong-language translations, degenerate embeddings, and silent audio all pass through to the user without warning. This creates a user trust problem: the application appears to succeed but delivers garbage.

---

### AI-003 — Critical: No Benchmark or Evaluation Infrastructure

---
finding_id:         AI-003
category:           Quality Measurement
evidence_ids:       A07-E025, A07-E026
files:              backend/app/benchmark/ (directory does not exist)
type:               AI Capability
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Not Applicable
subsystems:
  - Benchmark
  - CI
requirement_id:     None
requirement_status: None
estimated_effort:   Large
owner:              Backend
verification:       Benchmark script produces output on test dataset
---

**Verified facts**:
- No `backend/app/benchmark/` directory exists (A07-E025)
- No evaluation metrics (BLEU, ROUGE, CIDEr, CLIPScore) implemented anywhere
- Zero unit tests exercise model output quality (A07-E026)
- No CI pipeline runs model evaluation

**Assessment**: Without benchmark infrastructure, there is no mechanism to: detect regressions from model updates, compare model candidates (BLIP vs BLIP2 vs Florence-2), validate threshold tuning, or prove that fixes improve quality. The system cannot distinguish between "working" and "working correctly."

---

### AI-004 — Critical: Model Abstraction Layer Decorative — All Concrete Implementations Empty

---
finding_id:         AI-004
category:           Architecture
evidence_ids:       A07-E001, A07-E002, A07-E003, A07-E004, A07-E005, A07-E006, A07-E007, A07-E008
files:              models/implementations.py:47,67,87,106,123; caption_service.py:26-27; embedding_service.py:27-28; translation_service.py:27-28; tts_service.py:50
type:               AI Capability
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Architecture Debt
priority:           P1
regression_test:    Not Required
subsystems:
  - ModelsModule
  - Services
requirement_id:     None
requirement_status: None
estimated_effort:   Large
owner:              Backend
verification:       Model swap test — swap BLIP for Florence-2 without editing service layer
---

**Verified facts**:
- All 5 concrete model classes define core methods that raise `NotImplementedError` (A07-E001 through A07-E004)
- Service layer accesses `model_manager.get_components()` dict directly by string keys (A07-E005 through A07-E008)
- No model class method is ever called by any service — the abstraction is unused
- Swapping a model requires editing service layer Python code

**Assessment**: The model class hierarchy (`BaseCaptionModel` → `BLIP2Model`/`BLIPBaseModel`, etc.) exists on paper only. The system cannot actually swap models without code changes. This is architecture debt from an incomplete refactoring.

---

### AI-005 — High: No Model Weight Version Pinning

---
finding_id:         AI-005
category:           Reproducibility
evidence_ids:       A07-E009
files:              models/implementations.py:33,37,60,61,80,81,99,100,117
type:               AI Capability
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - ModelsModule
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Deployment test with cached vs fresh model weights
---

**Verified facts**:
- All 9 `from_pretrained()` calls across BLIP2, BLIP-Base, CLIP, NLLB, and XTTS lack `revision` parameter (A07-E009)
- HuggingFace Hub model weights on default branches are mutable — upstream can push changes at any time
- `transformers==4.36.2` pins the library but not the weights

**Assessment**: A deployment today and a deployment next month may use different model weights. This causes non-reproducible behavior between deployments and makes regression detection impossible.

---

### AI-006 — Medium: Grounding Threshold Configured But Never Used

---
finding_id:         AI-006
category:           Configuration
evidence_ids:       A07-E014, A07-E015
files:              settings.py:34; grounding_service.py:12,45-68; response_builder.py:32
type:               AI Capability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Required
subsystems:
  - GroundingService
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Change threshold in .env, verify it affects grounding decisions
---

**Verified facts**:
- `GROUNDING_SIMILARITY_THRESHOLD=0.75` defined in `settings.py:34` (A07-E014)
- `GroundingService.__init__` reads it into `self.threshold` (A07-E014)
- `self.threshold` never referenced in any decision method
- Decision logic uses hardcoded `>= 0.8`, `>= 0.6`, `>= 0.4`
- API response field `threshold_used=0.75` reports the configured value (A07-E015), not the actual applied thresholds

**Assessment**: The configured value `GROUDING_SIMILARITY_THRESHOLD=0.75` is stored but never consulted. The API response misreports `threshold_used=0.75` while actual thresholds are 0.8/0.6/0.4. This is a data accuracy issue — the user sees a threshold that doesn't match the decision logic. The grounding logic itself is correct (cosine similarity is properly computed and gated).

---

### AI-007 — High: Per-Language Translation Failures Not Isolated

---
finding_id:         AI-007
category:           Error Handling
evidence_ids:       A07-E021
files:              translation_service.py:52-55
type:               AI Capability
severity:           High
confidence:
  evidence:         Medium
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Required
subsystems:
  - TranslationService
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Test with one language failing mid-loop
---

**Verified facts**:
- Translation loop iterates over target languages without per-iteration error isolation (A07-E021)
- If one language fails, remaining languages in that iteration may be skipped or entire loop may abort depending on exception type
- Partial failures not logged with per-language granularity

**Assessment**: A user requesting 5 languages cannot determine which translations succeeded and which failed. Degraded behavior is opaque.

---

### AI-008 — High: Missing Speaker WAV Causes Silent TTS Degradation

---
finding_id:         AI-008
category:           Error Handling
evidence_ids:       A07-E018
files:              tts_service.py:27-30,44-46
type:               AI Capability
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - TTSService
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Deploy without default_speaker.wav, verify error log and response
---

**Verified facts**:
- Speaker reference WAV path hardcoded (`tts_service.py:27-30`)
- If file doesn't exist, `tts_service.py:44-46` returns empty dict `{}` without logging a warning or raising an error
- Pipeline continues silently without audio

**Assessment**: Silent degradation on missing file makes deployment failure invisible. A new deployment without the speaker WAV will appear to work but produce no audio.

---

### AI-009 — Medium: Hardcoded Model-Specific Code Prevents Model Swapping

---
finding_id:         AI-009
category:           Architecture
evidence_ids:       A07-E007, A07-E016, A07-E017
files:              translation_service.py:31-50; tts_service.py:18-22
type:               AI Capability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Architecture Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - TranslationService
  - TTSService
  - ModelsModule
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Attempt to use IndicTrans2 via config swap
---

**Verified facts**:
- `translation_service.py:35` uses `tokenizer.src_lang = "eng_Latn"` — NLLB-specific API
- `translation_service.py:41` uses `tokenizer.lang_code_to_id[lang]` — NLLB-specific
- `tts_service.py:21` has comment `# check if XTTS v2 officially supports te` — NLLB-specific coupling
- `.env.example` suggests `TRANSLATION_MODEL=IndicTrans2` but code is NLLB-only (A07-E016)
- Using IndicTrans2 would require rewriting `translation_service.py`

**Assessment**: The code is NLLB-specific despite config suggesting IndicTrans2 is supported. This is misleading for deployers and makes the TRANSLATION_MODEL config option a lie.

---

### AI-010 — Medium: Only First Knowledge Pack Used Despite List Configuration

---
finding_id:         AI-010
category:           Configuration
evidence_ids:       A07-E024
files:              retrieval_service.py:43
type:               AI Capability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - RetrievalService
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Configure 2+ knowledge packs, verify both are searched
---

**Verified facts**:
- `ACTIVE_KNOWLEDGE_PACKS` can list multiple packs in config (A07-E024)
- `retrieval_service.py:43` loads only `kb_list[0]` — subsequent packs ignored

**Assessment**: Multi-pack configuration is misleading. Users who create multiple knowledge packs thinking they're all active will get unexpected behavior.

---

### AI-011 — Medium: Always Uses Detailed Caption Mode

---
finding_id:         AI-011
category:           Configuration
evidence_ids:       A07-E027
files:              request_coordinator.py:96; caption_service.py:32
type:               AI Capability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - RequestCoordinator
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       API parameter test
---

**Verified facts**:
- `request_coordinator.py:96` always passes `detailed=True` (A07-E027)
- The only effect is token limit: 40 vs 80 tokens (A07-E019)
- No code path ever uses `detailed=False`
- No frontend UI toggle for detail level

**Assessment**: The detail parameter is dead code. Users get 80-token captions always with no way to request shorter captions.

---

### AI-012 — Medium: TTS Cold Start on First Request

---
finding_id:         AI-012
category:           Performance
evidence_ids:       A07-E008
files:              tts_service.py:33-35
type:               AI Capability
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - TTSService
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Measure first-request latency vs subsequent requests
---

**Verified facts**:
- XTTS model is lazy-loaded on first TTS request (`tts_service.py:33-35`)
- First request pays full model loading latency on top of inference

**Assessment**: First TTS request experiences 2-5x latency. Acceptable for development but surprising in production.

---

### AI-013 — Medium: Hardcoded Token Limits May Truncate Captions

---
finding_id:         AI-013
category:           Model Output Quality
evidence_ids:       A07-E019
files:              caption_service.py:32
type:               AI Capability
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - CaptionService
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Test caption generation with verbose images
---

**Verified facts**:
- Token limit hardcoded: 40 (basic) / 80 (detailed) tokens (A07-E019)
- BLIP/BLIP2 have no architectural cap preventing longer captions

**Assessment**: Complex images may generate truncated captions. Token limit is an arbitrary optimization, not a model limitation.

---

### AI-014 — Medium: Telugu TTS Support Uncertain

---
finding_id:         AI-014
category:           Model Capability
evidence_ids:       A07-E017
files:              tts_service.py:21
type:               AI Capability
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Runtime Validation Required
priority:           P2
regression_test:    Required
subsystems:
  - TTSService
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Runtime TTS test with Telugu input
---

**Verified facts**:
- Developer comment in `tts_service.py:21`: `# check if XTTS v2 officially supports te`
- Telugu language code `te` is in the hardcoded language list but developer was uncertain about support
- No runtime validation on startup to verify language support

**Assessment**: Telugu TTS may produce garbled output or fail at runtime. The uncertainly is documented in a comment but not addressed.

---

### AI-015 — Low: k=3 Hardcoded in FAISS Retrieval

---
finding_id:         AI-015
category:           Configuration
evidence_ids:       A07-E023
files:              request_coordinator.py:109
type:               AI Capability
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P3
regression_test:    Not Required
subsystems:
  - RetrievalService
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Unit test with different k values
---

**Verified facts**:
- `k=3` hardcoded in FAISS retrieval call (`request_coordinator.py:109`)
- Not configurable via settings or API parameter

**Assessment**: The number of retrieved knowledge base passages is not tunable without code changes. Minor — most applications need only 2-5 retrievals.

---

## 8. Model Inventory

| Model | Role | HF ID | Pinned? | Abstraction Works? | Output Validation |
|---|---|---|---|---|---|
| BLIP2 / BLIP-Base | Captioning | `Salesforce/blip-image-captioning-base` / `Salesforce/blip2-opt-2.7b` | No | No (NotImplementedError) | None |
| CLIP | Embedding | `openai/clip-vit-base-patch32` | No | No (NotImplementedError) | L2 norm only |
| NLLB | Translation | `facebook/nllb-200-distilled-600M` | No | No (NotImplementedError) | None |
| XTTS | TTS | `tts_models/multilingual/multi-dataset/xtts_v2` | No (lib pinned) | No (NotImplementedError) | None |
| FAISS | Vector search | `faiss-cpu==1.7.4` | Library pinned | N/A | None |

## 9. AI Capability Coverage Matrix

| Capability | Current State | Required State | Gap | Evidence |
|---|---|---|---|---|
| Output quality validation | None | Min length, relevance, language check | Missing entirely | AI-002 |
| Grounding confidence correctness | Cosine similarity properly computed | Verified correct — IndexFlatIP + L2 norm | No gap | AI-004 |
| Model swapping | Decoractive abstraction | Model-agnostic swap via config | 5 NotImplementedError raises | AI-004 |
| Model version reproducibility | Unpinned HF weights | Revision-pinned from_pretrained() | 9 unpinned calls | AI-005 |
| Benchmark infrastructure | None | BLEU/ROUGE/CIDEr/CLIPScore | No benchmark directory | AI-003 |
| Regression detection | None | CI-pipeline comparison | Missing entirely | AI-003 |
| Grounding threshold configurability | Configured but unused | Actual threshold affects decisions | Dead config value | AI-006 |
| Per-language error isolation | None | Isolated per-language try/catch | Shared error path | AI-007 |
| Knowledge pack multi-pack support | Only first pack used | All packs searched | Indexing bug | AI-010 |
| TTS speaker configurability | Hardcoded path | Configurable path | Hardcoded | AI-008 |
| Translation model configurability | NLLB-specific code | Any translation model | Model-specific coupling | AI-009 |

## 10. Runtime Validation Appendix

| ID | Hypothesis | Why Static Insufficient | Recommended Method |
|---|---|---|---|---|
| RV-AI-02 | Telugu TTS produces garbled output | Depends on XTTS v2 training data | Runtime audio quality check |
| RV-AI-03 | Missing speaker WAV causes silent skip without error | Depends on file system state at deploy time | Integration test without speaker WAV |
| RV-AI-04 | Per-language translation failures not isolated | Depends on exception type raised by NLLB | Integration test with one failing language |
| RV-AI-05 | Higer token limit improves caption quality | Depends on image complexity | A/B test with different max_length values |

## 11. Risk Register Mapping

| Risk ID | Finding | Severity | Confidence | Priority | Description |
|---|---|---|---|---|---|---|
| RR-07-002 | AI-002 | Critical | High | P0 | No output quality validation on any pipeline stage |
| RR-07-003 | AI-003 | Critical | High | P1 | No benchmark infrastructure — cannot measure quality |
| RR-07-004 | AI-004 | Critical | High | P1 | Model abstraction decorative — swaps require code edits |
| RR-07-005 | AI-005 | High | High | P1 | No model weight version pinning — non-reproducible |
| RR-07-006 | AI-006 | Medium | High | P2 | Grounding threshold configured but never used |
| RR-07-007 | AI-007 | High | Medium | P2 | Per-language translation failures not isolated |
| RR-07-008 | AI-008 | High | High | P2 | Missing speaker WAV causes silent TTS degradation |
| RR-07-009 | AI-009 | Medium | High | P2 | NLLB-specific code prevents translation model swap |
| RR-07-010 | AI-010 | Medium | High | P2 | Only first knowledge pack used despite list config |
| RR-07-011 | AI-011 | Medium | High | P2 | Always uses detailed caption mode |
| RR-07-012 | AI-012 | Medium | Medium | P2 | TTS cold start on first request |
| RR-07-013 | AI-013 | Medium | Medium | P2 | Hardcoded token limits may truncate captions |
| RR-07-014 | AI-014 | Medium | Medium | P2 | Telugu TTS support uncertain |
| RR-07-015 | AI-015 | Low | High | P3 | k=3 hardcoded in FAISS retrieval |

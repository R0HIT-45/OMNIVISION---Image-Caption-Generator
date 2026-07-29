# Audit 01 — Architecture Rule Violations

**Date:** 2026-07-29  
**Auditor:** opencode agent  
**Phase:** A0 — Pre-stabilization audit  
**Scope:** All backend Python (`backend/app/`) and frontend TypeScript source  

---

## Executive Summary

The codebase has a **critical architectural flaw**: the model abstraction layer is inverted. Model implementations (`BLIP2Model`, `CLIPModel`, `NLLBTranslationModel`, `XTTSModel`) are empty shells that raise `NotImplementedError` on their core methods. All actual inference logic lives in the service layer, which directly accesses model internals (`processor`, `tokenizer`, raw torch models) through a dictionary interface. This means:

- **No model can be swapped without modifying service code**
- **No new model type can be added without changes to 3+ files**
- **The architecture claims model-agnostic design but enforces model-specific coupling**

15 violations found across 7 categories. 2 Critical, 5 High, 5 Medium, 3 Low.

---

## 1. Encapsulation Violation — Inference in Service Layer

### Finding ARCH-001: Model implementations are empty shells

| Field | Value |
|---|---|
| **Evidence** | `implementations.py:47-48`, `:66-67`, `:86-87`, `:105-106`, `:122-123` |
| **Root Cause** | Every model's core method raises `NotImplementedError("Inference delegated to service layer via ModelManager")` |
| **Risk** | Critical — adding a new model requires modifying service code |
| **Fix Complexity** | L (move logic into implementations) |
| **Estimated Time** | 2-3 days |
| **Regression Risk** | High — all existing inference paths change |
| **Required Tests** | Unit tests for each model's `generate()`/`embed()`/`translate()`/`synthesize()` |
| **Blocks** | Phase C (model swapping) |

### Finding ARCH-002: Services access model internals directly

| Field | Value |
|---|---|
| **Evidence** | `caption_service.py:26-27`: `blip_bundle["processor"]`, `blip_bundle["model"]` |
| | `embedding_service.py:27-28`: `clip_bundle["processor"]`, `clip_bundle["model"]` |
| | `translation_service.py:27-28`: `trans_bundle["tokenizer"]`, `trans_bundle["model"]` |
| | `tts_service.py:50`: `tts_bundle["model"]` |
| **Root Cause** | `get_components()` returns raw dict of `{"processor": ..., "model": ...}` instead of encapsulating inference |
| **Risk** | Critical — every service has hardcoded knowledge of model internals |
| **Fix Complexity** | L (move bundle access into model.generate() etc.) |
| **Estimated Time** | 2-3 days |
| **Regression Risk** | High |
| **Required Tests** | Integration test for each service using mock models |
| **Blocks** | Phase C |

---

## 2. Interface Segregation Violation — `get_components()` Pattern

### Finding ARCH-003: `get_components()` violates encapsulation

| Field | Value |
|---|---|
| **Evidence** | `base.py:17-19`: `def get_components(self) -> Dict[str, Any]` |
| | `implementations.py:44,63,83,102,119`: all override `get_components()` |
| | `model_manager.py:74,104`: calls `.get_components()` |
| **Root Cause** | The base interface exposes internal implementation details rather than encapsulating functionality |
| **Risk** | High — any model with different internal structure (e.g., having `tokenizer` instead of `processor`) breaks the contract |
| **Fix Complexity** | M (remove method, make `generate()`/`embed()`/`translate()`/`synthesize()` self-contained) |
| **Estimated Time** | 1-2 days |
| **Regression Risk** | Medium |
| **Required Tests** | Unit tests for each abstract method |
| **Blocks** | Phase C |

---

## 3. Dependency Inversion Violation — Services Coupled to Manager

### Finding ARCH-004: Services call `get_model_manager()` directly

| Field | Value |
|---|---|
| **Evidence** | `caption_service.py:14`: `self.model_manager = get_model_manager()` |
| | `embedding_service.py:15`: `self.model_manager = get_model_manager()` |
| | `translation_service.py:14`: `self.model_manager = get_model_manager()` |
| | `tts_service.py:15`: `self.model_manager = get_model_manager()` |
| **Root Cause** | Services depend on a concrete singleton rather than an abstract model provider interface |
| **Risk** | High — impossible to mock or swap model management without patching |
| **Fix Complexity** | M (dependency-inject model manager or provide abstract interface) |
| **Estimated Time** | 1 day |
| **Regression Risk** | Medium |
| **Required Tests** | Service unit tests with injected mock managers |
| **Blocks** | Phase C |

---

## 4. Open/Closed Principle Violation — Registry & Routing

### Finding ARCH-005: Model registry uses fragile string matching

| Field | Value |
|---|---|
| **Evidence** | `registry.py:49-51`: `if model_id.endswith(key)` |
| **Root Cause** | Relies on model ID strings ending with registry keys (e.g., `"Salesforce/blip-image-captioning-base"` matches `"blip-image-captioning-base"`). Collision-prone and not explicit. |
| **Risk** | Medium — a model ID like `"custom/nllb-200-distilled-600M-v2"` would match translation registry |
| **Fix Complexity** | S (use exact mapping or explicit configuration) |
| **Estimated Time** | 2-4 hours |
| **Regression Risk** | Low |
| **Required Tests** | Registry unit tests for each model ID pattern |
| **Blocks** | Phase C |

### Finding ARCH-006: `get_model_id_for_key()` and `get_category_for_key()` use chained if/elif

| Field | Value |
|---|---|
| **Evidence** | `model_manager.py:44-53`: 4-way `if/elif` chain mapping model_key to model_id |
| | `model_manager.py:55-64`: 4-way `if/elif` chain mapping model_key to category |
| **Root Cause** | No data-driven mapping — adding a new model type requires modifying Manager code |
| **Risk** | Medium — violates Open/Closed principle |
| **Fix Complexity** | S (use dict lookup) |
| **Estimated Time** | 1-2 hours |
| **Regression Risk** | Low |
| **Required Tests** | Unit test for mapping |
| **Blocks** | Phase C |

### Finding ARCH-007: Adding new stage requires 3-file change

| Field | Value |
|---|---|
| **Evidence** | Stage metadata duplicated in: |
| | `orchestrator/frontend_transformer.py:21-46` (`STAGE_META` + `STAGE_ORDER` + `_model_label()` + `_stage_latency()`) |
| | `frontend/src/components/omnivision/pipeline-view.tsx:9-40` (`STAGE_LABELS` with hardcoded model names) |
| | `orchestrator/request_coordinator.py:89-159` (pipeline stage ordering) |
| **Root Cause** | No single source of truth for pipeline stages |
| **Risk** | Medium — adding a stage (e.g., capability classifier) requires syncing 3 files |
| **Fix Complexity** | M (extract stage config to shared JSON or settings) |
| **Estimated Time** | 1 day |
| **Regression Risk** | Medium |
| **Required Tests** | Integration test verifying all stages render |
| **Blocks** | Phase C, Phase D |

---

## 5. Single Responsibility Violation

### Finding ARCH-008: `ModelManager` mixes lifecycle management with pipeline policy

| Field | Value |
|---|---|
| **Evidence** | `model_manager.py:81-86`: Special-cases TTS loading with vision model unload |
| | `model_manager.py:91-92`: Special-cases TTS with `clear_gpu_memory()` |
| **Root Cause** | Memory pressure policy (unload vision before TTS) is hardcoded in the manager rather than orchestrated by the coordinator |
| **Risk** | Medium — if pipeline order changes or models are added, the policy logic must be updated here |
| **Fix Complexity** | M (move memory policy to `RequestCoordinator` or a dedicated `MemoryManager`) |
| **Estimated Time** | 1 day |
| **Regression Risk** | High (memory-related crashes if done wrong) |
| **Required Tests** | Memory lifecycle integration test |
| **Blocks** | Phase C |

### Finding ARCH-009: `ImageService` hardcodes limits instead of using settings

| Field | Value |
|---|---|
| **Evidence** | `image_service.py:15`: `self.max_size = 12 * 1024 * 1024` |
| **Root Cause** | Service defines its own threshold rather than reading from Settings |
| **Risk** | Medium — `MAX_UPLOAD_SIZE_MB` in settings has no effect |
| **Fix Complexity** | S (read from settings) |
| **Estimated Time** | 30 min |
| **Regression Risk** | Low |
| **Required Tests** | Parametrized test for size limit |
| **Blocks** | Phase A |

---

## 6. Layer Isolation Violations

### Finding ARCH-010: Model implementations depend on application settings

| Field | Value |
|---|---|
| **Evidence** | `implementations.py:6`: `from backend.app.config.settings import get_settings` |
| | `implementations.py:15`: `settings = get_settings()` |
| **Root Cause** | Model layer depends on application config layer — violates layered architecture |
| **Risk** | Low — model IDs are passed as constructor params in a proper design, not read from global settings |
| **Fix Complexity** | S (pass model_id and device as constructor args) |
| **Estimated Time** | 2-4 hours |
| **Regression Risk** | Low |
| **Required Tests** | Unit tests with non-default model IDs |
| **Blocks** | Phase C |

### Finding ARCH-011: `config_validator.py` imports torch at startup

| Field | Value |
|---|---|
| **Evidence** | `config_validator.py:4`: `import torch` |
| **Root Cause** | A startup validation module depends on a heavy AI library. If torch is not installed, startup crashes before any useful error message. |
| **Risk** | Low — torch is always present in the project, but violates separation of concerns |
| **Fix Complexity** | S (lazy import inside the validation function) |
| **Estimated Time** | 15 min |
| **Regression Risk** | None |
| **Required Tests** | Startup test without torch |
| **Blocks** | Phase D |

### Finding ARCH-012: `main.py` has hardcoded CORS allow_origins="*"

| Field | Value |
|---|---|
| **Evidence** | `main.py:44`: `allow_origins=["*"]` |
| **Root Cause** | No environment or profile-aware CORS configuration |
| **Risk** | Low for development, High for production |
| **Fix Complexity** | S (read from settings) |
| **Estimated Time** | 30 min |
| **Regression Risk** | Low |
| **Required Tests** | CORS integration test |
| **Blocks** | Phase D |

---

## 7. Missing Architecture Components

### Finding ARCH-013: No capability routing exists

| Field | Value |
|---|---|
| **Evidence** | `grep -r "capability\|classify.*image\|image.*type"` returned zero results in `backend/app/` |
| **Root Cause** | The architecture spec requires image-type classification (photo, screenshot, document, chart) before caption generation. Not implemented. |
| **Risk** | Medium — all image types are treated as photos. Screenshots, dashboards, and documents will produce poor results without routing. Independent review noted this is a missing feature, not a security/correctness defect, and the system works (suboptimally) without it. |
| **Fix Complexity** | XL (new module: CLIP zero-shot classifier + routing logic + tests) |
| **Estimated Time** | 3-5 days |
| **Regression Risk** | Low (new module, isolated) |
| **Required Tests** | Capability classification tests per image category |
| **Blocks** | Phase C (required for model specialization) |

### Finding ARCH-014: `BaseAIModel` lacks `model_id` and `metadata` properties

| Field | Value |
|---|---|
| **Evidence** | `models/base.py`: no `model_id` property, no `metadata` property |
| **Root Cause** | Architecture spec requires every model to expose `model_id`, `metadata` with version, capabilities, and hardware requirements |
| **Risk** | Medium — observability and experiment tracking cannot identify which model produced results |
| **Fix Complexity** | S (add abstract properties + implement in all classes) |
| **Estimated Time** | 4 hours |
| **Regression Risk** | Low |
| **Required Tests** | Unit test verifying each model reports metadata |
| **Blocks** | Phase B (experiment tracking) |

### Finding ARCH-015: No abstract service interface

| Field | Value |
|---|---|
| **Evidence** | `services/`: 7 service classes with no common base class |
| | `CaptionService`, `EmbeddingService`, `GroundingService`, `RetrievalService`, `TranslationService`, `TTSService`, `ImageService` |
| | Each has its own `warm_up()`/`shutdown()` signature (where they exist) |
| **Root Cause** | No shared contract for service lifecycle or generation |
| **Risk** | Medium — adding a new service requires copying patterns manually |
| **Fix Complexity** | M (introduce `BaseService` with lifecycle methods) |
| **Estimated Time** | 1 day |
| **Regression Risk** | Low |
| **Required Tests** | Lifecycle contract tests |
| **Blocks** | Phase C |

---

## Violation Summary

| ID | Category | Severity | Fix Complexity | Blocks Phase |
|---|---|---|---|---|
| ARCH-001 | Encapsulation — empty model implementations | **Critical** | L | C |
| ARCH-002 | Encapsulation — services access model internals | **Critical** | L | C |
| ARCH-003 | Interface Segregation — `get_components()` | High | M | C |
| ARCH-004 | Dependency Inversion — service-manager coupling | High | M | C |
| ARCH-007 | Open/Closed — 3-file stage sync | High | M | C, D |
| ARCH-013 | Missing — capability routing | High | XL | C |
| ARCH-005 | Open/Closed — fragile registry matching | Medium | S | C |
| ARCH-006 | Open/Closed — if/elif model routing | Medium | S | C |
| ARCH-008 | Single Responsibility — manager has pipeline policy | Medium | M | C |
| ARCH-009 | Single Responsibility — service hardcodes limits | Medium | S | A |
| ARCH-014 | Missing — `model_id`/`metadata` on models | Medium | S | B |
| ARCH-015 | Missing — service base interface | Medium | M | C |
| ARCH-010 | Layer Isolation — models depend on settings | Low | S | C |
| ARCH-011 | Layer Isolation — config_validator imports torch | Low | S | D |
| ARCH-012 | Layer Isolation — hardcoded CORS | Low | S | D |

---

## Recommendations

### Phase A — Fix Now (stabilization prerequisites)
1. **ARCH-009** — Make `ImageService` read `MAX_UPLOAD_SIZE_MB` from settings
2. **ARCH-006** — Replace if/elif chains with dict lookups in `model_manager.py`

### Phase B — Fix Before Benchmarking
3. **ARCH-014** — Add `model_id` and `metadata` to `BaseAIModel` and all implementations
4. **ARCH-015** — Introduce `BaseService` with lifecycle contract

### Phase C — Fix Before Model Improvements
5. **ARCH-001 + ARCH-002 + ARCH-003** — Major refactor: move inference into model implementations, remove `get_components()`, make services call abstract methods only
6. **ARCH-004** — Dependency-inject model provider into services
7. **ARCH-005** — Replace `endswith()` with explicit registry mapping
8. **ARCH-007** — Extract stage config to single source of truth
9. **ARCH-008** — Move memory policy from `ModelManager` to `RequestCoordinator` or `MemoryManager`
10. **ARCH-010** — Pass `model_id` as constructor arg, not from global settings
11. **ARCH-013** — Implement capability routing module

### Phase D — Fix Before Production
12. **ARCH-011** — Lazy-import `torch` in `config_validator.py`
13. **ARCH-012** — Profile-aware CORS from settings

---

## Verification Plan

For each fix, verify:
1. Existing tests pass (`pytest tests/`)
2. New unit tests cover the refactored path
3. `ruff` and `mypy` pass (when configured)
4. No regression in `evaluate_benchmark.py` output
5. Manual smoke test: upload an image, verify all stages complete

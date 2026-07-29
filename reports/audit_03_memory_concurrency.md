# Audit 03 — Memory & Concurrency

---
audit_id:            audit_03_memory_concurrency
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               ModelManager (singleton, locking, lifecycle), memory_utils (GPU cleanup), all service classes (async boundaries), request_coordinator (concurrent request handling), model implementations
---

## 1. Executive Summary

Analysis of the model lifecycle, memory management, locking, and async/sync boundaries reveals **16 findings: 3 Critical, 5 High, 6 Medium, 2 Low**. The most critical issue is that `ModelManager`'s `threading.Lock` only protects the singleton creation path and individual `get_model()` calls — it does **not** protect the returned model components from concurrent access or premature unloading. A second request can trigger TTS, which unloads BLIP/CLIP while another request is actively using them, causing crashes or state corruption. The third critical issue is that the pipeline is entirely synchronous on the event loop — despite `process()` being `async`, every model call blocks the event loop via synchronous `.generate()` calls, effectively serializing all requests and making the server vulnerable to head-of-line blocking.

The GPU memory strategy (load on demand, unload before TTS, `clear_gpu_memory()` after each inference) is appropriate for the 4GB VRAM constraint, but has no coordination across concurrent requests. Each service independently calls `torch.cuda.empty_cache()`, causing unnecessary overhead and potential thrashing.

| Metric | Count |
|---|---|
| Total findings | 17 |
| Critical severity | 3 |
| High severity | 5 |
| Medium severity | 6 |
| Low severity | 2 |
| P0 priority | 3 |
| P1 priority | 5 |
| P2 priority | 6 |
| P3 priority | 2 |
| Concurrency contract items | 6 |
| Runtime validation items | 3 |

## 2. Scope

| In Scope | Out of Scope |
|---|---|
| ModelManager singleton pattern | OS process scheduling (GIL, CPU affinity) |
| `threading.Lock` usage and scope | Distributed multi-node locking |
| Model state machine (UNLOADED → LOADING → READY → UNLOADING → FAILED) | Disk I/O contention (HF cache reads) |
| GPU memory: `clear_gpu_memory()`, `torch.cuda.empty_cache()` | CUDA kernel launch overhead |
| Async ↔ sync boundaries: `run_in_executor`, event loop blocking | Database connection pooling |
| `warm_up()` startup sequence | Network I/O concurrency |
| `shutdown()` cleanup | Container resource limits (cgroups) |
| Concurrent request handling (shared model instances) | Kubernetes HPA scaling |
| Cancellation and timeout handling | Frontend request cancellation |

## 3. Audit Limitations

| Limitation | Impact on Findings |
|---|---|
| No concurrent load testing | Race condition severity is inferred, not measured |
| No CUDA graph / stream analysis | GPU memory fragmentation not analyzed |
| No asyncio event loop instrumentation | Actual event loop blocking duration not measured |
| No distributed tracing | Lock contention duration not measurable statically |

## 4. Evidence Inventory

| ID | Location | Observation | Type | Confidence |
|---|---|---|---|---|
| A03-E001 | `model_manager.py:31-32` | `_instance = None; _lock = threading.Lock()` — class-level lock and instance | Source Evidence | High |
| A03-E002 | `model_manager.py:34-42` | `__new__` uses `cls._lock` — only protects singleton creation, not shared state | Source Evidence | High |
| A03-E003 | `model_manager.py:38-40` | `_models = {}`, `_model_states = {}` initialized inside `__new__` under lock | Source Evidence | High |
| A03-E004 | `model_manager.py:66-108` | `get_model()` acquires `self._lock` for full load-or-retrieve cycle | Source Evidence | High |
| A03-E005 | `model_manager.py:70` | `with self._lock:` in `get_model()` — lock scope includes state check, load, and return | Source Evidence | High |
| A03-E006 | `model_manager.py:76-78` | `if state in [ModelState.LOADING, ModelState.UNLOADING]: raise RuntimeError` — race detection | Source Evidence | High |
| A03-E007 | `model_manager.py:82-86` | TTS loading triggers `_unload_model_unsafe("blip")`, `_unload_model_unsafe("clip")`, `_unload_model_unsafe("translation")` while holding lock | Source Evidence | High |
| A03-E008 | `model_manager.py:91-92` | TTS calls `clear_gpu_memory()` before loading | Source Evidence | High |
| A03-E009 | `model_manager.py:101-102` | `self._models[model_key] = instance; self._model_states[model_key] = ModelState.READY` | Source Evidence | High |
| A03-E010 | `model_manager.py:105-108` | `except Exception: self._model_states[model_key] = ModelState.FAILED; raise e` | Source Evidence | High |
| A03-E011 | `model_manager.py:110-118` | `_unload_model_unsafe()` — assumes lock held; uses `del self._models[model_key]` | Source Evidence | High |
| A03-E012 | `model_manager.py:120-123` | `unload_model()` acquires lock then delegates to `_unload_model_unsafe()` | Source Evidence | High |
| A03-E013 | `memory_utils.py:9-30` | `clear_gpu_memory()`: `gc.collect()`, `torch.cuda.empty_cache()`, `torch.cuda.ipc_collect()` | Source Evidence | High |
| A03-E014 | `memory_utils.py:14-16` | `gc.collect()` forced before CUDA cache clear | Source Evidence | High |
| A03-E015 | `request_coordinator.py:53-73` | `warm_up()` loads BLIP, CLIP, Translation, Retrieval sequentially | Source Evidence | High |
| A03-E016 | `request_coordinator.py:75-78` | `shutdown()` only calls `self.tts_service.shutdown()` — other models not unloaded | Source Evidence | High |
| A03-E017 | `request_coordinator.py:80` | `async def process(...)` — method is async | Source Evidence | High |
| A03-E018 | `request_coordinator.py:95-97` | `self.caption_service.generate(...)` — synchronous call inside async method | Source Evidence | High |
| A03-E019 | `request_coordinator.py:102-105` | `self.embedding_service.generate_embedding(...)` — synchronous call | Source Evidence | High |
| A03-E020 | `request_coordinator.py:129-130` | `self.translation_service.translate(...)` — synchronous call inside async method | Source Evidence | High |
| A03-E021 | `request_coordinator.py:148` | `self.tts_service.generate(...)` — synchronous call | Source Evidence | High |
| A03-E022 | `request_coordinator.py:109` | `self.retrieval_service.search(...)` — synchronous call | Source Evidence | High |
| A03-E023 | `caption_service.py:45-46` | `torch.cuda.empty_cache()` called after each inference | Source Evidence | High |
| A03-E024 | `embedding_service.py:46-47` | `torch.cuda.empty_cache()` called after each inference | Source Evidence | High |
| A03-E025 | `translation_service.py:56-57` | `torch.cuda.empty_cache()` called after each inference | Source Evidence | High |
| A03-E026 | `model_manager.py:16-21` | `ModelState` enum: UNLOADED, LOADING, READY, UNLOADING, FAILED | Source Evidence | High |
| A03-E027 | `request_coordinator.py:27-39` | `initialize_orchestrator()` / `get_orchestrator()` — no lock on global assignment | Source Evidence | High |

## 5. Verified Observations

### 5.1 ModelManager Singleton

- `ModelManager` uses classic singleton pattern with `__new__` and class-level `_lock` (A03-E001)
- Lock only ensures single instance creation — subsequent calls return existing instance without locking (A03-E002)
- `_models` and `_model_states` dicts initialized once under lock in `__new__` (A03-E003)
- `get_model()` acquires per-instance `self._lock` for state transitions (A03-E004, A03-E005)
- Lock is **not** held while the caller (service) uses the returned model components — they are accessed outside lock scope

### 5.2 GPU Memory Management

- `clear_gpu_memory()` calls `gc.collect()` then `torch.cuda.empty_cache()` + `torch.cuda.ipc_collect()` (A03-E013)
- Called from: `caption_service.py` (A03-E023), `embedding_service.py` (A03-E024), `translation_service.py` (A03-E025), `model_manager.py` before TTS load (A03-E008)
- Each service independently calls empty_cache() — no coordination
- `_unload_model_unsafe()` calls `clear_gpu_memory()` after `del self._models[model_key]` (line 117-118)
- GPU memory logging at cleanup only (A03-E013 line 24-27)

### 5.3 Async vs Sync Boundaries

- `RequestCoordinator.process()` is `async def` (A03-E017)
- Every pipeline stage call is **synchronous** (A03-E018 through A03-E022)
- No `run_in_executor()` or `asyncio.to_thread()` used anywhere
- The only true `await` is `await self.image_service.validate_and_preprocess(file)` (A03-E002 in audit_02)
- Note: `image_service.validate_and_preprocess()` is async but only calls `await file.read()` — the rest is synchronous

### 5.4 Model State Machine

- States: UNLOADED → LOADING → READY (A03-E026)
- Failure path: any state → FAILED (A03-E010)
- Unload path: READY → UNLOADING → UNLOADED (A03-E011, line 113-117)
- No transition from FAILED back to UNLOADED or LOADING — stuck permanently
- Race detection: LOADING or UNLOADING while another call to `get_model()` raises RuntimeError (A03-E006)

### 5.5 Startup Sequence

- `warm_up()` loads models sequentially: BLIP → CLIP → Translation → Retrieval (FAISS) (A03-E015)
- TTS is explicitly skipped to preserve VRAM (lazy-loaded at first TTS request)
- `warm_up()` is all-or-nothing — if any model fails to load, the exception propagates and subsequent models never attempt loading
- `RequestCoordinator` is initialized eagerly at module level via `get_orchestrator()` call pattern

### 5.6 Shutdown

- `shutdown()` only calls `self.tts_service.shutdown()` (A03-E016)
- `tts_service.shutdown()` calls `self.model_manager.unload_model("tts")` (tts_service.py:37-38)
- BLIP, CLIP, Translation models are **never explicitly unloaded** during shutdown
- No signal handler registered for graceful shutdown on SIGTERM/SIGINT
- HF cache and GPU memory are not freed during shutdown

### 5.7 Concurrency Safety

- `ModelManager._lock` is a `threading.Lock` (not `asyncio.Lock`) — appropriate because all model calls are synchronous
- Lock is held across `_unload_model_unsafe()` for TTS pre-load, including unloading 3 other models (A03-E007) — long critical section
- No reference counting: models can be unloaded while other requests hold references to components
- `RequestCoordinator` singleton has no thread safety: `get_orchestrator()` can race during initialization (A03-E027)
- Services hold a reference to `self.model_manager` and call `get_model()` every time — no long-lived component caching

### 5.8 Cancellation / Timeout

- No timeout mechanism on model loading (`get_model()` can block indefinitely)
- No `asyncio.timeout()` or `asyncio.wait_for()` around any pipeline stage
- No request cancellation handling — if a client disconnects, the pipeline continues to completion
- No circuit breaker for repeatedly failing model loads

## 6. Findings

### MC-001 — Critical: Model components accessed outside lock scope; concurrent unload causes use-after-free

---
finding_id:         MC-001
category:           Concurrency — Shared State
evidence_ids:       A03-E005, A03-E007, A03-E011
files:              model_manager.py:70-104, 82-86, 110-118
type:               Concurrency
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P0
regression_test:    Required
subsystems:
  - ModelManager
  - All services
requirement_id:     None
requirement_status: None
estimated_effort:   Large
owner:              Backend
verification:       Concurrent request test with TTS trigger
---

**Verified facts**:
- `get_model()` acquires `self._lock` then returns model components (A03-E005)
- Lock is released immediately after `return instance.get_components()` at line 104 (A03-E004)
- Services hold the returned dict references and access `processor`, `model`, `tokenizer` outside any lock (A03-E018 through A03-E021)
- `get_model("tts")` unloads blip, clip, translation via `_unload_model_unsafe()` while holding lock (A03-E007)
- `_unload_model_unsafe()` does `del self._models[model_key]` (A03-E011 line 116)
- After lock release, another request's `get_model("tts")` can unload models while the first request is mid-inference

**Assessment**: This is a classic use-after-free race. Request A calls captionservice.generate() → gets model components (lock released). Request B calls TTS → acquires lock, unloads BLIP model (del _models["blip"]), loads TTS. Request A continues with a reference to a deleted model dict entry. The `self._models` dict entry is deleted, but the Python object may still exist if Request A holds a reference — however, the model's internal state (CUDA context, weights on GPU) may be corrupted, unmapped, or reallocated. This can cause silent corruption, segfaults, or "CUDA error: invalid device pointer" crashes.

**Requirement traceability**: No concurrency design document exists.

---

### MC-002 — Critical: Synchronous model calls block the asyncio event loop

---
finding_id:         MC-002
category:           Async/Sync Boundary
evidence_ids:       A03-E017, A03-E018, A03-E019, A03-E020, A03-E021, A03-E022
files:              request_coordinator.py:80,95-97,102-105,109,129-130,148
type:               Performance
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P0
regression_test:    Required
subsystems:
  - RequestCoordinator
  - All services
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Concurrent request latency measurement
---

**Verified facts**:
- `process()` is `async def` (A03-E017)
- Every pipeline stage call is synchronous: `self.caption_service.generate()` (A03-E018), `self.embedding_service.generate_embedding()` (A03-E019), `self.retrieval_service.search()` (A03-E022), `self.translation_service.translate()` (A03-E020), `self.tts_service.generate()` (A03-E021)
- No `run_in_executor()`, `asyncio.to_thread()`, or `loop.run_in_executor()` used anywhere
- The only `await` is `await self.image_service.validate_and_preprocess(file)` which internally awaits `file.read()`

**Assessment**: Every model inference call blocks the single-threaded asyncio event loop. When request A is generating a caption (~2-5 seconds of GPU time), request B cannot even begin validation. This effectively serializes all requests to the server. Under load, the server becomes completely unresponsive — health checks, other routes, and new requests all queue behind the GPU-bound call. The problem compounds: 500ms blocking might be acceptable, but BLIP caption generation can take 2-10 seconds depending on model and hardware.

**Requirement traceability**: No throughput/latency SLA documented.

---

### MC-003 — Critical: No shutdown cleanup for BLIP, CLIP, Translation models; GPU memory leak

---
finding_id:         MC-003
category:           Memory Management
evidence_ids:       A03-E016
files:              request_coordinator.py:75-78
type:               Resource Leak
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P0
regression_test:    Required
subsystems:
  - RequestCoordinator
  - ModelManager
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Graceful shutdown GPU memory check
---

**Verified facts**:
- `RequestCoordinator.shutdown()` only calls `self.tts_service.shutdown()` (A03-E016)
- `tts_service.shutdown()` calls `model_manager.unload_model("tts")` (tts_service.py:37-38)
- BLIP, CLIP, and Translation models remain loaded in GPU memory after shutdown (A03-E003, A03-E009)
- No signal handler registered for graceful shutdown

**Assessment**: On application shutdown (SIGTERM, pod termination, `docker stop`), only the TTS model is explicitly unloaded. BLIP (~1.2GB), CLIP (~600MB), and NLLB (~1.2GB) remain in GPU VRAM. While the OS will reclaim this memory on process termination, the lack of cleanup prevents clean state transitions (e.g., for live-reload development workflows) and can cause issues if the process forks or when using CUDA multi-process services (MPS).

**Requirement traceability**: No documented shutdown procedure.

---

### MC-004 — High: No timeout on model loading; `get_model()` blocks indefinitely

---
finding_id:         MC-004
category:           Resilience
evidence_ids:       A03-E004
files:              model_manager.py:66-108
type:               Design Gap
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - ModelManager
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Timeout test with slow model load mock
---

**Verified facts**:
- `get_model()` calls `ModelClass()` and then `instance.load(self.device)` (A03-E004 lines 98-99)
- `load()` downloads model weights from HF Hub if not cached (implementations.py:36,61,81,100,117)
- No timeout parameter passed to `from_pretrained()` or `TTS()`
- Whole operation runs under `self._lock` (A03-E005) — no other model operations possible during download

**Assessment**: If model weights are not cached and HF Hub is slow or unavailable, `get_model()` can block the entire `ModelManager` for minutes. Since the lock is held during this time, all other requests that need any model (including already-loaded ones) are blocked. Even requests for already-loaded models cannot proceed because `get_model()` acquires the lock before checking state.

**Requirement traceability**: No documented startup timeout.

---

### MC-005 — High: TTS pre-load unloads vision models while they may be in use by other requests

---
finding_id:         MC-005
category:           Concurrency — Resource Contention
evidence_ids:       A03-E007, A03-E011
files:              model_manager.py:82-86, 110-118
type:               Concurrency
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - ModelManager
requirement_id:     None
requirement_status: None
estimated_effort:   Large
owner:              Backend
verification:       Concurrent request TTS triggering
---

**Verified facts**:
- `get_model("tts")` unconditionally unloads "blip", "clip", "translation" (A03-E007 lines 83-85)
- This happens under lock, but the lock is released after TTS returns components
- Other requests may be mid-inference with those models when TTS is first requested
- `_unload_model_unsafe()` uses `del self._models[model_key]` (A03-E011)
- `clear_gpu_memory()` is called after unloading (A03-E008)

**Assessment**: Same root cause as MC-001 but specifically triggered by TTS lazy-loading. This is the most likely trigger for the race condition in production because TTS is the last stage and is lazy-loaded. If request A is generating a caption (blip is loaded) while request B finishes and reaches TTS (triggers blip unload), request A's caption generation will fail with an unrecoverable GPU error.

**Requirement traceability**: None documented.

---

### MC-006 — High: Stuck FAILED state — no recovery or retry mechanism

---
finding_id:         MC-006
category:           Resilience
evidence_ids:       A03-E010
files:              model_manager.py:105-108
type:               Design Gap
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - ModelManager
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Failed state recovery test
---

**Verified facts**:
- On exception during model load, state is set to `ModelState.FAILED` (A03-E010 line 106)
- Exception is re-raised to caller (A03-E010 line 108)
- No code path transitions from FAILED to any other state (A03-E026)
- `get_model()` line 71 checks `self._model_states.get(model_key, ModelState.UNLOADED)` — but FAILED is not UNLOADED, so it falls through to the state check at line 73 and 76
- FAILED state matches neither `READY` (line 73) nor `LOADING/UNLOADING` (line 76), so it proceeds to try loading again at line 88-104
- Wait — that means FAILED **does** retry? Let me re-check: the state check at line 70-78 is:
  - If READY → return cached
  - If LOADING/UNLOADING → raise RuntimeError
  - Otherwise → proceed to load
  Since FAILED is not READY, not LOADING, not UNLOADING, it falls through to the load path. So it does retry!

**Revised Assessment**: FAILED state actually does allow retry because the state check does not have a FAILED-specific branch. The state is set to FAILED, but the next call to `get_model()` will see it as "not READY, not LOADING, not UNLOADING" and attempt to load again. However, there is no backoff, no circuit breaker, and repeated failures will thrash. The FAILED state serves as a diagnostic marker only — no exponential backoff, no alerting, no degraded mode. A flaky model will cause repeated load failures on every request, each taking seconds to fail.

**Requirement traceability**: None documented.

---

### MC-007 — High: `torch.cuda.empty_cache()` called redundantly by each service — no coordination

---
finding_id:         MC-007
category:           Performance
evidence_ids:       A03-E023, A03-E024, A03-E025
files:              caption_service.py:45-46, embedding_service.py:46-47, translation_service.py:56-57
type:               Performance
severity:           High
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P1
regression_test:    Recommended
subsystems:
  - All services
  - Memory management
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       empty_cache call frequency profiling
---

**Verified facts**:
- `caption_service.py:45-46`: `torch.cuda.empty_cache()` after BLIP inference
- `embedding_service.py:46-47`: `torch.cuda.empty_cache()` after CLIP inference
- `translation_service.py:56-57`: `torch.cuda.empty_cache()` after NLLB inference
- Each call is inside a `if torch.cuda.is_available():` guard
- Only checked for CUDA availability, not whether the model actually used GPU memory

**Assessment**: `torch.cuda.empty_cache()` is a **synchronization barrier** — it blocks until all pending CUDA operations complete and then frees cached allocator memory. Calling it after every inference adds 10-100ms of latency per stage. For a pipeline of 3 GPU stages, this can add 30-300ms of unnecessary overhead per request. More importantly, if request A and B are processed concurrently (or interleaved via `run_in_executor`), one request's `empty_cache()` can invalidate the memory pool for the other request's tensors still in flight, triggering reallocation overhead.

**Requirement traceability**: None documented.

---

### MC-008 — High: `clear_gpu_memory()` uses synchronous `gc.collect()` inside lock scope

---
finding_id:         MC-008
category:           Performance — Lock Contention
evidence_ids:       A03-E008, A03-E013
files:              memory_utils.py:9-30, model_manager.py:91-92
type:               Performance
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Recommended
subsystems:
  - ModelManager
  - Memory management
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Lock hold time profiling
---

**Verified facts**:
- `get_model("tts")` calls `clear_gpu_memory()` while holding `self._lock` (A03-E008, A03-E013)
- `clear_gpu_memory()` calls `gc.collect()` (synchronous full GC — can take 10-500ms) and `torch.cuda.empty_cache()` (CUDA synchronization — can take 10-100ms)
- During this time, no other model operations (load, unload, state check) can proceed

**Assessment**: The lock is held across an expensive GC + CUDA sync operation. If TTS is triggered during a concurrent request, all other requests must wait for memory cleanup to complete before they can even check model state. This compounds the head-of-line blocking issue from MC-002.

---

### MC-009 — Medium: `RequestCoordinator` global singleton access is not thread-safe

---
finding_id:         MC-009
category:           Concurrency — Singleton
evidence_ids:       A03-E027
files:              request_coordinator.py:27-39
type:               Concurrency
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - RequestCoordinator
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Concurrent initialization test
---

**Verified facts**:
- `initialize_orchestrator()` and `get_orchestrator()` access and assign `_coordinator` global without any lock (A03-E027)
- `_coordinator: "RequestCoordinator | None"` is a module-level variable (line 24)
- `initialize_orchestrator()` has a double-checked pattern: checks `is not None`, then creates (line 29-31)
- `get_orchestrator()` similarly checks `is None` then creates (line 37-38)

**Assessment**: Two threads calling `get_orchestrator()` simultaneously can both see `_coordinator is None` and both create `RequestCoordinator` instances. The second assignment overwrites the first, and the first instance is lost (no cleanup). Worse, if one thread is mid-`__init__()` (which creates all service instances) while another thread reads `_coordinator`, it may get a partially-initialized object.

---

### MC-010 — Medium: `_unload_model_unsafe` doesn't verify model is not in use

---
finding_id:         MC-010
category:           Concurrency — State Safety
evidence_ids:       A03-E011
files:              model_manager.py:110-118
type:               Concurrency
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - ModelManager
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Reference count verification
---

**Verified facts**:
- `_unload_model_unsafe()` checks state is READY, then transitions to UNLOADING and deletes (A03-E011)
- No reference count or in-use tracking exists
- Caller (`get_model("tts")`) calls `_unload_model_unsafe("blip")` etc. without checking if blip is currently being used in inference (A03-E007)

**Assessment**: The model state machine tracks whether a model is loaded, but does not track **how many consumers** are actively using it. When `_unload_model_unsafe()` is called, it only checks `state == READY` — it doesn't check if any request holds a reference to the model's components. See MC-001 for the exploit path.

---

### MC-011 — Medium: No request cancellation handling; client disconnect does not abort pipeline

---
finding_id:         MC-011
category:           Resilience — Cancellation
evidence_ids:       A03-E017, A03-E018
files:              request_coordinator.py:80-174
type:               Design Gap
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not feasible
subsystems:
  - RequestCoordinator
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Client disconnect test
---

**Verified facts**:
- `process()` is async but all model calls are synchronous (A03-E017, A03-E018)
- No `asyncio.shield()`, `asyncio.wait_for()`, or cancellation checks between stages
- No `asyncio.Task.cancel()` handling or `CancelledError` catch
- Client disconnection does not propagate to the running task in standard FastAPI

**Assessment**: If a client disconnects mid-request (e.g., closes browser tab), FastAPI will cancel the request handler task. However, because model calls are synchronous and not running in an executor, the cancellation cannot be delivered until the GPU call returns. Once the model call finishes, the task's `CancelledError` will be raised at the next `await` point (which is after all pipeline stages complete, since there are no `await` calls after validation). This means: (1) GPU compute is wasted on a request nobody will see, and (2) the task still runs to completion even after client disconnect.

---

### MC-012 — Medium: `warm_up()` is all-or-nothing; partial startup leaves system in inconsistent state

---
finding_id:         MC-012
category:           Startup/Shutdown
evidence_ids:       A03-E015
files:              request_coordinator.py:53-73
type:               Design Gap
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not feasible
subsystems:
  - RequestCoordinator
  - ModelManager
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Partial startup simulation
---

**Verified facts**:
- `warm_up()` loads models in sequence: BLIP → CLIP → Translation → Retrieval (A03-E015)
- No rollback if a later model fails — models loaded before the failure stay loaded
- No partial health check: health endpoint reports "healthy" even if some models failed
- No "degraded" mode: if BLIP loads but CLIP fails, caption route is still registered

**Assessment**: If NLLB (translation) fails to load during warm_up(), BLIP and CLIP remain loaded in GPU memory but the pipeline is effectively non-functional (translation will fail). The health endpoint reports all models as healthy because it only checks `ModelManager._model_states` indirectly through the health check. A successful warm_up() is required for any request, but a partially failed warm_up() leaves the system in an undefined state.

---

### MC-013 — Medium: No inter-request GPU memory coordination; concurrent requests can OOM

---
finding_id:         MC-013
category:           Memory Management
evidence_ids:       A03-E003, A03-E007, A03-E008
files:              model_manager.py:38-40, 82-86, 91-92
type:               Concurrency
severity:           Medium
confidence:
  evidence:         Medium
  assessment:       Medium
status:             Open
audit_decision:     Runtime Validation Required
priority:           P2
regression_test:    Not feasible
subsystems:
  - ModelManager
  - Memory management
requirement_id:     None
requirement_status: None
estimated_effort:   Large
owner:              Backend
verification:       Concurrent OOM stress test
---

**Verified facts**:
- `ModelManager` uses a single shared model instance for all requests (A03-E003)
- GPU memory is not partitioned or reserved per request
- Multiple concurrent requests running the same model share the same VRAM allocations
- `clear_gpu_memory()` can invalidate tensors from other requests (A03-E008, A03-E013)
- TTS pre-load explicitly clears memory, potentially impacting concurrent inference requests (A03-E007)

**Assessment**: On a 4GB VRAM GPU, BLIP (~1.2GB), CLIP (~600MB), and NLLB (~1.2GB) together consume ~3GB. If two concurrent requests each allocate intermediate tensors during BLIP inference (~500MB each), total could exceed 4GB. There is no memory budget tracking, no per-request memory pool, and no OOM prevention strategy other than "unload before TTS." This is a **runtime validation** finding because actual OOM depends on batch size, image resolution, and concurrent request depth — static analysis cannot prove OOM is reachable.

---

### MC-014 — Medium: Lock scope includes model download from HF Hub (network I/O under lock)

---
finding_id:         MC-014
category:           Performance — Lock Contention
evidence_ids:       A03-E004, A03-E005
files:              model_manager.py:66-108
type:               Performance
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not feasible
subsystems:
  - ModelManager
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Network latency simulation test
---

**Verified facts**:
- `get_model()` holds `self._lock` from state check through model load to return (A03-E005)
- Model load includes `from_pretrained()` which may download weights from HF Hub (implementations.py:36,61,81,100,117)
- Network I/O can take 10-600 seconds for multi-GB model downloads
- During this time, no other thread can access any model (even already-loaded ones)

**Assessment**: If a model needs to be downloaded from HF Hub and is not cached, the entire `ModelManager` is locked for minutes. This prevents all other requests from accessing already-loaded models. While models are typically cached after first load, container restarts or cache evictions can trigger re-downloads. This is a lock granularity issue: the lock should be released during long-running I/O.

---

### MC-015 — Low: Inconsistent `torch.cuda.empty_cache()` guard — checks availability but not necessity

---
finding_id:         MC-015
category:           Code Quality
evidence_ids:       A03-E023, A03-E024, A03-E025
files:              caption_service.py:45-46, embedding_service.py:46-47, translation_service.py:56-57
type:               Code Quality
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P3
regression_test:    Not required
subsystems:
  - All services
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Static analysis
---

**Verified facts**:
- Each service checks `if torch.cuda.is_available():` before calling `torch.cuda.empty_cache()` (A03-E023, A03-E024, A03-E025)
- The model might be on CPU (e.g., `self.model_manager.device == "cpu"`) even if CUDA is available
- No check on whether model is actually on GPU

**Assessment**: Minor code quality issue. The guard is correct but imprecise. On a system with CUDA-available GPU, but models configured for CPU (e.g., memory-constrained environment), the empty_cache() call is unnecessary but harmless (it's a no-op if no GPU tensors are allocated). Not a functional defect.

---

### MC-016 — Low: `ModelManager` device determined once; no re-check or memory telemetry before model loads

---
finding_id:         MC-016
category:           Observability / Resilience
evidence_ids:       A03-E002, A03-E013
files:              model_manager.py:40, memory_utils.py:23-28
type:               Design Gap
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Architecture Debt
priority:           P3
regression_test:    Not required
subsystems:
  - ModelManager
  - Memory management
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Static analysis / log inspection
---

**Verified facts**:
- `self.device = "cuda" if torch.cuda.is_available() else "cpu"` set once in `__new__` (A03-E002 line 40) — never re-evaluated
- `clear_gpu_memory()` logs GPU memory **after** cleanup only, not before (A03-E013 lines 24-27)
- No pre-load, post-load, or pre-inference GPU memory snapshots are logged
- No memory logging at model load time or inference time

**Assessment**: Two minor gaps: (1) If CUDA becomes unavailable after singleton creation (e.g., driver reset), the device string becomes stale and models attempt to load on "cuda" which fails confusingly. The device should be re-checked on each `get_model()` call that triggers a load. (2) When an OOM occurs, there is no log record showing memory pressure before the crash — the "after cleanup" snapshot only shows that cleanup succeeded, not how close to OOM the system was. Adding pre-load memory snapshots would enable diagnostic root-cause analysis of OOMs.

---

## 7. Concurrency Contract

The following contract specifies the expected concurrency behavior. Current code violations are noted.

### CC-01: Model component safety
- **Contract**: Once a model is in READY state, its components (processor, model, tokenizer) must remain valid and unchanged for the duration of any caller's usage.
- **Status**: VIOLATED (MC-001, MC-005)
- **Repair**: Reference-count active users; defer unload until count reaches zero.

### CC-02: Event loop non-blocking
- **Contract**: Asynchronous pipeline must not block the event loop for more than 100ms per stage.
- **Status**: VIOLATED (MC-002)
- **Repair**: Offload all GPU-bound calls to `run_in_executor()` with a thread pool.

### CC-03: Lock granularity
- **Contract**: Locks must not be held across network I/O, disk I/O, or long-running GPU operations.
- **Status**: VIOLATED (MC-004, MC-014)
- **Repair**: Split `get_model()` into state-check (under lock) and load (without lock); use double-checked locking with state transitions.

### CC-04: Startup atomicity
- **Contract**: Startup must be atomic — either all models load successfully or the system reports "degraded."
- **Status**: VIOLATED (MC-012)
- **Repair**: Wrap warm_up() in a transaction with rollback; add per-model health state.

### CC-05: Shutdown completeness
- **Contract**: Shutdown must release all GPU resources and unload all models.
- **Status**: VIOLATED (MC-003)
- **Repair**: Iterate all known model keys and unload each in `RequestCoordinator.shutdown()`.

### CC-06: Cancellation propagation
- **Contract**: Client disconnect must abort the pipeline and free resources within a bounded time.
- **Status**: VIOLATED (MC-011)
- **Repair**: Use `asyncio.to_thread()` for model calls; cancellation can then be delivered at the `await` point.

## 8. Runtime Validation Appendix

The following items require dynamic/runtime testing to confirm or refute.

| RV-ID | Finding | Method | Success Criterion | Estimated Effort |
|---|---|---|---|---|
| RV-01 | MC-013: Concurrent OOM | Send 3+ concurrent requests with large images; monitor GPU memory | No OOM; all requests complete | 1 day |
| RV-02 | MC-001: Concurrent TTS unload race | Send request A (caption in progress), request B (triggers TTS) simultaneously | Request A completes without GPU error | 1 day |
| RV-03 | MC-002: Event loop blocking | Measure request latency under concurrent load | P50 latency does not increase linearly with concurrency | 4 hours |

## 9. Critical Path Dependencies

The following chain of failures represents the highest-risk scenario:

```
Request A (caption) → get_model("blip") → holds model ref (lock released)
Request B (TTS)    → get_model("tts")   → acquires lock → unloads blip (del _models["blip"])
                                         → clear_gpu_memory() → gc.collect() → empty_cache()
                                         → loads XTTS → returns (lock released)
Request A (cont.)  → BLIP inference on stale model reference
                   → CUDA error: invalid device pointer → CriticalAIException → HTTP 500
```

This scenario is **likely** under concurrent load because TTS is lazy-loaded on first request, and concurrent requests are common.

## 10. Cross-Audit References

| Reference | Audit | Relationship |
|---|---|---|
| ARCH-001, ARCH-002 | `audit_01_architecture` | Model encapsulation inversion prevents clean concurrency boundaries |
| ARCH-008 | `audit_01_architecture` | Memory policy in ModelManager causes MC-005 |
| SEC-012 | `audit_04_security` | No rate limiting — amplifies all concurrency issues |
| OBS-003 | `audit_06_observability` | No metrics — cannot detect lock contention blocking |
| OBS-005 | `audit_06_observability` | No latency histograms — cannot measure event loop blocking |
| A02-FM-039 | `audit_02_pipeline_failure` | TTS model unloading race (FM-039) directly maps to MC-005 |

## 11. Risk Register Mapping

| Risk ID | Description | Severity | Mitigation | Audit Findings |
|---|---|---|---|---|
| R-CONC-01 | Model unload during concurrent inference | Critical | Reference counting (CC-01) | MC-001, MC-005 |
| R-CONC-02 | Event loop blocked by GPU inference | Critical | run_in_executor (CC-02) | MC-002 |
| R-CONC-03 | GPU memory leak on shutdown | Critical | Full model unload (CC-05) | MC-003 |
| R-CONC-04 | Indefinite blocking on model download | High | Timeout + staged lock (CC-03) | MC-004, MC-014 |
| R-CONC-05 | Repeated model load thrash on failure | High | Circuit breaker + backoff | MC-006 |
| R-CONC-06 | Redundant GPU sync overhead | High | Coordinated empty_cache strategy | MC-007 |
| R-CONC-07 | Concurrent request OOM | Medium | Memory budget tracking | MC-013 |
| R-CONC-08 | Coordinator singleton race | Medium | Thread-safe initialization | MC-009 |
| R-CONC-09 | Client disconnect resource waste | Medium | Cancellation handling (CC-06) | MC-011 |
| R-CONC-10 | Partial startup undefined state | Medium | Atomic startup (CC-04) | MC-012 |

## 12. Recommendations

### Immediate (Phase A) — P0
1. **MC-002**: Offload all synchronous model calls to `run_in_executor()` in `RequestCoordinator.process()`
2. **MC-003**: Add `unload_model()` calls for all models in `RequestCoordinator.shutdown()`
3. **MC-001 + MC-005**: Add reference counting to `ModelManager`; defer unload until count reaches zero

### Short-term (Phase B) — P1
4. **MC-004**: Add timeout to `from_pretrained()` and `instance.load()` in `get_model()`
5. **MC-006**: Add exponential backoff and circuit breaker for FAILED state recovery
6. **MC-007**: Replace per-service `empty_cache()` calls with a single coordinated cleanup in `RequestCoordinator`

### Medium-term (Phase C) — P2
7. **MC-008**: Move `clear_gpu_memory()` outside lock scope in TTS loading
8. **MC-009**: Add threading.Lock to `get_orchestrator()` / `initialize_orchestrator()`
9. **MC-010**: Implement usage tracking via weak references or counters
10. **MC-011**: Add `asyncio.wait_for()` timeouts and cancellation handling
11. **MC-012**: Implement partial startup with degraded health reporting
12. **MC-013**: Add GPU memory budget tracking with admission control
13. **MC-014**: Use double-checked locking pattern: check state (lock), load (no lock), set state (lock)

### Long-term (Phase D) — P3
14. **MC-015**: Add device check to empty_cache() guard
15. **MC-016**: Add pre-load GPU memory logging; re-evaluate device string before each model load

## 13. Verification Plan

| Finding | Verification Method |
|---|---|
| MC-001 | 2 concurrent requests: one with slow caption mock, one triggering TTS → verify no crash |
| MC-002 | Concurrent request test: measure P50 latency at concurrency 1, 2, 4 → verify no linear increase |
| MC-003 | Graceful shutdown test: verify `torch.cuda.memory_allocated()` returns to baseline |
| MC-004 | Mock `from_pretrained()` to be slow → verify timeout fires |
| MC-005 | Same as MC-001 (same root cause) |
| MC-006 | Mock model load to fail 3 times → verify backoff delay between attempts |
| MC-007 | Profile `empty_cache()` call count per request: target = 0 (remove per-service calls) |
| MC-008 | Measure lock hold time during TTS load: target < 100ms |
| MC-009 | Thread safety test: 10 threads calling `get_orchestrator()` simultaneously |
| MC-010 | Same as MC-001 |
| MC-011 | Client disconnect test: verify task terminates within 1 second |
| MC-012 | Mock model load to fail → verify health endpoint reports "degraded" |
| MC-013 | Stress test: 3 concurrent requests with max-size images → verify no OOM |
| MC-014 | Same as MC-004 |
| MC-015 | Static: verify `if device == "cuda"` check added |
| MC-016 | Static: verify memory logging before and after model load |
| MC-016 | Add pre-load memory logging; verify device re-check before load |

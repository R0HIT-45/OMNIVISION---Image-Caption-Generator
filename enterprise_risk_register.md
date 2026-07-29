# Enterprise Risk Register

---
generated:     2026-07-29
source_audits: 11 (Architecture through Release Readiness)
total_risks:   55
status:        Active — consolidates findings from audits 01-11
---

## 1. Structure

Each risk is assigned a unique `RR-NN-NNN` identifier and cross-references the source audit finding(s). Risks are deduplicated across audits — where the same underlying issue appears in multiple audits, a single risk entry lists all cross-references.

Priority definitions:
- **P0** — Blocks any production deployment. Must fix before v0.9 release.
- **P1** — Required for v1.0 production release.
- **P2** — Should address before v1.0; acceptable to defer with documented exception.
- **P3** — Nice-to-have; address when resources permit.

---

## 2. P0 Risks (5 items)

| ID | Risk | Severity | Confidence | Audit References | Effort |
|---|---|---|---|---|---|
| RR-01-001 | **No output quality validation** — Zero checks on caption relevance, translation accuracy, embedding quality, or audio content across all pipeline stages. | Critical | High | AI-002 | Medium |
| RR-01-002 | **Hardcoded localhost API URL** — `BASE_URL = "http://localhost:8000/api/v1"` in `api.ts:3` ignores `VITE_OMNIVISION_API_URL`. Cannot deploy to non-localhost. | Critical | High | FE-001, CFG-007 | Small |
| RR-01-003 | **No CI/CD pipeline** — Zero automation for lint, test, build, deploy. No PR quality gates. | Critical | High | BL-001 | Large |
| RR-01-004 | **No backend lock file** — `requirements*.txt` with unpinned ranges. Non-reproducible pip installs. | Critical | High | BL-002, CFG-001 | Small |
| RR-01-005 | **No authentication, CORS wildcard+credentials** — All endpoints unauthenticated. `CORSMiddleware(allow_origins=["*"], allow_credentials=True)` is spec-invalid. | Critical | High | SEC-001, SEC-002 | Medium |

---

## 3. P1 Risks (18 items)

| ID | Risk | Severity | Confidence | Audit References | Effort |
|---|---|---|---|---|---|
| RR-02-001 | **No model weight version pinning** — All 9 `from_pretrained()` calls lack `revision` parameter. HF Hub updates silently change model behavior. | High | High | AI-005 | Small |
| RR-02-002 | **Model abstraction layer decorative** — All 5 concrete model classes raise `NotImplementedError`. Service layer accesses `get_components()` dict directly. Model swap requires service code edits. | Critical | High | AI-004, A01-001 | Large |
| RR-02-003 | **No benchmark infrastructure** — No `benchmark/` directory, no evaluation metrics, no regression detection. Cannot measure whether changes improve or degrade quality. | Critical | High | AI-003 | Large |
| RR-02-004 | **No per-request aggregate structured log** — Individual stages log with request_id but no single log record captures full lifecycle (timings, input, output, errors, GPU state). Operators must correlate multiple lines. | High | High | OBS-001 | Small |
| RR-02-005 | **No metrics or monitoring** — No Prometheus/OpenMetrics endpoint, no request counters, no latency histograms, no error rate tracking. | High | High | OBS-002 | Medium |
| RR-02-006 | **No GPU utilization or memory telemetry** — Per-request GPU memory not tracked. No utilization % or temperature monitoring. | High | High | OBS-004 | Medium |
| RR-02-007 | **Shared model instances across concurrent requests** — Single `self.model` in `ModelManager` shared across all concurrent requests. Undefined behavior (weights corruption, state leakage). | Critical | High | MC-001 | Large |
| RR-02-008 | **Event loop blocked by sync GPU inference** — All model inference runs synchronously in async route handlers. Blocks event loop for all concurrent requests. | Critical | High | MC-002 | Large |
| RR-02-009 | **`threading.Lock` in async context blocks event loop** — `ModelManager` uses `threading.Lock` with `acquire(blocking=True)` in async code paths. Blocks entire event loop thread. | High | High | MC-003 | Medium |
| RR-02-010 | **Only TTS unloaded at shutdown** — `request_coordinator.py:75-78` only calls `model_manager.unload_model("tts")`. BLIP, CLIP, NLLB, FAISS never released. | High | High | MC-004 | Small |
| RR-02-011 | **FAILED state is terminal** — No recovery path from FAILED. After model load failure, server must be restarted. | High | High | MC-005 | Small |
| RR-02-012 | **No cancellation or timeout handling** — Request cancellation does not stop in-progress pipeline. No request timeout mechanism. | High | High | MC-006, OBS-007 | Medium |
| RR-02-013 | **Decompression bomb protection gap** — No explicit image dimension or decompression bomb checking. Pillow internal protections may not cover all attack vectors. | High | Medium | SEC-003 | Small |
| RR-02-014 | **Docker backend lacks health check + runs as root** — Container process runs as root. No HEALTHCHECK for orchestrator probing. | High | High | BL-005 | Small |
| RR-02-015 | **No security scanning** — No Dependabot, pip-audit, npm audit, or Trivy configured. Known vulnerable `numpy==1.26.2` (CVE-2024-12905). | Critical | High | BL-004 | Medium |
| RR-02-016 | **Backend `audio_urls` unused by frontend** — Backend generates audio for every request but frontend uses browser `SpeechSynthesisUtterance` API instead. Waste of GPU compute. | High | High | FE-002 | Small |
| RR-02-017 | **No response schema validation** — `(await res.json()) as T` with zero runtime validation. Malformed backend JSON crashes the app. | High | High | FE-003 | Medium |
| RR-02-018 | **Documentation critically outdated** — All 21 docs locked at v1.0. Describe Streamlit frontend (actual: React), IndicTrans2 (actual: NLLB), flake8 (actual: Ruff). | Critical | High | DOC-001, DOC-002, DOC-003, DOC-004 | Large |

---

## 4. P2 Risks (22 items)

| ID | Risk | Severity | Confidence | Audit References | Effort |
|---|---|---|---|---|---|
| RR-03-001 | Grounding threshold configured but never used | Medium | High | AI-006, CFG-006 | Small |
| RR-03-002 | No liveness/readiness probes — single health endpoint always returns "online" | Medium | High | OBS-003, BL-005 | Small |
| RR-03-003 | Translation/TTS stages miss structured logging | Medium | High | OBS-005 | Small |
| RR-03-004 | Error logs don't distinguish 4xx from 5xx | Medium | High | OBS-006 | Small |
| RR-03-005 | Third-party library logs not in structured format | Medium | Medium | OBS-008 | Small |
| RR-03-006 | No configuration audit trail at startup | Medium | High | OBS-009 | Small |
| RR-03-007 | Translation failures not isolated per language | High | Medium | AI-007 | Small |
| RR-03-008 | Missing speaker WAV causes silent TTS skip | High | High | AI-008 | Small |
| RR-03-009 | NLLB-specific code prevents model swap | Medium | High | AI-009 | Medium |
| RR-03-010 | Only first knowledge pack used despite list config | Medium | High | AI-010, CFG-008 | Small |
| RR-03-011 | Always uses detailed caption mode | Medium | High | AI-011 | Small |
| RR-03-012 | TTS cold start on first request | Medium | Medium | AI-012 | Small |
| RR-03-013 | Hardcoded caption token limits (40/80) | Medium | Medium | AI-013 | Small |
| RR-03-014 | Telugu TTS support uncertain | Medium | Medium | AI-014 | Small |
| RR-03-015 | 45/46 UI components unused (bundle bloat) | Medium | High | FE-005 | Small |
| RR-03-016 | Missing backend fields in UI (grounding, model versions, stage errors) | Medium | High | FE-006 | Small |
| RR-03-017 | No image dimension validation | Medium | Medium | FE-007 | Small |
| RR-03-018 | Broken sitemap with empty BASE_URL | Medium | High | FE-008 | Small |
| RR-03-019 | Zero frontend test coverage | Medium | High | FE-009 | Large |
| RR-03-020 | Profile system partially implemented | High | High | CFG-001 | Medium |
| RR-03-021 | Mixed config resolution strategy (os.getenv + pydantic-settings + @property) | Medium | High | CFG-002 | Medium |
| RR-03-022 | Several dead config values (MAX_UPLOAD_SIZE_MB, API_BASE_URL, DATABASE_URL) | Medium | High | CFG-009 | Small |

---

## 5. P3 Risks (10 items)

| ID | Risk | Severity | Confidence | Audit References | Effort |
|---|---|---|---|---|---|
| RR-04-001 | Per-stage timing only in API response, not logged | Low | High | OBS-010 | Small |
| RR-04-002 | `k=3` hardcoded in FAISS retrieval | Low | High | AI-015 | Small |
| RR-04-003 | Hardcoded version and region in footer | Low | High | FE-010 | Small |
| RR-04-004 | Unused hook and dead code detection disabled | Low | High | FE-011 | Small |
| RR-04-005 | Dark theme error page mismatch | Low | Medium | FE-012 | Small |
| RR-04-006 | Pre-release frontend dev dependency | Low | Medium | BL-010 | Small |
| RR-04-007 | Dockerfile apt-get best practices | Medium | Medium | BL-009 | Small |
| RR-04-008 | Graceful shutdown doesn't drain active requests | Medium | High | MC-007 | Small |
| RR-04-009 | All-or-nothing startup (one model failure crashes all) | Medium | High | MC-008 | Small |
| RR-04-010 | Master Project Spec aspirational, not reflective | Low | High | DOC-010 | Medium |

---

## 6. Risk Distribution

| Priority | Count | Description |
|---|---|---|---|
| P0 | 5 | Blocks any production deployment |
| P1 | 18 | Required for v1.0 production release |
| P2 | 22 | Should address before v1.0 |
| P3 | 10 | Nice-to-have |
| **Total** | **55** | |

| Severity | Count |
|---|---|
| Critical | 6 |
| High | 21 |
| Medium | 20 |
| Low | 8 |

---

## 7. Risk by Subsystem

| Subsystem | P0 | P1 | P2 | P3 | Total | Key Risks |
|---|---|---|---|---|---|---|---|
| Models / AI Capability | 1 | 3 | 9 | 2 | 15 | No validation, no benchmark, decorative abstraction |
| Security / Auth | 1 | 3 | 1 | 0 | 5 | No auth, CORS, decompression bomb, no scanning |
| API / Frontend | 1 | 3 | 4 | 3 | 11 | Hardcoded URL, no response validation, unused audio_urls, dead components |
| Observability | 0 | 3 | 5 | 1 | 9 | No aggregate log, no metrics, no GPU telemetry |
| Concurrency / Memory | 0 | 6 | 2 | 2 | 10 | Shared model instances, event loop blocking, lock in async, no timeout |
| Configuration | 0 | 0 | 4 | 0 | 4 | Profile system partial, mixed resolution, dead values |
| Docker / Build | 2 | 3 | 0 | 2 | 7 | No CI/CD, no lock file, no health check, root user |
| Documentation | 0 | 1 | 0 | 1 | 2 | All docs outdated |

---

## 8. Cumulative Risk Register

| RR ID | Audit Finding(s) | Short Description | Priority | Severity | Effort | Phase |
|---|---|---|---|---|---|---|---|
| RR-01-001 | AI-002 | No output quality validation | P0 | Critical | Medium | A |
| RR-01-002 | FE-001, CFG-007 | Hardcoded localhost API URL | P0 | Critical | Small | A |
| RR-01-003 | BL-001 | No CI/CD pipeline | P0 | Critical | Large | A |
| RR-01-004 | BL-002 | No backend lock file | P0 | Critical | Small | A |
| RR-01-005 | SEC-001, SEC-002 | No auth, CORS wildcard+credentials | P0 | Critical | Medium | A |
| RR-02-001 | AI-005 | No model version pinning | P1 | High | Small | A |
| RR-02-002 | AI-004, A01-001 | Model abstraction decorative (NotImplementedError) | P1 | Critical | Large | C |
| RR-02-003 | AI-003 | No benchmark infrastructure | P1 | Critical | Large | C |
| RR-02-004 | OBS-001 | No per-request aggregate log | P1 | High | Small | B |
| RR-02-005 | OBS-002 | No metrics or monitoring | P1 | High | Medium | B |
| RR-02-006 | OBS-004 | No GPU telemetry | P1 | High | Medium | B |
| RR-02-007 | MC-001 | Shared model instances across concurrent requests | P1 | Critical | Large | B |
| RR-02-008 | MC-002 | Event loop blocked by sync GPU inference | P1 | Critical | Large | B |
| RR-02-009 | MC-003 | threading.Lock in async context | P1 | High | Medium | B |
| RR-02-010 | MC-004 | Only TTS unloaded at shutdown | P1 | High | Small | B |
| RR-02-011 | MC-005 | FAILED state is terminal | P1 | High | Small | A |
| RR-02-012 | MC-006, OBS-007 | No cancellation/timeout handling | P1 | High | Medium | B |
| RR-02-013 | SEC-003 | Decompression bomb protection gap | P1 | High | Small | A |
| RR-02-014 | BL-005 | Docker lacks health check, runs as root | P1 | High | Small | B |
| RR-02-015 | BL-004 | No security scanning (numpy CVE) | P1 | Critical | Medium | B |
| RR-02-016 | FE-002 | Backend audio_urls unused by frontend | P1 | High | Small | B |
| RR-02-017 | FE-003 | No response schema validation | P1 | High | Medium | B |
| RR-02-018 | DOC-001, DOC-002, DOC-003, DOC-004 | All docs critically outdated | P1 | Critical | Large | C |
| RR-03-001 | AI-006, CFG-006 | Grounding threshold configured but never used | P2 | Medium | Small | A |
| RR-03-002 | OBS-003, BL-005 | No liveness/readiness probes | P2 | Medium | Small | B |
| RR-03-003 | OBS-005 | Translation/TTS miss structured logging | P2 | Medium | Small | C |
| RR-03-004 | OBS-006 | Error logs don't distinguish 4xx/5xx | P2 | Medium | Small | C |
| RR-03-005 | OBS-008 | Third-party logs not structured | P2 | Medium | Small | C |
| RR-03-006 | OBS-009 | No config audit trail | P2 | Medium | Small | C |
| RR-03-007 | AI-007 | Translation failures not isolated | P2 | High | Small | C |
| RR-03-008 | AI-008 | Missing speaker WAV silent skip | P2 | High | Small | A |
| RR-03-009 | AI-009 | NLLB-specific code prevents swap | P2 | Medium | Medium | C |
| RR-03-010 | AI-010, CFG-008 | Only first knowledge pack used | P2 | Medium | Small | C |
| RR-03-011 | AI-011 | Always detailed caption mode | P2 | Medium | Small | C |
| RR-03-012 | AI-012 | TTS cold start | P2 | Medium | Small | C |
| RR-03-013 | AI-013 | Hardcoded token limits | P2 | Medium | Small | C |
| RR-03-014 | AI-014 | Telugu TTS uncertain | P2 | Medium | Small | C |
| RR-03-015 | FE-005 | 45/46 UI components unused | P2 | Medium | Small | C |
| RR-03-016 | FE-006 | Missing backend fields in UI | P2 | Medium | Small | C |
| RR-03-017 | FE-007 | No image dimension validation | P2 | Medium | Small | C |
| RR-03-018 | FE-008 | Broken sitemap | P2 | Medium | Small | C |
| RR-03-019 | FE-009 | Zero frontend test coverage | P2 | Medium | Large | C |
| RR-03-020 | CFG-001 | Profile system partially implemented | P2 | High | Medium | C |
| RR-03-021 | CFG-002 | Mixed config resolution strategy | P2 | Medium | Medium | C |
| RR-03-022 | CFG-009 | Dead config values | P2 | Medium | Small | C |
| RR-04-001 | OBS-010 | Per-stage timing not logged | P3 | Low | Small | C |
| RR-04-002 | AI-015 | k=3 hardcoded in retrieval | P3 | Low | Small | C |
| RR-04-003 | FE-010 | Hardcoded version/region | P3 | Low | Small | C |
| RR-04-004 | FE-011 | Unused hook, no dead code detection | P3 | Low | Small | C |
| RR-04-005 | FE-012 | Dark theme error page | P3 | Low | Small | C |
| RR-04-006 | BL-010 | Pre-release dev dependency | P3 | Low | Small | C |
| RR-04-007 | BL-009 | Docker apt-get best practices | P3 | Medium | Small | C |
| RR-04-008 | MC-007 | No graceful drain on shutdown | P3 | Medium | Small | C |
| RR-04-009 | MC-008 | All-or-nothing startup | P3 | Medium | Small | C |
| RR-04-010 | DOC-010 | Master spec aspirational | P3 | Low | Medium | C |

---

## 9. Phase Allocation Summary

### Phase A — Immediate Fixes (5 items)
P0 blockers + quick wins that significantly improve correctness and deployability:
1. **RR-01-001**: Add output quality validation (Medium)
2. **RR-01-002**: Fix hardcoded API URL (Small)
3. **RR-01-004**: Generate backend lock file (Small)
4. **RR-01-005**: Fix CORS + add basic auth (Medium)
5. **RR-02-013**: Add decompression bomb validation (Small)

### Phase B — Operations (10 items)
Monitoring, concurrency, and container hygiene for production:
1. **RR-01-003**: Add GitHub Actions CI (Large)
2. **RR-02-004**: Add per-request aggregate log (Small)
3. **RR-02-005**: Add metrics endpoint (Medium)
4. **RR-02-006**: Add GPU telemetry (Medium)
5. **RR-02-007**: Fix model concurrency — per-request instances (Large)
6. **RR-02-008**: Offload GPU inference to thread pool (Large)
7. **RR-02-009**: Replace threading.Lock with asyncio.Lock (Medium)
8. **RR-02-012**: Add timeout and cancellation handling (Medium)
9. **RR-02-014**: Add Docker health check, non-root user (Small)
10. **RR-02-015**: Add Dependabot + pip-audit (Medium)

### Phase C — Quality (remaining items)
Benchmarks, model abstraction, docs, tech debt:
- Build benchmark infrastructure (Large)
- Fix model abstraction layer (Large)
- Update all documentation (Large)
- Clean up dead UI components (Small)
- Add frontend tests (Large)
- All remaining P2/P3 items

---

## 10. Effort Summary

| Phase | Small | Medium | Large | Total |
|---|---|---|---|---|---|
| A | 3 | 2 | 0 | 5 |
| B | 4 | 4 | 2 | 10 |
| C | 19 | 7 | 5 | 31 |
| **Total** | **26** | **13** | **7** | **46** (excl. documentation) |

Effort estimates assume 1-2 days (Small), 3-5 days (Medium), 1-3 weeks (Large) per item with a single developer.

---

## 11. Source Audit Index

| Audit | File | Total Findings |
|---|---|---|
| 01 — Architecture | `reports/audit_01_architecture.md` | 15 violations |
| 02 — Pipeline Failure | `reports/audit_02_pipeline_failure.md` | 38 failure modes |
| 03 — Memory & Concurrency | `reports/audit_03_memory_concurrency.md` | 15 findings |
| 04 — Security | `reports/audit_04_security.md` | 25 findings |
| 05 — Configuration | `reports/audit_05_configuration.md` | 15 findings |
| 06 — Observability | `reports/audit_06_observability.md` | 10 findings |
| 07 — AI Capability | `reports/audit_07_ai_capability.md` | 14 findings |
| 08 — Frontend | `reports/audit_08_frontend.md` | 12 findings |
| 09 — Dependency & Build | `reports/audit_09_dependency_build.md` | 10 findings |
| 10 — Documentation | `reports/audit_10_documentation.md` | 10 findings |
| 11 — Release Readiness | `reports/audit_11_release_readiness.md` | Aggregate |

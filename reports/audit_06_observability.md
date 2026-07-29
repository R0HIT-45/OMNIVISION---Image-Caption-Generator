# Audit 06 — Observability

---
audit_id:            audit_06_observability
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               Logging, metrics, tracing, health checks, monitoring hooks across backend/ and deployment/
---

## 1. Executive Summary

Analysis of 14 source files reveals **10 findings: 0 Critical, 3 High, 6 Medium, 1 Low**. The most critical issue is **no per-request structured JSON log at pipeline completion** — individual stages log with structured fields but there is no single log record capturing the full request lifecycle (input, output, all stage timings, memory, GPU, errors). The second most impactful issue is **no metrics or monitoring infrastructure** — no Prometheus endpoint, no request counters, no latency histograms, no error rate tracking.

The logging system has structured JSON output with per-stage logging, but lacks aggregation, metrics, tracing, and production monitoring capabilities.

| Metric | Count |
|---|---|
| Total findings | 10 |
| Confirmed defects | 6 |
| Design debt | 3 |
| Runtime validation required | 1 |
| Critical severity | 0 |
| High severity | 3 |
| Medium severity | 6 |
| Low severity | 1 |
| P0 priority | 0 |
| P1 priority | 4 |
| P2 priority | 5 |
| P3 priority | 1 |

## 2. Scope

| In Scope | Out of Scope |
|---|---|
| Structured logging (logging_config.py, logging_middleware.py) | Application Performance Monitoring (APM) vendor integration |
| Per-stage logging (services, request_coordinator) | Real-user monitoring (RUM) |
| Health endpoint (main.py:59-88) | Log aggregation infrastructure (ELK, Loki, Datadog) |
| Error response logging (exceptions/handlers.py) | Alerting rule configuration |
| Pipeline timing (ProcessingContext) | SLA/SLO monitoring |
| Frontend-side observability | Synthetic monitoring |

## 3. Audit Limitations

| Limitation | Impact on Findings |
|---|---|
| No log output inspection at runtime | Cannot verify structured fields are correctly populated in all code paths |
| No metrics endpoint dynamic scanning | Prometheus/OpenMetrics endpoint absence verified statically only |
| No APM agent configuration review | Datadog/NewRelic/Grafana agent not present in dependencies |

## 4. Evidence Inventory

| ID | Location | Observation | Type | Confidence |
|---|---|---|---|---|
| A06-E001 | `logging_config.py:9-33` | `JSONFormatter` formats structured logs with timestamp, level, logger, message, plus optional fields | Source Evidence | High |
| A06-E002 | `logging_config.py:36-65` | Only `omnivision` and `uvicorn` loggers configured; stdout handler only; level hardcoded to INFO | Source Evidence | High |
| A06-E003 | `logging_middleware.py:12-52` | Request logging middleware logs start/end with request_id, latency_ms, phase, success | Source Evidence | High |
| A06-E004 | `request_coordinator.py:81-84` | Pipeline start log: request_id, pipeline_stage="init", success | Source Evidence | High |
| A06-E005 | `request_coordinator.py:163-174` | Pipeline error logs: request_id, pipeline_stage="error", success=False | Source Evidence | High |
| A06-E006 | `caption_service.py:21-24,48-52` | Caption stage log: request_id, pipeline_stage="caption", success, generated_text in message | Source Evidence | High |
| A06-E007 | `embedding_service.py:22-24,49-52` | Embedding stage log: request_id, pipeline_stage="embedding", success | Source Evidence | High |
| A06-E008 | `translation_service.py:59-60` | Translation log: no structured extra fields (plain string message) | Source Evidence | High |
| A06-E009 | `tts_service.py:70` | TTS log: no structured extra fields (plain string message) | Source Evidence | High |
| A06-E010 | `schemas.py:73-105` | `ProcessingContext` has per-stage timing fields (caption_time, embedding_time, etc.) but no single log record dumps them | Source Evidence | High |
| A06-E011 | `main.py:59-88` | Health endpoint returns status, version, profile, CUDA info, GPU memory, KB status | Source Evidence | High |
| A06-E012 | `response_builder.py:18-70` | `build_success()` computes total_time from ctx but only returns it in API response, not in a log record | Source Evidence | High |
| A06-E013 | `main.py` | No Prometheus metrics endpoint, no `/metrics` route registered | Source Evidence | High |
| A06-E014 | `main.py` | No liveness/readiness probes beyond the health endpoint; no separate `/livez` or `/readyz` | Source Evidence | High |
| A06-E015 | `memory_utils.py:23-28` | `clear_gpu_memory()` logs GPU memory allocated/reserved after cleanup — potential telemetry | Source Evidence | High |

## 5. Verified Observations

### 5.1 Structured Logging

- `JSONFormatter` produces structured JSON log lines (A06-E001)
- Optional fields supported: `request_id`, `pipeline_stage`, `phase`, `latency_ms`, `success`, `model`, `profile` (A06-E001)
- Only `omnivision` and `uvicorn` loggers configured (A06-E002)
- Third-party library logs (transformers, PIL, faiss) use default format to stderr (A06-E002)
- Log level hardcoded to `INFO` — no runtime configuration (A06-E002)

### 5.2 Pipeline Stage Logging

- Pipeline start logs: `request_id`, `pipeline_stage="init"`, `success=True` (A06-E004)
- Caption stage: `request_id`, `pipeline_stage="caption"`, `success`, generated_text in message (A06-E006)
- Embedding stage: `request_id`, `pipeline_stage="embedding"`, `success` (A06-E007)
- Translation stage: no structured fields — plain `logger.info("Translations complete.")` (A06-E008)
- TTS stage: no structured fields — plain `logger.info("TTS generation complete.")` (A06-E009)
- Pipeline error: `request_id`, `pipeline_stage="error"`, `success=False` (A06-E005)
- Unhandled exceptions: logged in middleware (A06-E003) with `request_id`, `phase="request_end"`, `success=False`, `latency_ms`

### 5.3 Per-Stage Timing

- `ProcessingContext` stores per-stage timings: `caption_time`, `embedding_time`, `retrieval_time`, `grounding_time`, `translation_time`, `audio_time` (A06-E010)
- `ResponseBuilder.build_success()` computes `total_time` from `ctx.start_time` (A06-E012)
- **No log record dumps the per-stage timings** — they only appear in the API response body (A06-E012)
- Timing data is lost if no API consumer reads it

### 5.4 Monitoring and Metrics

- No Prometheus/OpenMetrics endpoint (A06-E013)
- No request counter, latency histogram, or error rate tracking
- No `/metrics` route registered in `main.py` (A06-E013)
- No `prometheus_client` or similar dependency in requirements
- No circuit breaker or bulkhead pattern with observable state

### 5.5 Health Checks

- Single health endpoint `GET /api/v1/health` (A06-E011)
- Returns: status, version, profile, CUDA, GPU model, GPU memory, KB pack status, threshold, model names
- No separate liveness (`/livez`) or readiness (`/readyz`) endpoints (A06-E014)
- Health endpoint does not verify model availability (only checks KB file existence)
- Health endpoint always returns `"status": "online"` unless the server is completely unreachable — no internal state check

### 5.6 Error Visibility

- `logging_middleware.py:44` logs `str(e)` on request failure (A06-E003)
- `exceptions/handlers.py:61` logs exception class and message on API errors
- `request_coordinator.py:163-174` logs pipeline exceptions with pipeline_stage="error"
- Error responses include exception class name and message in JSON body
- **No distinction between client errors (4xx) and server errors (5xx) in log structure** — both logged with `success=False`

### 5.7 GPU Telemetry

- `memory_utils.py:23-28` logs allocated/reserved GPU memory (A06-E015) — only called during explicit cleanup
- No GPU utilization or temperature monitoring
- No per-request GPU memory tracking

## 6. Assessments

The observability posture is functional for development debugging but insufficient for production operations. The structured JSON logging is well-designed with consistent fields, but two significant gaps exist: (1) no aggregate per-request log record that captures the full pipeline lifecycle, and (2) no metrics infrastructure whatsoever. In production, operators need to monitor request rates, latency percentiles, error rates, and GPU utilization — none of which are currently instrumented.

## 7. Findings

### OBS-001 — High: No per-request aggregate structured log

---
finding_id:         OBS-001
category:           Structured Logging
evidence_ids:       A06-E004, A06-E006, A06-E007, A06-E008, A06-E009, A06-E010, A06-E012
files:              logging_middleware.py; request_coordinator.py; response_builder.py
type:               Observability
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - RequestCoordinator
  - Logging
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Log inspection after single request
---

**Verified facts**:
- Individual pipeline stages log with `request_id` and `pipeline_stage` (A06-E004, A06-E006, A06-E007)
- `ProcessingContext` accumulates per-stage timings, input metadata, output caption, success/failure (A06-E010)
- `ResponseBuilder.build_success()` has access to all timing data but only returns it in API response (A06-E012)
- No single log record captures: request_id, input filename, all stage timings, final caption, model versions, GPU metrics, error details, total duration
- Translation and TTS stages use plain string logs without structured extras (A06-E008, A06-E009)

**Assessment**: When investigating a production issue, an operator must correlate multiple log lines by request_id to reconstruct the full request lifecycle. A single starting log line and a single completion log line with full context (timings, input, output, errors, GPU state) would reduce mean time to resolution. The data exists in `ProcessingContext` and `ResponseBuilder` but is never emitted as a structured log.

---

### OBS-002 — High: No metrics or monitoring infrastructure

---
finding_id:         OBS-002
category:           Metrics
evidence_ids:       A06-E013
files:              main.py; requirements*.txt
type:               Observability
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - API
  - Deployment
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Metrics endpoint availability check
---

**Verified facts**:
- No `/metrics` endpoint registered (A06-E013)
- No `prometheus_client`, `opentelemetry`, or similar dependency in any requirements file (A06-E013)
- No request counter, latency histogram, or error rate gauge anywhere in the codebase

**Assessment**: Without metrics infrastructure, operators have no visibility into: request throughput (RPS), latency percentiles (p50/p95/p99), error rates, concurrent request count, GPU utilization, or memory pressure. Debugging production issues requires log correlation alone. This is a prerequisite for production deployment.

---

### OBS-003 — Medium: No separate liveness and readiness probes

---
finding_id:         OBS-003
category:           Health Checks
evidence_ids:       A06-E011, A06-E014
files:              main.py:59-88
type:               Observability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - API
  - Deployment
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Probe endpoint test
---

**Verified facts**:
- Only one health endpoint exists: `GET /api/v1/health` (A06-E011)
- Kubernetes/orchestrator typically requires separate `/livez` (liveness — is the process alive?) and `/readyz` (readiness — can it serve traffic?) probes
- Current health endpoint always returns `"status": "online"` once the server is running — does not verify model availability or KB accessibility
- If a model fails after startup (OOM, CUDA error), the health endpoint still returns "online" (A06-E011)

**Assessment**: In Kubernetes deployments, the orchestrator needs to distinguish between "process is running" (liveness) and "process can serve requests" (readiness). A single health endpoint that doesn't validate internal state means the orchestrator cannot detect when the application is alive but not ready (e.g., after a model crash).

---

### OBS-004 — High: No GPU utilization or memory telemetry

---
finding_id:         OBS-004
category:           Metrics
evidence_ids:       A06-E015
files:              memory_utils.py:23-28; main.py; request_coordinator.py
type:               Observability
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - Backend
  - Deployment
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       GPU metric collection test
---

**Verified facts**:
- `memory_utils.py:23-28` already logs GPU memory allocated/reserved — but only during explicit cleanup (A06-E015)
- No per-request GPU memory tracking
- No GPU utilization (compute utilization %) logging
- No GPU temperature monitoring
- No mechanism to emit GPU metrics to a time-series database

**Assessment**: GPU is the most expensive and constrained resource. Without utilization telemetry, operators cannot: detect GPU memory leaks (models not freed), optimize model loading (swap timing), identify GPU-bound vs CPU-bound bottlenecks, or right-size GPU allocation.

---

### OBS-005 — Medium: Translation and TTS stages miss structured logging

---
finding_id:         OBS-005
category:           Structured Logging
evidence_ids:       A06-E008, A06-E009
files:              translation_service.py:59-60; tts_service.py:70
type:               Observability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Not Required
subsystems:
  - TranslationService
  - TTSService
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Log output inspection
---

**Verified facts**:
- `translation_service.py:59` logs `logger.info("Translations complete.")` — no `extra` dict with structured fields (A06-E008)
- `tts_service.py:70` logs `logger.info("TTS generation complete.")` — no `extra` dict with structured fields (A06-E009)
- All other pipeline stages use structured extras (A06-E004, A06-E006, A06-E007)

**Assessment**: Inconsistent logging makes automated log parsing unreliable. If a log aggregator parses structured fields to identify pipeline stages and success/failure, translation and TTS completions are invisible.

---

### OBS-006 — Medium: Error logs do not distinguish 4xx from 5xx

---
finding_id:         OBS-006
category:           Structured Logging
evidence_ids:       A06-E003
files:              logging_middleware.py:40-51
type:               Observability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - Logging
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Log output inspection under error conditions
---

**Verified facts**:
- `logging_middleware.py:40-51` logs `success=False` for ALL exceptions, whether client error (4xx — ValidationException) or server error (5xx — CriticalAIException)
- No `status_code` field in the error log record
- Error response already has the status code but it's not included in the log extra dict

**Assessment**: Client errors (validation failures) and server errors (AI failures) are logged identically. An operator cannot differentiate between "user uploaded invalid file" (client issue, no action needed) and "model crashed" (server issue, urgent) without parsing the exception message string. A `status_code` field in the log would enable alerting rules on 5xx rates.

---

### OBS-007 — Medium: No request timeout or cancellation logging

---
finding_id:         OBS-007
category:           Observability
evidence_ids:       A06-E003, A06-E004
files:              request_coordinator.py; logging_middleware.py
type:               Observability
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - RequestCoordinator
  - Logging
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Timeout/disconnect log inspection
---

**Verified facts**:
- No request timeout mechanism (MC-006)
- No cancellation handling (MC-006)
- If client disconnects, middleware logs `success=False` with `str(e)` — but cancellation events are not differentiated from other failures
- No log field indicating "client disconnected" vs "server error" vs "timeout"

**Assessment**: Timeouts and cancellations have different operational responses than server errors. A timeout might indicate resource exhaustion; a cancellation might indicate frontend UX issues. Without distinguishing these in logs, operators cannot identify the root cause of incomplete requests.

---

### OBS-008 — Medium: Third-party library logs not included in structured format

---
finding_id:         OBS-008
category:           Structured Logging
evidence_ids:       A06-E002
files:              logging_config.py:53-63
type:               Observability
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - Configuration
  - Logging
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Log output inspection at runtime
---

**Verified facts**:
- `logging_config.py` configures only `omnivision` and `uvicorn` loggers (A06-E002)
- Third-party library loggers (`transformers`, `PIL`, `faiss`, `urllib3`, `httpx`, `numpy`) use Python's default logging configuration
- Default config: WARNING level, plain-text format, stderr output

**Assessment**: When troubleshooting model issues, HuggingFace transformers and FAISS logs at WARNING/ERROR level go to stderr in plain text, not to the structured JSON stdout. An operator reading the application logs would miss warnings about model loading, tokenizer issues, or FAISS index problems.

---

### OBS-009 — Medium: No audit trail for configuration changes

---
finding_id:         OBS-009
category:           Observability
evidence_ids:       A06-E002
files:              logging_config.py; settings.py
type:               Observability
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Not Required
subsystems:
  - Configuration
  - Logging
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Startup log inspection
---

**Verified facts**:
- On startup, `config_validator.py` validates configuration but does not log the resolved configuration values
- No log line records "starting with profile X, BLIP model Y, CLIP model Z, threshold T"
- Changes to environment variables between deployments are not logged

**Assessment**: When debugging a behavioral change between deployments, operators need to know what configuration was active. Without a startup log of effective configuration values, the only source of truth is the deployment environment variable set, which may not be preserved.

---

### OBS-010 — Low: Per-stage timing only available in API response

---
finding_id:         OBS-010
category:           Structured Logging
evidence_ids:       A06-E010, A06-E012
files:              response_builder.py:46-53; schemas.py:97-104
type:               Observability
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P3
regression_test:    Not Required
subsystems:
  - Logging
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Log inspection after request
---

**Verified facts**:
- `ProcessingContext` stores per-stage timings (A06-E010)
- `ResponseBuilder.build_success()` returns them in API response only (A06-E012)
- No log record captures per-stage timings for server-side analysis

**Assessment**: Per-stage timing is valuable for performance analysis over time. Currently only available if an API consumer records it. Server-side logging would enable latency percentiles per pipeline stage without relying on client-side data collection.

---

## 8. Observability Coverage Matrix

| Aspect | Current State | Required State | Gap | Evidence |
|---|---|---|---|---|
| Per-request structured log | Individual stage logs with request_id | Single start + end record with full context | Missing aggregate record | A06-E004, A06-E012 |
| Request throughput (RPS) | Not instrumented | Prometheus counter | Not implemented | A06-E013 |
| Latency percentiles | Not instrumented | p50/p95/p99 latency histogram | Not implemented | A06-E013 |
| Error rate tracking | `success` boolean in logs | 5xx/4xx counters, error budget | No separate 5xx tracking | A06-E003 |
| GPU utilization | Not instrumented | Utilization % gauge, memory gauge | Not implemented | A06-E015 |
| GPU memory per request | Not instrumented | Per-request allocation/log | Not implemented | A06-E015 |
| Liveness probe | None | `/livez` endpoint | Not implemented | A06-E014 |
| Readiness probe | None | `/readyz` endpoint | Not implemented | A06-E014 |
| Configuration audit trail | None | Startup log of effective config | Not implemented | A06-E009 |
| Third-party log unification | Plain text, stderr | Structured JSON, same stream | Missing logger config | A06-E002 |
| Timeout/cancellation visibility | Not distinguishable | Status field for cancellation | Missing log field | A06-E003 |
| Pipeline stage latency | In API response only | Logged server-side | Missing log emission | A06-E010, A06-E012 |

## 9. Runtime Validation Appendix

| ID | Hypothesis | Why Static Insufficient | Recommended Method |
|---|---|---|---|
| RV-OBS-01 | Per-stage timing values in API response match actual wall-clock time | Timing correctness depends on sys.monotonic() behavior | Compare API response timing with server-side log timestamps |
| RV-OBS-02 | Third-party library warnings are logged to stderr and invisible in structured logs | Depends on library logging configuration at initialization time | Trigger a warning (invalid input, missing cache), check log output format |
| RV-OBS-03 | Health endpoint returns "online" even after model failure | No model state check in health endpoint — can only verify at runtime | Crash a model (simulated OOM), hit health endpoint |

## 10. Risk Register Mapping

| Risk ID | Finding | Severity | Confidence | Priority | Description |
|---|---|---|---|---|---|
| RR-06-001 | OBS-001 | High | High | P1 | No per-request aggregate structured log — operators must correlate multiple lines |
| RR-06-002 | OBS-002 | High | High | P1 | No metrics or monitoring — no RPS, latency, error rate visibility |
| RR-06-003 | OBS-003 | Medium | High | P2 | No liveness/readiness probes — orchestrator cannot detect degraded state |
| RR-06-004 | OBS-004 | High | High | P1 | No GPU utilization or memory telemetry |
| RR-06-005 | OBS-005 | Medium | High | P2 | Translation and TTS stages miss structured logging fields |
| RR-06-006 | OBS-006 | Medium | High | P2 | Error logs do not distinguish 4xx from 5xx |
| RR-06-007 | OBS-007 | Medium | Medium | P2 | No timeout/cancellation differentiation in logs |
| RR-06-008 | OBS-008 | Medium | Medium | P2 | Third-party library logs not in structured format |
| RR-06-009 | OBS-009 | Medium | High | P2 | No configuration change audit trail at startup |
| RR-06-010 | OBS-010 | Low | High | P3 | Per-stage timing only available in API response, not logged |

## 11. Cross-Audit References

| This Finding | Audit 03 (Mem/Conc) | Audit 04 (Security) | Audit 05 (Configuration) | Risk Register |
|---|---|---|---|---|
| OBS-001 | MC-002 (event loop blocked — affects latency logging) | — | — | RR-06-001 |
| OBS-002 | — | — | — | RR-06-002 |
| OBS-003 | — | SEC-007 (health endpoint leaks info) | — | RR-06-003 |
| OBS-004 | MC-004 (models not unloaded — GPU tracking would detect) | — | — | RR-06-004 |
| OBS-007 | MC-006 (no cancellation handling) | — | — | RR-06-007 |
| OBS-008 | — | — | CFG-007 (logger config gaps) | RR-06-008 |
| OBS-009 | — | — | CFG-001, CFG-002 (config design issues) | RR-06-009 |

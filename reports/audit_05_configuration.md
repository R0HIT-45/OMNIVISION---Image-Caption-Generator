# Audit 05 — Configuration

---
audit_id:            audit_05_configuration
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               All configuration sources: settings.py, .env, .env.example, logging_config.py, config_validator.py, pack.json, frontend .env, docker-compose.yml, pyproject.toml, .pre-commit-config.yaml
---

## 1. Executive Summary

Analysis of 12 configuration files reveals **15 findings: 2 High, 9 Medium, 4 Low**. The most impactful issues are a **partially implemented profile system** (only BLIP_MODEL respects profiles; other models ignore them) and a **settings class with mixed resolution strategies** (direct `os.getenv()` calls alongside `pydantic-settings` env_file resolution, creating unpredictable precedence). Additionally, `GROUNDING_SIMILARITY_THRESHOLD` (0.75) is hardcoded in the service layer as thresholds (0.8/0.6/0.4) that differ from the configured value.

The configuration system is functional for development but has enough inconsistencies to cause subtle bugs in production — particularly around profile-dependent model selection and dead configuration values.

| Metric | Count |
|---|---|
| Total findings | 15 |
| Confirmed defects | 8 |
| Architecture debt | 1 |
| Design debt | 4 |
| Runtime validation required | 1 |
| Informational | 1 |
| Evidence: High confidence | 13 |
| Evidence: Medium confidence | 2 |
| Assessment: High confidence | 12 |
| Assessment: Medium confidence | 3 |
| Assessment: Low confidence | 0 |
| High severity | 2 |
| Medium severity | 9 |
| Low severity | 4 |
| P1 priority | 2 |
| P2 priority | 9 |
| P3 priority | 4 |

## 2. Scope

| In Scope | Out of Scope |
|---|---|
| `settings.py` — Settings class and field definitions | Runtime configuration reload behavior |
| `.env` — Actual environment values | Encrypted/secret store integration |
| `.env.example` — Configuration template | CI/CD pipeline configuration |
| `config_validator.py` — Startup validation | OS-level environment injection |
| `logging_config.py` — Logging configuration | Third-party service configuration |
| `pack.json` — Knowledge pack metadata | Benchmark configuration |
| `frontend/.env` — Frontend configuration | |
| `docker-compose.yml` — Environment variable passing | |
| `pyproject.toml` — Tool configuration | |
| `.pre-commit-config.yaml` — Pre-commit hooks | |
| Profile system implementation | |
| Dead/unused configuration values | |

## 3. Audit Limitations

| Limitation | Impact on Findings |
|---|---|
| No runtime config loading test | Cannot verify environment variable override precedence in all scenarios |
| No multi-profile deployment test | Profile switching behavior only analyzed in code, not at runtime |
| No secret store integration review | Only `.env` file evaluated as configuration source |
| No frontend build-time config test | Vite environment variable injection not verified at build time |

## 4. Methodology

All findings derived from static source code analysis. Configuration values are traced from definition (`settings.py`) to consumption (service layer, validators) to identify gaps, dead values, and inconsistencies.

## 5. Evidence Inventory

| ID | Location | Observation | Type | Confidence |
|---|---|---|---|---|
| A05-E001 | `settings.py:10` | `PROFILE: str = os.getenv("PROFILE", "development")` — direct os.getenv, not pydantic field | Source Evidence | High |
| A05-E002 | `settings.py:17-28` | `BLIP_MODEL` is a `@property` with profile-based logic | Source Evidence | High |
| A05-E003 | `settings.py:30-32` | `CLIP_MODEL`, `TRANSLATION_MODEL`, `TTS_MODEL` are plain fields with no profile awareness | Source Evidence | High |
| A05-E004 | `settings.py:34` | `GROUNDING_SIMILARITY_THRESHOLD` — direct `os.getenv()` + `float()` call | Source Evidence | High |
| A05-E005 | `settings.py:37-39` | `ACTIVE_KNOWLEDGE_PACKS` is a `@property` with `json.loads()` | Source Evidence | High |
| A05-E006 | `settings.py:47` | `MAX_UPLOAD_SIZE_MB` defined but unused in backend code | Source Evidence | High |
| A05-E007 | `settings.py:49-51` | `Config.extra = "allow"` — silently accepts unknown env vars | Source Evidence | High |
| A05-E008 | `image_service.py:15` | `self.max_size = 12 * 1024 * 1024` — hardcoded, ignores settings | Source Evidence | High |
| A05-E009 | `grounding_service.py:12` | `self.threshold = settings.GROUNDING_SIMILARITY_THRESHOLD` — reads setting | Source Evidence | High |
| A05-E010 | `grounding_service.py:45,51,57,63` | Hardcoded thresholds (0.8, 0.6, 0.4) — different from configured 0.75 | Source Evidence | High |
| A05-E011 | `.env.example:23` | `TRANSLATION_MODEL=ai4bharat/indictrans2-en-indic-dist-200M` — different model | Source Evidence | High |
| A05-E012 | `.env:23` | `DATABASE_URL=postgresql://user:password@localhost:5432/omnivision` — defined but unused | Source Evidence | High |
| A05-E013 | `retrieval_service.py:43` | `pack_name = self.active_packs[0]` — only first pack used despite list type | Source Evidence | High |
| A05-E014 | `api.ts:3` | `BASE_URL` hardcoded, `VITE_OMNIVISION_API_URL` unconsumed | Source Evidence | High |
| A05-E015 | `settings.py:49-51` | `env_file = ".env"` — single env file, no profile-specific override | Source Evidence | High |
| A05-E016 | `config_validator.py:17-19` | Valid profile list `["development", "demo", "production"]` — validates but only BLIP_MODEL uses it | Source Evidence | High |
| A05-E017 | `.env:26` | `MAX_UPLOAD_SIZE_MB=12` — defined but unused, `image_service.py` uses hardcoded 12MB | Source Evidence | High |
| A05-E018 | `docker-compose.yml:32` | `VITE_OMNIVISION_API_URL=http://backend:8000/api/v1` — set but unconsumed by frontend | Derived Inference | Medium |
| A05-E019 | `logging_config.py:36-65` | Logging configured for `omnivision` and `uvicorn` loggers only — other loggers get default config | Source Evidence | High |

## 6. Verified Observations

### 6.1 Settings Definition

- `Settings` class uses `pydantic-settings.BaseSettings` with `env_file = ".env"` (A05-E015)
- Several fields bypass pydantic resolution using direct `os.getenv()` calls: `PROFILE` (A05-E001), `GROUNDING_SIMILARITY_THRESHOLD` (A05-E004)
- `BLIP_MODEL` and `ACTIVE_KNOWLEDGE_PACKS` are `@property` methods, not pydantic fields (A05-E002, A05-E005)
- `Config.extra = "allow"` (A05-E007) — silently ignores unknown environment variables (including typos)

### 6.2 Profile System

- `BLIP_MODEL` is the only setting that varies by profile (A05-E002): development → base model, demo/production → blip2-opt-2.7b
- `CLIP_MODEL`, `TRANSLATION_MODEL`, `TTS_MODEL` have no profile awareness (A05-E003)
- `config_validator.py:17-19` validates profile but profile affects almost nothing (A05-E016)

### 6.3 Dead Configuration

- `MAX_UPLOAD_SIZE_MB` (A05-E006) — defined in settings, set in `.env` (A05-E017), but `image_service.py` hardcodes `12 * 1024 * 1024` (A05-E008)
- `API_BASE_URL` — defined in settings, never consumed by backend code
- `DATABASE_URL` (A05-E012) — defined in `.env` but never consumed

### 6.4 Threshold Inconsistency

- `GROUNDING_SIMILARITY_THRESHOLD` defaults to 0.75 (A05-E004)
- Service reads it (A05-E009) and passes to response builder
- But actual grounding logic uses hardcoded thresholds: >= 0.8 (high), >= 0.6 (medium), >= 0.4 (low) (A05-E010)
- Configured value (0.75) is only returned in API responses, never used in decision logic

### 6.5 Knowledge Pack Configuration

- `ACTIVE_KNOWLEDGE_PACKS` is a list type (A05-E005)
- Code only reads `self.active_packs[0]` (A05-E013) — ignores all but first pack
- `config_validator.py` validates each pack exists, but runtime only uses the first

### 6.6 Environment Variable Precedence

- Mix of resolution strategies creates unclear precedence:
  - Pydantic fields read from `.env` file (A05-E015)
  - `@property` fields call `os.getenv()` directly (A05-E002, A05-E005)
  - Some fields use `os.getenv()` in their default value (A05-E001, A05-E004)
- Precedence: direct `os.getenv()` in property → OS env var → pydantic field (from .env) → pydantic default

### 6.7 Example vs Actual Configuration

- `.env.example:23` recommends `ai4bharat/indictrans2-en-indic-dist-200M` (A05-E011)
- `.env:10` uses `facebook/nllb-200-distilled-600M` — different model entirely
- Code in `translation_service.py` is NLLB-specific (uses `tokenizer.src_lang = "eng_Latn"`, NLLB API)

### 6.8 Logging Configuration

- `logging_config.py` configures `JSONFormatter` with structured fields (A05-E019)
- Only `omnivision` and `uvicorn` loggers are configured — other loggers (e.g., `transformers`, `PIL`, `faiss`) inherit default config
- Log level hardcoded to `INFO` — no environment variable for level override

## 7. Assessments

The configuration system has evolved organically rather than being designed as a coherent whole. The mix of pydantic-settings fields, direct `os.getenv()` calls, and `@property` methods creates unpredictable precedence. The profile system is essentially vestigial — only one setting varies by profile despite the startup validator treating it as critical. Several configuration values are defined but dead (never consumed), while critical values like image size limits are hardcoded in the service layer.

## 8. Findings

### CFG-001 — High: Partially implemented profile system

---
finding_id:         CFG-001
category:           Configuration Design
evidence_ids:       A05-E001, A05-E002, A05-E003, A05-E016
files:              settings.py:10-28; config_validator.py:17-19
type:               Configuration
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Multi-profile deployment test
---

**Verified facts**:
- `config_validator.py:17-19` enforces that `PROFILE` must be one of `["development", "demo", "production"]` (A05-E016)
- `BLIP_MODEL` is the only setting that varies by profile (A05-E002): development → blip-base, demo/production → blip2
- `CLIP_MODEL`, `TRANSLATION_MODEL`, `TTS_MODEL` are flat defaults with no profile awareness (A05-E003)
- The `demo` and `production` profiles are functionally identical for `BLIP_MODEL` (both use blip2) (A05-E002)

**Assessment**: The profile system is partially implemented. Only one of four model settings respects the profile. The `demo` and `production` profiles are indistinguishable. If the intent is for profiles to select appropriate model configurations (e.g., production uses different translation model than development), this is not implemented. A developer switching from `development` to `demo` profile may expect all models to upgrade accordingly.

**Requirement traceability**: None documented.

---

### CFG-002 — High: Mixed configuration resolution strategy

---
finding_id:         CFG-002
category:           Configuration Design
evidence_ids:       A05-E001, A05-E002, A05-E004, A05-E005, A05-E007
files:              settings.py
type:               Configuration
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Env var override test across all resolution paths
---

**Verified facts**:
- `PROFILE` uses `os.getenv("PROFILE", "development")` directly (A05-E001) — bypasses pydantic env_file
- `BLIP_MODEL` is a `@property` that calls `os.getenv("BLIP_MODEL")` before profile logic (A05-E002)
- `GROUNDING_SIMILARITY_THRESHOLD` uses `os.getenv()` + `float()` (A05-E004) — bypasses pydantic type coercion
- `ACTIVE_KNOWLEDGE_PACKS` is a `@property` with `json.loads(os.getenv(...))` (A05-E005)
- `CLIP_MODEL` is a plain pydantic field using `os.getenv("CLIP_MODEL", "...")` as default (A05-E003)
- `Config.extra = "allow"` (A05-E007) — silently ignores unknown env vars, including typos

**Assessment**: The settings class uses three different resolution strategies: (1) direct `os.getenv()` in property methods, (2) `os.getenv()` in field default values, (3) pydantic-settings env_file resolution. Each has different precedence rules. A variable set in `.env` may or may not be overridable by a system environment variable depending on which strategy is used. This makes configuration behavior unpredictable in production deployment where env vars come from Docker/Kubernetes. `extra = "allow"` compounds this by silently ignoring typos — `BLIP_MDOEL` would be silently accepted.

**Requirement traceability**: None documented.

---

### CFG-003 — Medium: MAX_UPLOAD_SIZE_MB defined but hardcoded in service

---
finding_id:         CFG-003
category:           Dead Configuration
evidence_ids:       A05-E006, A05-E008, A05-E017
files:              settings.py:47; image_service.py:15; .env:26
type:               Configuration
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - ImageService
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Config value-to-service trace test
---

**Verified facts**:
- `settings.py:47` defines `MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", 10))` (A05-E006)
- `.env:26` sets `MAX_UPLOAD_SIZE_MB=12` (A05-E017)
- `image_service.py:15` hardcodes `self.max_size = 12 * 1024 * 1024` — never references settings (A05-E008)

**Assessment**: The configuration value is defined, documented, and set in `.env` — but never consumed. The service layer hardcodes a duplicate value. Changing `MAX_UPLOAD_SIZE_MB` in `.env` has no effect. This is both a configuration defect and a maintenance risk (two values to keep in sync).

---

### CFG-004 — Medium: Grounding threshold configured but unused in logic

---
finding_id:         CFG-004
category:           Dead Configuration
evidence_ids:       A05-E004, A05-E009, A05-E010
files:              settings.py:34; grounding_service.py:12,45-68; response_builder.py:32
type:               Configuration
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - GroundingService
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Threshold value trace through decision logic
---

**Verified facts**:
- `settings.py:34` defines `GROUNDING_SIMILARITY_THRESHOLD` defaulting to 0.75 (A05-E004)
- `grounding_service.py:12` reads it: `self.threshold = settings.GROUNDING_SIMILARITY_THRESHOLD` (A05-E009)
- `grounding_service.py:45-68` uses hardcoded thresholds: `if score >= 0.8`, `elif score >= 0.6`, `elif score >= 0.4` (A05-E010)
- `response_builder.py:32` returns `threshold_used=settings.GROUNDING_SIMILARITY_THRESHOLD` — reports 0.75 but logic uses 0.8/0.6/0.4
- `frontend_transformer.py:59` also uses the setting for display

**Assessment**: The configured threshold (0.75) is never used in the grounding decision logic. The actual thresholds (0.8, 0.6, 0.4) are hardcoded in the method. The setting is only returned in API responses, creating a discrepancy between the reported threshold and the actual behavior. A user setting `GROUNDING_SIMILARITY_THRESHOLD=0.9` would see it reported in responses but the grounding behavior would remain unchanged.

---

### CFG-005 — Medium: Model mismatch between example env and actual config

---
finding_id:         CFG-005
category:           Configuration Drift
evidence_ids:       A05-E011
files:              .env.example:23; .env:10; translation_service.py:31-50
type:               Configuration
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - TranslationService
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Model compatibility verification
---

**Verified facts**:
- `.env.example:23` recommends `TRANSLATION_MODEL=ai4bharat/indictrans2-en-indic-dist-200M` (A05-E011)
- `.env:10` uses `TRANSLATION_MODEL=facebook/nllb-200-distilled-600M`
- `translation_service.py:31-50` uses NLLB-specific API: `tokenizer.src_lang = "eng_Latn"`, `tokenizer.lang_code_to_id[code]`
- NLLB and IndicTrans2 use different tokenizer APIs, different language codes, different special tokens

**Assessment**: The example configuration references a completely different model than what the code supports. If a developer copies `.env.example` to `.env` and runs the application, translation will fail because the code uses NLLB-specific API calls. IndicTrans2 uses a different tokenizer interface, different language code format, and different generation parameters. The service layer is NLLB-specific and cannot work with IndicTrans2 without code changes.

---

### CFG-006 — Medium: ACTIVE_KNOWLEDGE_PACKS list but only first pack used

---
finding_id:         CFG-006
category:           Configuration Design
evidence_ids:       A05-E005, A05-E013
files:              settings.py:37-39; retrieval_service.py:40-44
type:               Configuration
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Architecture Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - RetrievalService
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Backend
verification:       Multi-pack loading test
---

**Verified facts**:
- `settings.py:37-39` defines `ACTIVE_KNOWLEDGE_PACKS` as `List[str]` parsed from JSON env var (A05-E005)
- `retrieval_service.py:43` only reads `self.active_packs[0]` — ignores all but the first pack (A05-E013)
- `config_validator.py:42-48` validates that ALL packs in the list exist on disk, then runtime only uses the first

**Assessment**: The configuration schema supports multiple knowledge packs, but the runtime implementation ignores everything after the first. This is architecture debt — the interface was designed for multi-pack support but never implemented. The startup validator also validates packs that will never be loaded, creating a misleading startup experience (you can configure a pack, see it pass validation, but it has no effect).

---

### CFG-007 — Medium: Logger configuration gaps

---
finding_id:         CFG-007
category:           Configuration
evidence_ids:       A05-E019
files:              logging_config.py:36-65
type:               Configuration
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
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Log output review at runtime
---

**Verified facts**:
- `logging_config.py:53-63` configures only `omnivision` and `uvicorn` loggers (A05-E019)
- Third-party loggers (`transformers`, `PIL`, `faiss`, `urllib3`, `httpx`) inherit root logger defaults
- Log level hardcoded to `INFO` — no environment variable override

**Assessment**: Third-party library loggers use default Python logging (WARNING level, plain-text format, stderr). This means debug information from HuggingFace transformers, PIL, and FAISS goes to stderr in a different format than the application's structured JSON logs. In production, this creates inconsistent log output. No mechanism exists to increase log level for debugging without code changes.

---

### CFG-008 — Medium: Frontend API URL configuration dead

---
finding_id:         CFG-008
category:           Dead Configuration
evidence_ids:       A05-E014, A05-E018
files:              api.ts:3; frontend/.env:1; docker-compose.yml:32
type:               Configuration
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Not Required
subsystems:
  - Frontend
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Build-time URL substitution test
---

**Verified facts**:
- `api.ts:3` hardcodes `const BASE_URL = "http://localhost:8000/api/v1"` (A05-E014)
- `frontend/.env:1` defines `VITE_OMNIVISION_API_URL=http://localhost:8000/api/v1` — never consumed
- `docker-compose.yml:32` sets `VITE_OMNIVISION_API_URL=http://backend:8000/api/v1` — never consumed

**Assessment**: The environment variable `VITE_OMNIVISION_API_URL` is set in two locations (`.env` and `docker-compose.yml`) but never read by the application. The hardcoded URL in `api.ts` is the only value used. This breaks Docker deployment where the backend hostname is `backend`, not `localhost`. Duplicate finding with SEC-010; retained here as the correct domain.

---

### CFG-009 — Medium: DATABASE_URL is dead configuration placeholder

---
finding_id:         CFG-009
category:           Dead Configuration
evidence_ids:       A05-E012
files:              .env:23
type:               Configuration
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Informational
priority:           P3
regression_test:    Not Required
subsystems:
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   None
owner:              Backend
verification:       Backend code search
---

**Verified facts**:
- `.env:23` defines `DATABASE_URL=postgresql://user:password@localhost:5432/omnivision` (A05-E012)
- No backend code references `DATABASE_URL` or any database connection

**Assessment**: This is a v2.0 placeholder with no current function. It contains embedded credentials (username and password) in the `.env` file. While `.env` is gitignored, the presence of placeholder credentials in an active configuration file may mislead developers into thinking a database connection is required. Remove when unused, or add when database functionality is implemented.

---

### CFG-010 — Medium: Missing logging level configuration

---
finding_id:         CFG-010
category:           Configuration
evidence_ids:       A05-E019
files:              logging_config.py:49,56,61; .env.example; .env
type:               Configuration
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
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       LOG_LEVEL env var override test
---

**Verified facts**:
- `logging_config.py` hardcodes log level to `INFO` for all configured loggers
- No `LOG_LEVEL` environment variable or settings field exists
- No mechanism to enable `DEBUG` level without code changes

**Assessment**: Debugging production issues requires log level changes. Without a configuration mechanism (env var or settings field), developers must modify code to enable debug logging. This should be configurable via `LOG_LEVEL` environment variable in `.env`.

---

### CFG-011 — Low: Settings.Config.extra = "allow" masks typos

---
finding_id:         CFG-011
category:           Configuration Design
evidence_ids:       A05-E007
files:              settings.py:49-51
type:               Configuration
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P3
regression_test:    Not Required
subsystems:
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Env var typo test
---

**Verified facts**:
- `settings.py:50` sets `extra = "allow"` (A05-E007)
- Any environment variable with any name is silently accepted without error

**Assessment**: Setting `extra = "allow"` means a typo like `BLIP_MDOEL=value` is silently accepted. The developer expects `BLIP_MODEL` to be set, but pydantic does not warn about `BLIP_MDOEL`. The `property`-based fields (A05-E002, A05-E005) also use `os.getenv()` directly, so they don't participate in pydantic's validation at all. This creates a configuration surface where errors are invisible.

---

### CFG-012 — Low: No environment variable documentation for all settings

---
finding_id:         CFG-012
category:           Documentation
evidence_ids:       A05-E001, A05-E002, A05-E003, A05-E004, A05-E005
files:              .env.example; settings.py
type:               Configuration
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P3
regression_test:    Not Required
subsystems:
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Env file completeness check
---

**Verified facts**:
- `.env.example` documents: PROFILE, FASTAPI_HOST, FASTAPI_PORT, API_BASE_URL, CLIP_MODEL, TRANSLATION_MODEL, TTS_MODEL, GROUNDING_SIMILARITY_THRESHOLD, ACTIVE_KNOWLEDGE_PACKS, UPLOAD_DIR, AUDIO_DIR, KNOWLEDGE_BASE_DIR, MAX_UPLOAD_SIZE_MB
- `.env.example` does NOT document: BLIP_MODEL (profile-based, documented in comment), APP_NAME, DATABASE_URL (present in `.env` but not in `.env.example`)
- `settings.py` defines additional fields not in `.env.example`: APP_NAME, API_BASE_URL (in example but commented indirectly)

**Assessment**: Most settings are documented in `.env.example`, but the file is not exhaustive. `DATABASE_URL` exists in `.env` but not in `.env.example`, so a new developer cloning the repo won't know it should be configured. Minor documentation gap.

---

### CFG-013 — Low: No settings.yaml despite methodology reference

---
finding_id:         CFG-013
category:           Configuration
evidence_ids:       A05-E015
files:              settings.py; .env; .env.example
type:               Configuration
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Informational
priority:           P3
regression_test:    Not Required
subsystems:
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       Config file audit
---

**Verified facts**:
- All configuration is via `.env` file and environment variables
- No `settings.yaml` or `settings.yml` file exists in the project
- The methodology mentions `settings.yaml` as the configuration system, but implementation uses `.env`

**Assessment**: The code uses `.env` (via `pydantic-settings`) rather than YAML. This is not a defect but a discrepancy with the documented methodology. If YAML-based configuration is desired for complex structures (like profile-specific model configs, multi-pack configurations), it would need to be implemented.

---

### CFG-014 — Low: Pre-commit hooks only cover Python formatting

---
finding_id:         CFG-014
category:           Configuration
evidence_ids:       A05-E016
files:              .pre-commit-config.yaml
type:               Configuration
severity:           Low
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P3
regression_test:    Not Required
subsystems:
  - Build
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              DevOps
verification:       Pre-commit config review
---

**Verified facts**:
- `.pre-commit-config.yaml` only runs `black` (formatter) and `ruff` (linter) on Python files
- No hooks for: YAML linting, TOML validation, shellcheck, secret scanning, trailing whitespace, end-of-file fixer, JSON validation

**Assessment**: Pre-commit hooks provide value beyond Python code. Missing hooks allow misformatted configuration files (YAML, TOML, JSON) and potential secret commits.

---

## 9. Configuration State Inventory

| Setting | Defined In | Consumed By | Profile Aware? | Dead? | Evidence |
|---|---|---|---|---|---|
| `PROFILE` | `settings.py:10` | `config_validator.py`, `settings.BLIP_MODEL` | N/A | No | A05-E001 |
| `BLIP_MODEL` | `settings.py:17-28` | `model_manager.py:46` | Yes | No | A05-E002 |
| `CLIP_MODEL` | `settings.py:30` | `model_manager.py:48` | No | No | A05-E003 |
| `TRANSLATION_MODEL` | `settings.py:31` | `model_manager.py:50` | No | No | A05-E003 |
| `TTS_MODEL` | `settings.py:32` | `model_manager.py:52` | No | No | A05-E003 |
| `GROUNDING_SIMILARITY_THRESHOLD` | `settings.py:34` | `grounding_service.py:12`, `response_builder.py:32` | No | **Logic uses hardcoded 0.8/0.6/0.4** | A05-E004 |
| `ACTIVE_KNOWLEDGE_PACKS` | `settings.py:37-39` | `retrieval_service.py:43` (first only) | No | **Partial (list >1 ignored)** | A05-E005 |
| `MAX_UPLOAD_SIZE_MB` | `settings.py:47` | **Nowhere** — `image_service.py` hardcodes | No | **Yes — dead** | A05-E006 |
| `API_BASE_URL` | `settings.py:13` | **Nowhere** | No | **Yes — dead** | |
| `FASTAPI_HOST` | `settings.py:11` | `main.py:98` | No | No | |
| `FASTAPI_PORT` | `settings.py:12` | `main.py:98` | No | No | |
| `UPLOAD_DIR` | `settings.py:42` | `main.py:53` | No | No | |
| `AUDIO_DIR` | `settings.py:43` | `main.py:54`, `tts_service.py:16` | No | No | |
| `KNOWLEDGE_BASE_DIR` | `settings.py:44` | `retrieval_service.py:16`, `config_validator.py` | No | No | |
| `DATABASE_URL` | `.env:23` | **Nowhere** | No | **Yes — v2.0 placeholder** | A05-E012 |
| `VITE_OMNIVISION_API_URL` | `frontend/.env:1` | **Nowhere** — `api.ts` hardcodes | No | **Yes — dead** | A05-E014 |
| `LOG_LEVEL` | Not defined | N/A | N/A | **Not implemented** | A05-E019 |

## 10. Runtime Validation Appendix

| ID | Hypothesis | Why Static Insufficient | Recommended Method |
|---|---|---|---|
| RV-CFG-01 | Changing `GROUNDING_SIMILARITY_THRESHOLD` in `.env` has no effect on grounding behavior | Code reads setting but decision logic is hardcoded — need to verify the value path | Change to 0.5, send request with similarity 0.7, check behavior against expected threshold |
| RV-CFG-02 | Profile switch from development to demo loads different BLIP model | `BLIP_MODEL` property references profile, but HF cache may serve same model | Switch profile, verify loaded model ID in logs |
| RV-CFG-03 | Docker deployment frontend cannot reach backend due to hardcoded localhost URL | `api.ts` hardcodes localhost, Docker internal networking uses hostname `backend` | Build frontend image, deploy with docker-compose, verify API calls resolve |

## 11. Risk Register Mapping

| Risk ID | Finding | Severity | Confidence | Priority | Description |
|---|---|---|---|---|---|
| RR-05-001 | CFG-001 | High | High | P1 | Profile system partially implemented — only BLIP_MODEL varies by profile |
| RR-05-002 | CFG-002 | High | High | P1 | Mixed config resolution strategy creates unpredictable env var precedence |
| RR-05-003 | CFG-003 | Medium | High | P2 | MAX_UPLOAD_SIZE_MB defined but hardcoded in service |
| RR-05-004 | CFG-004 | Medium | High | P2 | Grounding threshold configured (0.75) but logic uses hardcoded values (0.8/0.6/0.4) |
| RR-05-005 | CFG-005 | Medium | High | P2 | .env.example recommends IndicTrans2 but code is NLLB-specific |
| RR-05-006 | CFG-006 | Medium | High | P2 | ACTIVE_KNOWLEDGE_PACKS list — only first pack used at runtime |
| RR-05-007 | CFG-007 | Medium | Medium | P2 | Logger configuration only covers omnivision and uvicorn loggers |
| RR-05-008 | CFG-008 | Medium | High | P2 | Frontend VITE_OMNIVISION_API_URL dead — breaks Docker deployment |
| RR-05-009 | CFG-009 | Medium | High | P3 | DATABASE_URL placeholder with embedded credentials, never consumed |
| RR-05-010 | CFG-010 | Medium | High | P2 | No LOG_LEVEL configuration — debug requires code change |
| RR-05-011 | CFG-011 | Low | High | P3 | extra = "allow" silently accepts env var typos |
| RR-05-012 | CFG-012 | Low | High | P3 | .env.example does not document all settings |
| RR-05-013 | CFG-013 | Low | High | P3 | No settings.yaml despite methodology reference |
| RR-05-014 | CFG-014 | Low | Medium | P3 | Pre-commit hooks only cover Python formatting |

## 12. Cross-Audit References

| This Finding | Audit 01 (Architecture) | Audit 03 (Mem/Conc) | Audit 04 (Security) | Risk Register |
|---|---|---|---|---|
| CFG-003 | — | — | SEC-006 (hardcoded max_size) | RR-05-003 |
| CFG-004 | — | — | — | RR-05-004 |
| CFG-005 | — | — | — | RR-05-005 |
| CFG-006 | — | — | — | RR-05-006 |
| CFG-008 | — | — | SEC-010 (same finding) | RR-05-008 |
| CFG-009 | — | — | — | RR-05-009 |

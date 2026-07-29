# Audit 09 — Dependency & Build

---
audit_id:            audit_09_dependency_build
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               Dependency management, build reproducibility, Docker configuration, CI/CD pipeline, linting tooling, security scanning
---

## 1. Executive Summary

Analysis of 10 build/dependency files reveals **10 findings: 4 Critical, 3 High, 2 Medium, 1 Low**. The most critical issues are: **no CI/CD pipeline exists** (zero automation for linting, testing, building, or deploying), **no backend lock file** (non-reproducible pip installs), **no `.dockerignore`** (Docker builds send entire working tree as context), and **no security scanning** (known CVEs like numpy CVE-2024-12905 go undetected). Build system maturity is rated **2/5**.

| Metric | Count |
|---|---|
| Total findings | 10 |
| Confirmed defects | 6 |
| Design debt | 2 |
| Informational | 2 |
| Critical severity | 4 |
| High severity | 3 |
| Medium severity | 2 |
| Low severity | 1 |
| P0 priority | 2 |
| P1 priority | 3 |
| P2 priority | 4 |
| P3 priority | 1 |

## 2. Scope

| In Scope | Out of Scope |
|---|---|
| `requirements*.txt` (backend) | Third-party library source code |
| `frontend/package.json` + `frontend/bun.lock` | Frontend build tools internals |
| `Dockerfile` (root) + `frontend/Dockerfile` | Kubernetes/Helm configuration |
| `docker-compose.yml` | Cloud deployment (ECS, GKE, etc.) |
| `.github/workflows/` | Terraform / Pulumi infrastructure |
| `.pre-commit-config.yaml` | |
| `pyproject.toml` | |

## 3. Audit Limitations

| Limitation | Impact on Findings |
|---|---|
| No `pip-audit` runtime | Cannot enumerate all known CVEs in transitive dependencies |
| No Docker build execution | Cannot verify layer caching or image size at runtime |
| No npm audit runtime | Cannot enumerate frontend transitive vulnerability surface |

## 4. Evidence Inventory

| ID | Location | Observation | Type | Confidence |
|---|---|---|---|---|
| A09-E001 | `requirements.txt` | 15 dependencies, all unpinned (`>=` ranges only) | Source Evidence | High |
| A09-E002 | `requirements-base.txt` | 18 dependencies, 14 pinned, 3 torch deps unpinned (`>=2.1.0`) | Source Evidence | High |
| A09-E003 | Root directory | No `poetry.lock`, `Pipfile.lock`, or `constraints.txt` exists | Source Evidence | High |
| A09-E004 | `frontend/bun.lock` | Lock file present (Bun v1 format) | Source Evidence | High |
| A09-E005 | `frontend/package.json` | 54 direct deps (`^` range), 17 dev deps (`^` range) | Source Evidence | High |
| A09-E006 | `.github/workflows/` | Directory does not exist — no CI/CD pipeline | Source Evidence | High |
| A09-E007 | `Dockerfile:21-24` | `COPY . .` before `RUN mkdir` — layer cache invalidation | Source Evidence | High |
| A09-E008 | Root directory | No `.dockerignore` file exists | Source Evidence | High |
| A09-E009 | `Dockerfile:29` | No `HEALTHCHECK` instruction; runs as root | Source Evidence | High |
| A09-E010 | `frontend/Dockerfile` | No `HEALTHCHECK` instruction | Source Evidence | High |
| A09-E011 | Root directory | No `dependabot.yml` or security scanning config | Source Evidence | High |
| A09-E012 | `requirements-base.txt:13` | `numpy==1.26.2` pinned — CVE-2024-12905 present | Source Evidence | High |
| A09-E013 | `pyproject.toml:1-10` | Black + Ruff configured for backend | Source Evidence | High |
| A09-E014 | `.pre-commit-config.yaml:2-12` | Pre-commit runs Black with `--fix` and Ruff with `--fix` | Source Evidence | High |
| A09-E015 | `frontend/eslint.config.js` | ESLint configured with TS + React + Prettier | Source Evidence | High |
| A09-E016 | `docker-compose.yml:10` | Mounts `.env` file without fallback | Source Evidence | High |
| A09-E017 | `docker-compose.yml:16-22` | GPU reservations require NVIDIA driver + nvidia-container-toolkit | Source Evidence | High |
| A09-E018 | `requirements-cuda.txt` | Not a pip requirements file — contains only comments/instructions | Source Evidence | High |
| A09-E019 | `Dockerfile:6-11` | `apt-get install` without `--no-install-recommends` | Source Evidence | High |
| A09-E020 | `Dockerfile:14` | `pip install torch` without `--no-cache-dir` | Source Evidence | High |

## 5. Verified Observations

### 5.1 Backend Dependencies

- `requirements.txt`: 15 deps, all unpinned — development convenience file (A09-E001)
- `requirements-base.txt`: 18 deps, 14 pinned, 3 torch deps floating (`>=2.1.0`) (A09-E002)
- No lock file or constraints file exists (A09-E003)
- `numpy==1.26.2` pinned — affected by CVE-2024-12905 (A09-E012)
- `requirements-cuda.txt` is a guide/comments file, not valid pip format (A09-E018)

### 5.2 Frontend Dependencies

- 54 direct deps, 17 dev deps, all `^` (caret) ranges (A09-E005)
- `bun.lock` lock file committed — good reproducibility (A09-E004)
- `nitro@3.0.260603-beta` is a pre-release beta dependency — stability risk
- 8+ unused dependencies identified in Audit 8 (FE-005)

### 5.3 CI/CD Pipeline

- No `.github/workflows/` directory exists (A09-E006)
- Zero automation: no lint, no test, no build, no deploy runs automatically
- No GitHub Actions, GitLab CI, Jenkins, or any CI configuration

### 5.4 Docker Configuration

| Aspect | Backend (`Dockerfile`) | Frontend (`frontend/Dockerfile`) |
|---|---|---|
| Base image | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04` (~2.9GB) | `node:20-alpine` → `nginx:alpine` |
| Multi-stage | No | Yes |
| Non-root user | No (root) | No (nginx default) |
| `HEALTHCHECK` | None (A09-E009) | None (A09-E010) |
| `.dockerignore` | None (A09-E008) | None (A09-E008) |
| `apt-get` flags | No `--no-install-recommends` (A09-E019) | N/A |
| pip cache cleanup | No `--no-cache-dir` (A09-E020) | N/A |

### 5.5 Linting and Formatting

- Backend: Black (line-length=100) + Ruff (E/F/I/W, ignore E501) in pre-commit (A09-E013, A09-E014)
- Frontend: ESLint (TS + React + Prettier) + Prettier (width=100) — no pre-commit hook (A09-E015)
- No frontend linting in pre-commit — only runs if developer manually runs ESLint

### 5.6 Security Scanning

- No Dependabot, no Snyk, no `pip-audit`, no `npm audit`, no Trivy (A09-E011)
- Known vulnerable `numpy==1.26.2` (CVE-2024-12905) in pinned deps (A09-E012)
- No container image scanning

## 6. Assessments

The build system shows awareness of good practices (pre-commit with Black+Ruff, frontend lock file, multi-stage Docker for frontend) but has fundamental gaps. The lack of CI/CD is the single most impactful finding — without it, every change requires manual verification, and there is no enforcement of linting, testing, or security checks. The Docker backend image lacks basic production hygiene (health check, non-root user, `.dockerignore`).

## 7. Findings

### BL-001 — Critical: No CI/CD Pipeline

---
finding_id:         BL-001
category:           CI/CD
evidence_ids:       A09-E006
files:              .github/workflows/ (directory does not exist)
type:               Dependency & Build
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P0
regression_test:    Not Applicable
subsystems:
  - CI/CD
  - Build
requirement_id:     None
requirement_status: None
estimated_effort:   Large
owner:              DevOps
verification:       PR triggers lint + test + build in CI
---

**Verified facts**:
- No `.github/workflows/` directory exists (A09-E006)
- No GitHub Actions, GitLab CI, Jenkinsfile, or any CI configuration
- Pre-commit hooks exist but are local-only — no server-side enforcement

**Assessment**: There is zero automation for linting, testing, building, or deploying. Every change requires manual execution. No PR gate blocks broken code. This is the single largest infrastructure gap.

---

### BL-002 — Critical: No Backend Lock File — Non-Reproducible Installs

---
finding_id:         BL-002
category:           Reproducibility
evidence_ids:       A09-E001, A09-E002, A09-E003
files:              requirements.txt; requirements-base.txt
type:               Dependency & Build
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P0
regression_test:    Required
subsystems:
  - Build
  - Deployment
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Backend
verification:       pip install on two different dates produces identical hashes
---

**Verified facts**:
- `requirements.txt`: 15 deps, all `>=` ranges (A09-E001)
- `requirements-base.txt`: 3 torch deps unpinned (`>=2.1.0`) (A09-E002)
- No `poetry.lock`, `Pipfile.lock`, `constraints.txt`, or `pip freeze > requirements-lock.txt` (A09-E003)

**Assessment**: Two pip installs at different times can resolve different transitive dependency versions. Combined with unpinned torch versions, this creates non-reproducible builds. A CI pipeline cannot produce deterministic builds.

---

### BL-003 — Critical: No `.dockerignore` — Build Context Bloat

---
finding_id:         BL-003
category:           Docker
evidence_ids:       A09-E008
files:              .dockerignore (does not exist)
type:               Dependency & Build
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Not Required
subsystems:
  - Docker
  - Build
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              DevOps
verification:       Docker build context size before and after
---

**Verified facts**:
- No `.dockerignore` file in root directory (A09-E008)
- Entire project tree (including `node_modules/`, `__pycache__/`, `.venv/`, `venv/`, `.git/`) is sent to Docker daemon on every build via `COPY . .`
- `.gitignore` excludes some of these from git but not from Docker context

**Assessment**: Slow Docker builds, large context uploads to remote builders, and risk of accidental inclusion of secrets or unnecessary files in the image.

---

### BL-004 — Critical: No Security Scanning — Known CVEs Present

---
finding_id:         BL-004
category:           Security
evidence_ids:       A09-E011, A09-E012
files:              requirements-base.txt:13; .github/ (no dependabot.yml)
type:               Dependency & Build
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Not Required
subsystems:
  - Build
  - Security
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              DevOps
verification:       Security scan produces no findings for critical CVEs
---

**Verified facts**:
- No Dependabot, Snyk, pip-audit, npm audit, or Trivy configuration (A09-E011)
- `numpy==1.26.2` pinned — CVE-2024-12905 present (A09-E012)
- No vulnerability scanning in any build step or CI pipeline

**Assessment**: Known vulnerable dependencies are shipped in every build. Without automated scanning, the team will not detect new CVEs in any of the 60+ direct dependencies and their transitive chains.

---

### BL-005 — High: Docker Backend Image Lacks Health Check and Runs as Root

---
finding_id:         BL-005
category:           Docker
evidence_ids:       A09-E009
files:              Dockerfile:29
type:               Dependency & Build
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Not Required
subsystems:
  - Docker
  - Deployment
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              DevOps
verification:       Container status in orchestrator with and without health check
---

**Verified facts**:
- `Dockerfile:29`: `CMD ["uvicorn"...]` runs as root (A09-E009)
- No `HEALTHCHECK` instruction in backend or frontend Dockerfile (A09-E009, A09-E010)
- Container runtime has no way for orchestrator to detect process health

**Assessment**: Root container processes violate the principle of least privilege. Missing health checks mean Kubernetes/Docker cannot detect when the application is alive but not serving (e.g., during model loading or after OOM). Also noted in OBS-003.

---

### BL-006 — High: Docker Layer Cache Invalidation

---
finding_id:         BL-006
category:           Docker
evidence_ids:       A09-E007
files:              Dockerfile:21-24
type:               Dependency & Build
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - Docker
  - Build
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              DevOps
verification:       Build timing with and without layer ordering fix
---

**Verified facts**:
- `Dockerfile:21`: `COPY . .` copies entire project
- `Dockerfile:24`: `RUN mkdir -p /app/data/knowledge_base` — modifies filesystem after copy
- Any change to `RUN mkdir` order invalidates the pip install layer cache

**Assessment**: Every rebuild re-installs all Python packages because the `COPY . .` layer changes. Fix: reorder to `RUN mkdir` before `COPY . .`.

---

### BL-007 — High: No Docker Compose .env Fallback

---
finding_id:         BL-007
category:           Docker
evidence_ids:       A09-E016
files:              docker-compose.yml:10
type:               Dependency & Build
severity:           High
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - Docker
  - Configuration
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              DevOps
verification:       `docker-compose up` without .env file
---

**Verified facts**:
- `docker-compose.yml:10`: mounts `.env` file via `env_file: .env`
- If `.env` is missing, Docker Compose exits with error

**Assessment**: New developers or CI environments without `.env` cannot start via Docker Compose. A `.env.example` exists but is not automatically copied.

---

### BL-008 — Medium: Frontend Linting Not in Pre-Commit

---
finding_id:         BL-008
category:           Linting
evidence_ids:       A09-E015
files:              .pre-commit-config.yaml
type:               Dependency & Build
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - Frontend
  - Linting
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Pre-commit run on frontend change
---

**Verified facts**:
- ESLint + Prettier configured in `eslint.config.js` and `.prettierrc` (A09-E015)
- No pre-commit hook for ESLint or Prettier
- `.pre-commit-config.yaml` only configures Black and Ruff for backend

**Assessment**: Frontend linting is not enforced on commit. Developers must remember to run ESLint manually.

---

### BL-009 — Medium: Docker apt-get Install Lacks Best Practices

---
finding_id:         BL-009
category:           Docker
evidence_ids:       A09-E019, A09-E020
files:              Dockerfile:6-14
type:               Dependency & Build
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Informational
priority:           P2
regression_test:    Not Required
subsystems:
  - Docker
  - Build
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              DevOps
verification:       Image size comparison with and without flags
---

**Verified facts**:
- `apt-get install` without `--no-install-recommends` (A09-E019) — installs unnecessary packages
- `pip install` without `--no-cache-dir` (A09-E020) — pip cache retained in image layer
- No `apt-get clean` or `rm -rf /var/lib/apt/lists/*` after install

**Assessment**: These are Dockerfile best practice issues that increase image size unnecessarily.

---

### BL-010 — Low: Pre-release Frontend Dev Dependency

---
finding_id:         BL-010
category:           Stability
evidence_ids:       A09-E005
files:              frontend/package.json
type:               Dependency & Build
severity:           Low
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Informational
priority:           P3
regression_test:    Not Required
subsystems:
  - Frontend
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Check for stable release availability
---

**Verified facts**:
- `nitro@3.0.260603-beta` is a pre-release/beta dependency in frontend `devDependencies`

**Assessment**: Beta dependencies may introduce breaking changes on minor updates. Should be pinned exactly or migrated to stable.

---

## 8. Build System Maturity Score

| Category | Score | Max | Justification |
|---|---|---|---|
| Reproducibility | 0.5 | 1 | Frontend has `bun.lock`; backend has NO lock file |
| Docker best practices | 0.5 | 1 | Multi-stage for frontend, but no `.dockerignore`, no health check, no non-root user, no pip cache cleanup |
| CI/CD | 0 | 1 | No CI/CD pipeline at all |
| Linting/formatting | 1 | 1 | Pre-commit with Black+Ruff for backend; ESLint+Prettier for frontend |
| Security scanning | 0 | 1 | No Dependabot, no pip-audit, no npm audit, no Snyk |
| **Total** | **2** | **5** | |

## 9. Dependency Inventory

### Backend

| Dependency | Pinned? | Notes |
|---|---|---|
| torch / torchvision / torchaudio | No (`>=2.1.0`) | Floating version, CUDA 11.8 in Docker |
| numpy | Yes (`1.26.2`) | CVE-2024-12905 |
| transformers | Yes (`4.36.2`) | |
| sentence-transformers | Yes (`2.2.2`) | |
| fastapi | Yes (`0.108.0`) | |
| uvicorn | Yes (`0.25.0`) | |
| TTS | No (commented out) | Not installed by default |
| 10 others | Yes | See requirements-base.txt |

### Frontend

| Category | Count |
|---|---|
| Runtime deps | 54 |
| Dev deps | 17 |
| Beta deps | 1 (nitro) |
| Unused deps | 8+ |
| Lock file | `bun.lock` |

## 10. Runtime Validation Appendix

| ID | Hypothesis | Why Static Insufficient | Recommended Method |
|---|---|---|---|
| RV-BL-01 | `docker-compose up` fails without .env file | Depends on file system state | Run without .env, verify error |
| RV-BL-02 | numpy CVE-2024-12905 is exploitable in this context | Exploit depends on attack surface | Run pip-audit or Trivy scan |

## 11. Risk Register Mapping

| Risk ID | Finding | Severity | Confidence | Priority | Description |
|---|---|---|---|---|---|
| RR-09-001 | BL-001 | Critical | High | P0 | No CI/CD pipeline — zero automation |
| RR-09-002 | BL-002 | Critical | High | P0 | No backend lock file — non-reproducible |
| RR-09-003 | BL-003 | Critical | High | P1 | No .dockerignore — build context bloat |
| RR-09-004 | BL-004 | Critical | High | P1 | No security scanning — CVEs undetected |
| RR-09-005 | BL-005 | High | High | P1 | Docker lacks health check, runs as root |
| RR-09-006 | BL-006 | High | High | P2 | Docker layer cache invalidation ordering |
| RR-09-007 | BL-007 | High | Medium | P2 | Docker Compose fails without .env file |
| RR-09-008 | BL-008 | Medium | High | P2 | Frontend linting not in pre-commit |
| RR-09-009 | BL-009 | Medium | Medium | P2 | Dockerfile best practices (apt-get, pip cache) |
| RR-09-010 | BL-010 | Low | Medium | P3 | Pre-release frontend dev dependency |

## 12. Cross-Audit References

| This Finding | Audit 04 (Security) | Audit 06 (Observability) | Audit 08 (Frontend) |
|---|---|---|---|
| BL-001 | — | — | — |
| BL-003 | — | — | — |
| BL-004 | SEC-003 (decompression bomb) | — | — |
| BL-005 | — | OBS-003 (health probes) | — |
| BL-007 | — | — | — |
| BL-008 | — | — | FE-005 (unused deps) |

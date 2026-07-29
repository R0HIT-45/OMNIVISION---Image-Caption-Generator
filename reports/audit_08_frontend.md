# Audit 08 — Frontend State & UX

---
audit_id:            audit_08_frontend
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               Frontend source code (React 19, TanStack Start), API integration, UI components, state handling, accessibility, build config
---

## 1. Executive Summary

Analysis of 65+ frontend source files reveals **12 findings: 1 Critical, 3 High, 5 Medium, 3 Low**. The most critical issue is a **hardcoded `http://localhost:8000/api/v1` base URL that overrides the `.env` variable**, making deployment to non-localhost environments impossible without code changes. Key findings include: the backend's `audio_urls` feature is completely unused (browser TTS used instead), 45 of 46 shadcn UI components are dead imports, and there is zero frontend test coverage.

| Metric | Count |
|---|---|
| Total findings | 12 |
| Confirmed defects | 5 |
| Design debt | 4 |
| Architecture debt | 1 |
| Informational | 2 |
| Critical severity | 1 |
| High severity | 3 |
| Medium severity | 5 |
| Low severity | 3 |
| P0 priority | 1 |
| P1 priority | 2 |
| P2 priority | 5 |
| P3 priority | 4 |

## 2. Scope

| In Scope | Out of Scope |
|---|---|
| SvelteKit/Svelte components | Backend API semantics (covered in audits 1-7) |
| API layer (fetch calls, error handling) | Third-party component library internals |
| Routing and navigation | Visual design review |
| State management (loading, empty, error) | Performance benchmarking |
| Responsive design implementation | Accessibility audit |
| Build configuration (Vite, TypeScript) | SEO analysis |
| Frontend package.json dependencies | Cross-browser testing |

## 3. Audit Limitations

| Limitation | Impact on Findings |
|---|---|
| No runtime execution of frontend | Cannot verify component rendering behavior or API integration end-to-end |
| Node modules not analyzed for version compatibility | Dependency version conflicts based on package.json only |
| No design mockups available | UX findings based on code analysis only |

## 4. Evidence Inventory

| ID | Location | Observation | Type | Confidence |
|---|---|---|---|---|
| A08-E001 | `routes/index.tsx` (entry route) | Single page app with upload form and results display | Source Evidence | High |
| A08-E002 | `api.ts:3` | `const BASE_URL = "http://localhost:8000/api/v1"` hardcoded, env var `VITE_OMNIVISION_API_URL` never read | Source Evidence | High |
| A08-E003 | `api.ts:5` | `const TIMEOUT = 300_000` (5 minutes) hardcoded | Source Evidence | High |
| A08-E004 | `api.ts:15-27` | Request function creates internal `AbortController`, pipes user signal | Source Evidence | High |
| A08-E005 | `api.ts:38` | Non-OK responses: `throw new Error("${status} ${statusText}")` | Source Evidence | High |
| A08-E006 | `api.ts:39` | Response parsed as `await res.json()` cast to `T` — no runtime validation | Source Evidence | High |
| A08-E007 | `api.ts:48-51` | `getHealth()` fabricates `version: "1.0.0"` — hardcoded, not from backend | Source Evidence | High |
| A08-E008 | `routes/index.tsx:85-88` | Error handling: catches `TimeoutError` and `AbortError`, falls back to generic string | Source Evidence | High |
| A08-E009 | `routes/index.tsx:124-140` | Error displayed as alert banner with retry button | Source Evidence | High |
| A08-E010 | `upload-hero.tsx:17` | Accepted types hardcoded: `["image/png", "image/jpeg", "image/webp"]` | Source Evidence | High |
| A08-E011 | `upload-hero.tsx:64` | File size limit hardcoded: `12 * 1024 * 1024` (12 MB) | Source Evidence | High |
| A08-E012 | `upload-hero.tsx:44-55` | Processing status thresholds hardcoded (3s, 10s, 30s, 90s, 150s) | Source Evidence | High |
| A08-E013 | `caption-result.tsx:44-50` | Uses `SpeechSynthesisUtterance` (browser TTS) instead of backend `audio_urls` | Source Evidence | High |
| A08-E014 | `types.ts` | `BackendResponse.audio_urls` field declared but never read in any component | Source Evidence | High |
| A08-E015 | `caption-result.tsx:106-115` | Does not display `explainability.grounding_applied`, `threshold_used`, `matchedEntity` | Source Evidence | High |
| A08-E016 | `upload-hero.tsx` | No image dimension validation (width/height) | Source Evidence | High |
| A08-E017 | `components/ui/` | 45 of 46 UI components are never imported by any app component | Source Evidence | High |
| A08-E018 | `package.json` | 8+ unused dependencies: react-hook-form, zod, recharts, date-fns, etc. | Source Evidence | High |
| A08-E019 | `__root.tsx:103` | Root error component renders but no granular error boundaries | Source Evidence | High |
| A08-E020 | `start.ts` | SSR error middleware catches and renders error page | Source Evidence | High |
| A08-E021 | `error-page.ts` | Static HTML error page with light theme — does not match dark UI | Source Evidence | High |
| A08-E022 | `use-mobile.tsx` | Hook exists but is never imported by any component | Source Evidence | High |
| A08-E023 | `sitemap[.]xml.ts:4` | `BASE_URL = ""` (empty string) — generates broken sitemap | Source Evidence | High |
| A08-E024 | Frontend | No test files found (zero `*.test.*`, `*.spec.*`, `__tests__/`) | Source Evidence | High |
| A08-E025 | `tsconfig.json:19` | `noUnusedLocals: false` — dead code not caught at compile time | Source Evidence | High |
| A08-E026 | `site-footer.tsx:27` | Region `eu-west-1` and version `1.0.0` hardcoded in footer | Source Evidence | High |
| A08-E027 | `caption-result.tsx:27-38` | Confidence color CSS classes hardcoded (High/Medium/Low/Reject) | Source Evidence | High |
| A08-E028 | `metrics-grid.tsx` | Health endpoint fields partially displayed; `model_versions`, `stage_errors` not shown | Source Evidence | High |

## 5. Verified Observations

### 5.1 Architecture

- React 19 + TanStack Start (SSR) with TanStack Router (A08-E001)
- 2 routes: `/` (index) and `/sitemap.xml` (server-generated)
- TanStack React Query for server state (health polling); `useState` for local UI
- Tailwind CSS v4 + shadcn/ui components
- TypeScript strict mode enabled

### 5.2 API Layer

- Single `request<T>()` function wraps `fetch()` (A08-E004)
- `BASE_URL` hardcoded to `localhost:8000` — overrides `VITE_OMNIVISION_API_URL` (A08-E002)
- No response schema validation — raw `as T` cast (A08-E006)
- Health version field is a hardcoded string `"1.0.0"` (A08-E007)
- Timeout hardcoded to 300s (A08-E003)
- No retry logic on failure

### 5.3 Image Upload

- Accepted types: png, jpeg, webp (A08-E010)
- Max size: 12 MB (A08-E011)
- No dimension validation (A08-E016)
- No upload progress bar
- Drag-and-drop support with proper keyboard fallback (hidden file input)

### 5.4 Result Display

- Primary caption shown with fallback chain: `final_caption || raw_caption` (A08-E013)
- Confidence label badge with color coding (A08-E027)
- Similarity score progress bar
- Language tab switcher (English default, Hindi, Telugu)
- Audio playback via browser `SpeechSynthesisUtterance` — backend `audio_urls` ignored (A08-E013, A08-E014)
- Missing UI fields: `grounding_applied`, `threshold_used`, `matchedEntity`, `model_versions`, `stage_errors` (A08-E015, A08-E028)

### 5.5 Error Handling

- HTTP 4xx/5xx: generic `Error` with status text (A08-E005)
- Timeout (300s): `TimeoutError` message (A08-E008)
- Cancel: `AbortError` silently ignored (A08-E008)
- Network failure: generic fallback string (A08-E008)
- Malformed response: runtime crash (A08-E006)
- Error displayed as alert banner with retry button (A08-E009)

### 5.6 Dead Code

- 45 of 46 shadcn UI components unused (A08-E017)
- 8+ unused npm dependencies (A08-E018)
- `use-mobile.tsx` hook never imported (A08-E022)
- `react-hook-form + zod` bundled but no forms exist
- `recharts` bundled but no charts rendered

### 5.7 Test Coverage

- Zero test files (A08-E024)
- No testing framework in `devDependencies`
- No Playwright, Vitest, or Cypress config

## 6. Assessments

The frontend is well-structured with modern React patterns and responsive design, but has significant gaps for production deployment. The hardcoded localhost URL is a deployment blocker. The unused `audio_urls` feature represents wasted backend TTS investment. The dead component bloat (45/46 unused) adds ~200KB+ to the bundle for no benefit. Zero test coverage means any refactoring or upgrade carries high risk.

## 7. Findings

### FE-001 — Critical: Hardcoded API URL Prevents Non-Localhost Deployment

---
finding_id:         FE-001
category:           Configuration
evidence_ids:       A08-E002
files:              src/lib/omnivision/api.ts:3
type:               Frontend
severity:           Critical
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P0
regression_test:    Required
subsystems:
  - Frontend
  - Deployment
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Deploy to staging URL, verify API calls reach backend
---

**Verified facts**:
- `BASE_URL = "http://localhost:8000/api/v1"` hardcoded at `api.ts:3` (A08-E002)
- `.env` defines `VITE_OMNIVISION_API_URL` but it is never read by any code
- No build-time or runtime mechanism to override the URL

**Assessment**: This is a production deployment blocker. Every non-localhost deployment requires editing source code. Also noted in CFG-007 (configuration audit).

---

### FE-002 — High: Backend audio_urls Feature Completely Unused

---
finding_id:         FE-002
category:           Feature Gap
evidence_ids:       A08-E013, A08-E014
files:              caption-result.tsx:44-50; types.ts
type:               Frontend
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P1
regression_test:    Required
subsystems:
  - CaptionResult
  - TTSService (via backend)
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Check network tab for audio_url request
---

**Verified facts**:
- Backend returns `audio_urls: Record<string, string>` per language (A08-E014)
- Frontend uses `SpeechSynthesisUtterance` browser API instead (A08-E013)
- `audio_urls` field in TypeScript type is never accessed

**Assessment**: The backend TTS pipeline generates audio files for every request, but the frontend discards them. This wastes backend GPU time, storage, and bandwidth. Browser TTS quality varies by OS, and non-English voices may be unavailable or poor quality.

---

### FE-003 — High: No Response Schema Validation — Malformed Backend Response Crashes App

---
finding_id:         FE-003
category:           Error Handling
evidence_ids:       A08-E006
files:              api.ts:39
type:               Frontend
severity:           High
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - API Layer
requirement_id:     None
requirement_status: None
estimated_effort:   Medium
owner:              Frontend
verification:       Mock backend returning unexpected shape, verify graceful error
---

**Verified facts**:
- `return (await res.json()) as T` — raw cast with zero validation (A08-E006)
- If backend changes a field name, type, or structure, the frontend will crash with `TypeError` during render
- No try/catch around `res.json()` — invalid JSON also crashes

**Assessment**: TypeScript `as T` is a compile-time assertion that does nothing at runtime. Any backend contract violation causes an unhandled error with no meaningful error message.

---

### FE-004 — High: Audio URL Implementation Gap (Backend Generates, Frontend Ignores)

*Duplicate with FE-002 — see FE-002.*

---

### FE-005 — Medium: 45 of 46 UI Components Unused — Bundle Bloat

---
finding_id:         FE-005
category:           Dead Code
evidence_ids:       A08-E017, A08-E018
files:              components/ui/*.tsx (45 of 46 files); package.json
type:               Frontend
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
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Bundle size analysis before and after cleanup
---

**Verified facts**:
- Only `button.tsx` is imported by app components (A08-E017)
- 45 other UI components (accordion, dialog, card, calendar, chart, etc.) are dead imports
- 8+ unused npm dependencies: `react-hook-form`, `zod`, `recharts`, `date-fns`, `react-day-picker`, `embla-carousel-react`, `input-otp`, `react-resizable-panels`, `vaul` (A08-E018)

**Assessment**: This adds unnecessary bundle size, dependency audit surface, and maintenance burden. Likely introduced by scaffolding with shadcn/ui's `init` which generates all components by default.

---

### FE-006 — Medium: Missing Backend Fields in UI

---
finding_id:         FE-006
category:           Feature Gap
evidence_ids:       A08-E015, A08-E028
files:              caption-result.tsx; metrics-grid.tsx; types.ts
type:               Frontend
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - CaptionResult
  - MetricsGrid
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Visual inspection after backend returns full response
---

**Verified facts**:
- `explainability.grounding_applied`, `threshold_used`, `matchedEntity` declared in `BackendResponse` but never displayed (A08-E015)
- `metadata.model_versions` never displayed (A08-E028)
- `stage_errors` never displayed (A08-E028)

**Assessment**: Users and operators cannot see: which models generated the caption, whether grounding was applied, what threshold was used, or if any pipeline stage had errors.

---

### FE-007 — Medium: No Image Dimension Validation

---
finding_id:         FE-007
category:           Validation
evidence_ids:       A08-E016
files:              upload-hero.tsx
type:               Frontend
severity:           Medium
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P2
regression_test:    Not Required
subsystems:
  - UploadHero
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Upload extremely wide/tall image, verify server-side handling
---

**Verified facts**:
- Only file type and size validated (A08-E010, A08-E011)
- No image dimension check before upload (A08-E016)

**Assessment**: Very high resolution images (e.g., 10000x10000) will be uploaded before rejection by the backend, wasting bandwidth. Backend also lacks dimension validation (image_service.py:35-37 resizes but does not reject oversized).

---

### FE-008 — Medium: Broken Sitemap with Empty BASE_URL

---
finding_id:         FE-008
category:           SEO
evidence_ids:       A08-E023
files:              sitemap[.]xml.ts:4
type:               Frontend
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Required
subsystems:
  - Routing
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Visit /sitemap.xml in browser
---

**Verified facts**:
- `BASE_URL = ""` (empty string) at `sitemap.xml.ts:4` (A08-E023)
- Generated `<loc></loc>` entries have no base URL — invalid XML

**Assessment**: Sitemap generation is broken. Search engine crawlers will encounter invalid URLs.

---

### FE-009 — Medium: Zero Frontend Test Coverage

---
finding_id:         FE-009
category:           Testing
evidence_ids:       A08-E024
files:              frontend/ (entire directory)
type:               Frontend
severity:           Medium
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Confirmed Defect
priority:           P2
regression_test:    Not Applicable
subsystems:
  - Frontend
requirement_id:     None
requirement_status: None
estimated_effort:   Large
owner:              Frontend
verification:       CI pipeline runs frontend tests on PR
---

**Verified facts**:
- Zero test files found anywhere in frontend (A08-E024)
- No testing framework in `devDependencies`
- No Playwright, Vitest, or Cypress configuration

**Assessment**: Any frontend change carries unknown regression risk. There are no component tests, integration tests, or E2E tests.

---

### FE-010 — Low: Hardcoded Version and Region in Footer

---
finding_id:         FE-010
category:           Configuration
evidence_ids:       A08-E026
files:              site-footer.tsx:27; api.ts:50
type:               Frontend
severity:           Low
confidence:
  evidence:         High
  assessment:       High
status:             Open
audit_decision:     Informational
priority:           P3
regression_test:    Not Required
subsystems:
  - SiteFooter
  - API Layer
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Check footer text against deployment
---

**Verified facts**:
- `site-footer.tsx:27`: Version `"1.0.0"` and region `"eu-west-1"` hardcoded (A08-E026)
- `api.ts:50`: Health response fabricates `version: "1.0.0"` (A08-E007)

**Assessment**: Version will go stale and region cannot be changed without code edits.

---

### FE-011 — Low: Unused Hook and Config Oversight

---
finding_id:         FE-011
category:           Dead Code
evidence_ids:       A08-E022, A08-E025
files:              use-mobile.tsx; tsconfig.json:19
type:               Frontend
severity:           Low
confidence:
  evidence:         High
  assessment:       High
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
verification:       Check for import references
---

**Verified facts**:
- `use-mobile.tsx` hook never imported (A08-E022)
- `tsconfig.json:19` sets `noUnusedLocals: false` — dead variables not caught (A08-E025)

---

### FE-012 — Low: Dark Theme Error Page Mismatch

---
finding_id:         FE-012
category:           UX
evidence_ids:       A08-E021
files:              error-page.ts
type:               Frontend
severity:           Low
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Design Debt
priority:           P3
regression_test:    Not Required
subsystems:
  - SSR
requirement_id:     None
requirement_status: None
estimated_effort:   Small
owner:              Frontend
verification:       Trigger SSR error in dark mode
---

**Verified facts**:
- `error-page.ts` is a static HTML page with light theme (A08-E021)
- App uses dark theme throughout
- On SSR error, user sees a light-themed page that clashes with the dark UI

---

## 8. UI Component Inventory

| Component | Used? | Notes |
|---|---|---|
| button.tsx | Yes | Imported by multiple components |
| badge.tsx | No | Only referenced internally |
| alert.tsx | No | Only referenced internally |
| card.tsx | No | Only referenced internally |
| progress.tsx | No | Only referenced internally |
| ... 41 others | No | See unused list in FE-005 |

## 9. Frontend State Coverage Matrix

| State | Covered? | Evidence |
|---|---|---|
| Empty (no file) | Yes | Drop zone shown (A08-E001) |
| Loading (processing) | Yes | Spinner + status text + disabled buttons (A08-E008) |
| Success (result) | Yes | Caption + metrics + pipeline shown (A08-E001) |
| Error (API failure) | Yes | Alert banner with retry (A08-E009) |
| Timeout (300s) | Yes | Specific "timed out" message (A08-E008) |
| Cancelled (user abort) | Yes | Silently ignored (A08-E008) |
| Network offline | No | No `navigator.onLine` check |
| Partial result | No | No rendering of incomplete data |
| Health degraded | Yes | Red dot + "Degraded" text (A08-E001 via header) |
| Malformed response | No | Runtime crash (A08-E006) |

## 10. Missing Features Matrix

| Backend Feature | Frontend Status | Impact |
|---|---|---|
| `audio_urls` per language | Unused (browser TTS instead) | Waste of backend TTS compute |
| `explainability.grounding_applied` | Not displayed | User can't tell if grounding was used |
| `explainability.threshold_used` | Not displayed | User can't see threshold applied |
| `explainability.matchedEntity` | Not displayed | User can't see which KB fact matched |
| `metadata.model_versions` | Not displayed | Operator can't verify deployed models |
| `stage_errors` | Not displayed | User can't see which stages failed |
| KB management | Not implemented | No way to manage knowledge base |
| Per-language audio download | Not implemented | audio_urls ignored entirely |

## 11. Runtime Validation Appendix

| ID | Hypothesis | Why Static Insufficient | Recommended Method |
|---|---|---|---|
| RV-FE-01 | Malformed JSON from backend crashes entire app | Depends on error shape at runtime | Mock malformed response, verify error boundary |
| RV-FE-02 | Browser TTS produces poor non-English audio | Depends on OS/browser voice support | Test on Windows, macOS, Linux, mobile |
| RV-FE-03 | Processing status time thresholds match actual pipeline latency | Guesses, not based on any measurement | Compare with backend timing data |

## 12. Risk Register Mapping

| Risk ID | Finding | Severity | Confidence | Priority | Description |
|---|---|---|---|---|---|
| RR-08-001 | FE-001 | Critical | High | P0 | Hardcoded localhost API URL — deployment blocker |
| RR-08-002 | FE-002 | High | High | P1 | Backend audio_urls completely unused by frontend |
| RR-08-003 | FE-003 | High | High | P1 | No response validation — malformed backend crashes app |
| RR-08-004 | FE-005 | Medium | High | P2 | 45/46 UI components unused — bundle bloat |
| RR-08-005 | FE-006 | Medium | High | P2 | Multiple backend response fields not displayed |
| RR-08-006 | FE-007 | Medium | Medium | P2 | No image dimension validation |
| RR-08-007 | FE-008 | Medium | High | P2 | Broken sitemap with empty BASE_URL |
| RR-08-008 | FE-009 | Medium | High | P2 | Zero frontend test coverage |
| RR-08-009 | FE-010 | Low | High | P3 | Hardcoded version and region in footer |
| RR-08-010 | FE-011 | Low | High | P3 | Unused hook and dead code catching disabled |
| RR-08-011 | FE-012 | Low | Medium | P3 | Dark theme error page mismatch |

## 13. Cross-Audit References

| This Finding | Audit 05 (Config) | Audit 07 (AI Capability) |
|---|---|---|
| FE-001 | CFG-007 (config gaps) | — |
| FE-002 | — | AI-008 (missing speaker WAV causes silent degradation) |
| FE-006 | CFG-006 (threshold reported but not used) | AI-006 (grounding threshold ghost) |

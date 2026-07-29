# Repository Health Audit — Phase A0

**Date:** 2026-07-29  
**Auditor:** opencode agent  
**Scope:** All project source, config, tests, scripts, dependencies

---

## 1. Duplicate & Redundant Files

| File 1 | File 2 | Issue |
|---|---|---|
| `backend/tests/test_api.py` | `tests/test_api.py` | **Duplicate test directory.** Both test the API. `backend/tests/` is older/less robust (references nonexistent fixture). `tests/` uses inline valid JPEG bytes. |
| `backend/tests/test_services.py` | `tests/test_grounding.py` | **Overlapping coverage.** Both test GroundingService with nearly identical scenarios. `tests/test_grounding.py` is more comprehensive (6 test cases vs 2). |
| `knowledge_base/raw/heritage_facts.json` | `sample_facts.json` | **Identical content.** Both contain the same 4 heritage entities verbatim. `sample_facts.json` at root is redundant. |
| `evaluate_benchmark.py` (root) | `evaluation/` dir | **Misplaced file.** The benchmark script lives at root while related output goes to `evaluation/`. Should be inside `evaluation/`. |

**Action:** Consolidate `tests/` as the single test directory, remove `backend/tests/`. Remove `sample_facts.json`. Move `evaluate_benchmark.py` into `evaluation/`.

---

## 2. Unused Dependencies

| Package | File | Reason to Remove |
|---|---|---|
| `streamlit==1.29.0` | `requirements-base.txt:19` | Frontend is React/TanStack Start, not Streamlit |
| `streamlit>=1.25.0` | `requirements.txt:6` | Same — unused |
| `requests==2.31.0` | `requirements-base.txt:20` | Not imported anywhere in the codebase |
| `TTS>=0.22.0` (commented) | `requirements.txt:20` | Already covered by `coqui-tts` in requirements-base.txt |

**Action:** Remove `streamlit` and `requests` from both requirement files. Remove commented TTS line.

---

## 3. Configuration Drift

### 3.1 `.env` vs `.env.example`

| Key | `.env` | `.env.example` | Drift |
|---|---|---|---|
| `TRANSLATION_MODEL` | `facebook/nllb-200-distilled-600M` | `ai4bharat/indictrans2-en-indic-dist-200M` | **Different values.** `.env.example` recommends IndicTrans2 but `.env` uses NLLB. |
| `MAX_UPLOAD_SIZE_MB` | `12` | `10` | **Different limits.** `.env` overrides the example's 10MB to 12MB. |
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/omnivision` | *(not present)* | `.env` has a v2.0 placeholder not in example. |

### 3.2 Frontend Env Not Used

`frontend/.env` contains `VITE_OMNIVISION_API_URL=http://localhost:8000/api/v1` but `frontend/src/lib/omnivision/api.ts:3` hardcodes `BASE_URL = "http://localhost:8000/api/v1"` instead of reading from env.

**Action:** Align `.env` and `.env.example` to a single source of truth. Make frontend read `VITE_OMNIVISION_API_URL`.

---

## 4. Hardcoded Values Bypassing Settings

| File | Line | Hardcoded Value | Should Use |
|---|---|---|---|
| `services/image_service.py` | 15 | `self.max_size = 12 * 1024 * 1024` | `settings.MAX_UPLOAD_SIZE_MB` |
| `services/grounding_service.py` | 45–68 | `score >= 0.8`, `score >= 0.6`, `score >= 0.4` | `self.threshold` (already reads it but ignores it) |
| `frontend/src/lib/omnivision/api.ts` | 3 | `BASE_URL = "http://localhost:8000/api/v1"` | `import.meta.env.VITE_OMNIVISION_API_URL` |
| `frontend/src/lib/omnivision/api.ts` | 50 | `version: "1.0.0"` | `data.version` from API response |
| `frontend/src/components/omnivision/site-header.tsx` | 66 | `href="https://github.com"` | Actual repo URL |

**Action:** Route all hardcoded values through settings or env vars.

---

## 5. Type Mismatches

| File | Line | Issue |
|---|---|---|
| `frontend/src/lib/omnivision/types.ts` | 30 | `stage_errors: string[]` but API returns `StageError[]` (objects with `stage` + `reason`). |

**Action:** Fix the type to match the `StageError` schema from the backend.

---

## 6. Dead Code & NotImplementedError Pattern

| File | Lines | Issue |
|---|---|---|
| `models/implementations.py` | 47–48, 66–67, 86–87, 105–106, 122–123 | All `generate()`/`embed()`/`translate()`/`synthesize()` methods raise `NotImplementedError`. Inference is delegated to service layer, violating the model-agnostic principle. |
| `models/base.py` | 17–19 | `get_components()` leaks model internals (processor, tokenizer, etc.) to services. |
| `tests/test_pipeline.py` | 31–35 | References `ctx.vision_time` but `ProcessingContext` uses `caption_time`. |

**Action:** Move generation logic into model implementations. Remove `get_components()`. Fix test to use correct field name.

---

## 7. Test Fixture Issues

| File | Line | Issue |
|---|---|---|
| `backend/tests/test_api.py` | 54 | `open("scripts/test_images/noise.jpg", "rb")` — path does not exist. Correct path is `test_images/failure_modes/noise.jpg`. |
| `tests/test_grounding.py` | 15–16 | Patches `get_settings` but only mocks `GROUNDING_SIMILARITY_THRESHOLD`. Settings is used as a module-level global; the mock may not propagate correctly. |

**Action:** Fix fixture paths. Verify grounding test mock works correctly.

---

## 8. Naming & Organization Issues

| Issue | Details |
|---|---|
| `backend/tests/` vs `tests/` | Two test directories causes confusion about which is canonical. |
| `sample_facts.json` at root | Redundant with `knowledge_base/raw/heritage_facts.json`. |
| `evaluate_benchmark.py` at root | Should be in `evaluation/`. |
| `docs/16_MODEL_EVALUATION.md` and `docs/16_SYSTEM_OPERATIONS_GUIDE.md` | Both numbered `16` — duplicate number. `SYSTEM_OPERATIONS_GUIDE` should be `17` (and later docs renumbered). |
| `knowledge_base/raw/heritage_facts.json` | Only 4 demo entities. Needs expansion to 200–500 entities per roadmap. |

**Action:** Renumber docs, consolidate into single canonical test directory.

---

## 9. Grounding Service Threshold Bug

`services/grounding_service.py` initializes `self.threshold = settings.GROUNDING_SIMILARITY_THRESHOLD` (line 12) but then uses hardcoded thresholds `0.8`, `0.6`, `0.4` (lines 45, 51, 57) instead of comparing against `self.threshold`. The threshold setting is effectively dead code.

**Action:** Replace hardcoded branches with `score >= self.threshold` and `score >= self.threshold * 0.75` style relative bands.

---

## 10. Security Observations

| Issue | Severity | Details |
|---|---|---|
| `CORS allow_origins=["*"]` | Medium | `main.py:44` — permissive CORS in production. Should be scoped to known origins per profile. |
| No MIME spoofing check | Low | `image_service.py` trusts `file.content_type` from client. Should verify magic bytes. |
| No rate limiting | Low | No middleware for rate limiting. |
| No API key auth | Low | `routes/` have no authentication middleware. |

---

## Summary

| Category | Count | Severity |
|---|---|---|
| **P0** (must fix before next phase) | 5 | Grounding threshold bug, hardcoded BASE_URL, type mismatch, dead model pattern, test fixture path |
| **P1** (should fix) | 8 | Config drift, duplicate files, unused deps, hardcoded version, missing async patterns |
| **P2** (nice to fix) | 5 | Renumbered docs, CORS hardening, MIME verification, rate limiting, repo URL |

**Immediate next steps:**
1. Fix grounding threshold logic (`grounding_service.py`)
2. Remove `backend/tests/` duplicate, consolidate to `tests/`
3. Fix frontend `api.ts` to read `VITE_OMNIVISION_API_URL`
4. Fix `types.ts` `stage_errors` type
5. Remove unused `streamlit` and `requests` dependencies

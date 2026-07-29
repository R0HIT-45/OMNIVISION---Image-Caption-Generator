# Canonical Audit Template v2.0

```
---
audit_id:            audit_04_security
audit_version:       2.0
generated:           2026-07-29
methodology_version: 2.0
template_version:    2.0
scope:               [per-audit description]
---

## 1. Executive Summary

[2-3 paragraph overview. Key findings table below.]

| Metric | Count |
|---|---|
| Total findings | N |
| Confirmed defects | N |
| Architecture debt | N |
| Design debt | N |
| Runtime validation required | N |
| Informational | N |
| Evidence: High confidence | N |
| Evidence: Medium confidence | N |
| Assessment: High confidence | N |
| Assessment: Medium confidence | N |
| Assessment: Low confidence | N |
| Critical severity | N |
| High severity | N |
| Medium severity | N |
| Low severity | N |
| P0 priority | N |
| P1 priority | N |
| P2 priority | N |
| P3 priority | N |

## 2. Scope

[What is and isn't covered. File/directory boundaries.]

## 3. Audit Limitations

[Single page. Static analysis only, no profiling, no stress testing, etc.]

## 4. Methodology

[Brief description of approach. Reference to template v2.0.]

## 5. Evidence Inventory

| ID | Location | Observation | Evidence Type | Confidence |
|---|---|---|---|---|
| A04-E001 | file:line | observed fact | Source Evidence | High |

**Evidence types**:

| Type | Meaning | Allowed In |
|---|---|---|
| Source Evidence | Directly observed in source code | Verified Facts, Assessment |
| Derived Inference | Logical conclusion from Source Evidence | Assessment only |
| Runtime Hypothesis | Cannot be verified statically | Assessment, Runtime Appendix |
| External Requirement | From requirements doc, spec, or standard | Assessment, Requirement Traceability |

**Rule**: Only Source Evidence may appear in Verified Facts. Derived Inferences and Runtime Hypotheses are cited only in Assessment.

## 6. Verified Observations

[Structured observations grouped by theme. Source evidence only — no judgments.]

## 7. Assessments

[Engineering judgments derived from verified observations. Clearly labeled as assessment. May cite Derived Inferences and Runtime Hypotheses.]

## 8. Findings

### FO-001 — Descriptive Title

---
finding_id:         FO-001
category:           [per-audit domain]
evidence_ids:       A04-E001, A04-E002
files:              file:line; file:line
type:               [Concurrency | Security | Configuration | ...]
severity:           Critical
confidence:
  evidence:         High
  assessment:       Medium
status:             Open
audit_decision:     Confirmed Defect
priority:           P1
regression_test:    Required
subsystems:
  - SubsystemA
  - SubsystemB
requirement_id:     R-SEC-004
requirement_status: Documented
estimated_effort:   Medium
owner:              Backend
verification:       Automated regression test
---

**Verified facts**:
- Bullet list of source-verified observations (A04-E001, A04-E002)

**Assessment**:
- Engineering judgment separated from facts

**Requirement traceability**:
- R-SEC-004: [excerpt or "None documented"]

## 9. Domain-Specific Inventory

Per-audit replacement:
- Audit 3: Concurrency Contract
- Audit 4: Security Surface Inventory
- Audit 5: Configuration State Inventory
- Audit 6: Observability Coverage Matrix
- etc.

## 10. Runtime Validation Appendix

| ID | Hypothesis | Why Static Insufficient | Recommended Method |
|---|---|---|---|
| RV-01 | ... | ... | ... |

## 11. Risk Register Mapping

| Risk ID | Finding | Severity | Confidence | Priority | Description |
|---|---|---|---|---|---|
| RR-04-001 | FO-001 | Critical | Medium | P1 | ... |

## 12. Cross-Audit References

| This Finding | Audit 01 (Architecture) | Audit 02 (Pipeline) | Audit 03 (Mem/Conc) | Audit 04 (Security) | Risk Register |
|---|---|---|---|---|---|
| FO-001 | ARCH-XXX | PIPE-XXX | MC-XXX | — | RR-04-001 |

---

## Finding Status Lifecycle

| Status | Meaning |
|---|---|
| `Open` | Identified, not yet actioned |
| `Accepted` | Reviewed, accepted as risk/debt |
| `Mitigated` | Partial fix applied, residual risk accepted |
| `Resolved` | Fully addressed |
| `False Positive` | Determined not valid upon review |
| `Deferred` | Valid but postponed to future phase |

## Priority Definitions

| Priority | Meaning |
|---|---|
| `P0` | Blocking — must fix before next release |
| `P1` | Critical — address during current phase |
| `P2` | Important — schedule after P0/P1 |
| `P3` | Nice to have — address when convenient |

## Requirement Status

| Status | Meaning |
|---|---|
| `Documented` | Written requirement exists |
| `Inferred` | Implied by system design or security best practice |
| `None` | No requirement documented |

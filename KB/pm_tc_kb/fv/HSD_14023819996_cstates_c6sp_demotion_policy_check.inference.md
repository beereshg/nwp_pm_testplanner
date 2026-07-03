# Deep Analysis: CStates: C6SP Demotion policy check

| Field | Value |
|-------|-------|
| **HSD ID** | 14023819996 |
| **Title** | CStates: C6SP Demotion policy check |
| **Date** | 2026-05-28 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Core C-States |
| **NWP Disposition** | **Skip** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip**

C6S-P (MWAIT code 0x20) is the deepest C6 flavor — it combines cache flush (C6S) with Package C-state permission (PkgC6 allowed). On NWP, **PkgC6 is ZBB'd** (not in scope per NWP PM MAS). Since C6S-P exists specifically to enable PkgC6 transitions, this test case has no valid execution context on NWP.

**Key Justification:**
- C6S-P demotion policy is meaningful only when PkgC6 is a real sleep target — ZBB on NWP
- BIOS knob `AcpiC2Enumeration=3` for C6S-P enumeration triggers PkgC6 pathway that is absent
- The C6S (without package) demotion is covered by HSD 14023819991 which **is** in scope

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- N/A — test is ZBB for NWP

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| — | Not applicable | PkgC6 is ZBB on NWP; C6S-P MWAIT 0x20 has no valid target package state |

### NWP Pass Criteria
- N/A — SKIP disposition

---

## Section C: NWP Delta Impact Analysis

### PkgC6 Scope

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PkgC6 | Supported | **ZBB** | C6S-P test meaningless — no PkgC6 target |
| C6S-P MWAIT | 0x20 supported | Not in scope | Skip entire TC |
| C6S (no pkg) | Supported | Supported | Covered by 14023819991 |

---

## Section D: Key Registers & Validation Points

Not applicable for Skip disposition.

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **PkgC6 ZBB confirmation** — ensure NWP PM MAS explicitly ZBBs PkgC6 | Low | Already confirmed in NWP PM MAS; no action needed |

---

## Section F: Recommendation

**Recommendation: SKIP — PkgC6 is ZBB on NWP**

C6S-P demotion policy is inseparable from PkgC6 behavior. Since NWP does not support PkgC6, this TC should be skipped. C6S (without package) demotion is covered by 14023819991.

Required adaptations:
1. None — mark as Skip in test plan

**Priority**: Low — no action required; superseded by 14023819991 for C6S scope

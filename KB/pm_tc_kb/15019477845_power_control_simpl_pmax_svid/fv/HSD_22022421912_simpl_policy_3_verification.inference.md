# Deep Analysis: SIMPL Policy 3 Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421912 |
| **Title** | SIMPL Policy 3 Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL Policy 3 — highest-frequency policy; verify freq limits match policy 3 spec |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Policy 3 is the highest frequency SIMPL policy (fuse = 0x17 per TC 22022421902). Same fuse-override constraint as Policies 1-2 — may be unreachable on silicon without override.

NWP: single IMH (imh0).

Tags: `plc.ti_gate.b0`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```python
import pm.Active_PM.Power.simpl.simpl_pmx as simpl_pmx
simpl_pmx.main("simpl_pmx.py --policy 3".split())
```

### Steps
| Step | Action |
|------|--------|
| 1 | Run `simpl_pmx.py --policy 3` |
| 2 | Verify `sv.socket0.imh0.pcudata.patch_persistent.current_policy` = 3 |
| 3 | Verify IO/Mem freq at or near Policy 3 max (0x17 ratio) |
| 4 | Verify BW counters reflect heavy IO + Mem traffic |

### Pass Criteria — `current_policy` = 3; freqs near policy 3 max; HPM messages confirm policy selection

---

## Section F: Recommendation

**Recommendation: ADOPT with caution — Policy 3 (max freq) may require fuse override; `simpl_pmx.py --policy 3`; NWP imh0 only; highest priority to validate if reachable**

**Priority**: Medium — Policy 3 is the performance ceiling for SIMPL; important to validate if fuse overrides become available

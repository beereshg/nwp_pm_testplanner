# Deep Analysis: SIMPL Policy 2 Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421910 |
| **Title** | SIMPL Policy 2 Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL Policy 2 — verify policy selected with appropriate BW/traffic pattern |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same constraint as TC 22022421909 — Policy 2 may be unreachable without fuse override on current silicon. Test attempts random exercise of Policy 2 via `simpl_pmx.py --policy2`.

NWP: single IMH (imh0).

Tags: `plc.ti_gate.b0`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```python
import pm.Active_PM.Power.simpl.simpl_pmx as simpl_pmx
simpl_pmx.main("simpl_pmx.py --policy2".split())
```

### Steps
| Step | Action |
|------|--------|
| 1 | Run `simpl_pmx.py --policy2` |
| 2 | Verify `sv.socket0.imh0.pcudata.patch_persistent.current_policy` = 2 |
| 3 | Verify BW counters reflect Policy 2 traffic profile |
| 4 | Verify freq across IO/Mem domains match Policy 2 spec |

### Pass Criteria — `current_policy` = 2 under specified traffic; freq within Policy 2 bounds

---

## Section F: Recommendation

**Recommendation: ADOPT with caution — Same fuse-override limitation as Policy 1; `simpl_pmx.py --policy2`; NWP imh0 only**

**Priority**: Medium — Policy 2 may require fuse override; attempt and document

# Deep Analysis: SIMPL Policy 1 Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421909 |
| **Title** | SIMPL Policy 1 Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL Policy 1 — verify policy is selected under medium IO + light Mem workload |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SIMPL Policy 1 selection by driving appropriate workload. Source TC note: *"DMR supports only Policy 0 and currently we do not have a means to override fuses and check the other policies. Revisit the test case with IMH2."*

**NWP consideration**: NWP has single IMH (no IMH2), so same limitation applies — if NWP silicon also only activates Policy 0 by fuse default, this TC may be limited to verifying that Policy 1 is NOT selected (confirming Policy 0 stability). Test should proceed with available NWP SIMPL support and be escalated to SIMPL feature team if Policy 1 is unreachable.

Tags: `plc.ti_gate.b0`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```python
import pm.Active_PM.Power.simpl.simpl_pmx as simpl_pmx
simpl_pmx.main("simpl_pmx.py --policy1".split())
```

### Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Change UFS ratios for IO/Mem to max SIMPL ratio | Fuse override if available |
| 2 | Start medium IO + light Mem workload | Drive IO fabric with moderate traffic |
| 3 | Verify UFS Status reflects ratio change | TPMI/PCuData registers |
| 4 | Read `current_policy` | `sv.socket0.imh0.pcudata.patch_persistent.current_policy` |
| 5 | Verify Policy 1 is active | `current_policy` = 1 |

### NWP Register Paths
```python
# NWP: sv.socket0.imh0 only
current = sv.socket0.imh0.pcudata.patch_persistent.current_policy
print(f"SIMPL current_policy: {current}")  # Expected: 1 if Policy 1 reachable
# BW counters
io_bw  = sv.socket0.imh0.pcudata.simpl_bw_counter_io
mem_bw = sv.socket0.imh0.pcudata.simpl_bw_counter_mem
```

### Pass Criteria
- `current_policy` = 1 under specified workload
- BW counters reflect workload distribution
- If Policy 1 unreachable: escalate to SIMPL feature team; mark as "Blocked — Policy 1 requires fuse override"

---

## Section F: Recommendation

**Recommendation: ADOPT with caution — Source TC notes Policy 1 may be unreachable without fuse override on DMR; same limitation likely on NWP; attempt TC and document whether Policy 1 is achievable on NWP silicon; `simpl_pmx.py --policy1`**

**Priority**: Medium — Policy 1 may require fuse override; coordinate with SIMPL feature team for NWP Policy 1 test vector

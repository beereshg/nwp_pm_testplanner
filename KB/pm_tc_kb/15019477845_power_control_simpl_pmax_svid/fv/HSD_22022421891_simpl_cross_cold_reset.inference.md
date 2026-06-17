# Deep Analysis: SIMPL Cross Cold Reset

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421891 |
| **Title** | SIMPL Cross Cold Reset |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL reset cross-product — policy 0 restored on cold reset |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies that after a cold reset, SIMPL reverts to policy 0 (default safe policy). The SIMPL Cold Reset Handshake terminates and `current_policy` and `target_policy` return to 0.

NWP has single IMH (imh0) — registers use `sv.socket0.imh0` only (no `imh1`).

Tags: `DMR_PO`, `plc.ti_gate.b0`, `plc.feature.p2`, `pm.xproducts.reset`, `NGA_MAIN`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
# Covered by Reset Team; PMx coverage:
python runPmx.py -x nwp.xml -p simpl_reset -tM 60
```

### Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set SIMPL to non-default policy (if possible) | Fuse/override state |
| 2 | Initiate a Cold Reset | Platform cold reset |
| 3 | After boot, read `current_policy` | `sv.socket0.imh0.pcudata.patch_persistent.current_policy` |
| 4 | Read `target_policy` | `sv.socket0.imh0.pcudata.patch_persistent.target_policy` |
| 5 | Verify both = 0 (default policy) | Cold reset must restore Policy 0 |

### NWP Register Paths
```python
# DMR: sv.sockets.imhs → NWP: sv.socket0.imh0 (single IMH only)
current = sv.socket0.imh0.pcudata.patch_persistent.current_policy
target  = sv.socket0.imh0.pcudata.patch_persistent.target_policy
assert current == 0, f"SIMPL current_policy should be 0 after cold reset, got {current}"
assert target  == 0, f"SIMPL target_policy should be 0 after cold reset, got {target}"
```

### Pass Criteria
- After cold reset: `current_policy` = 0 and `target_policy` = 0 on IMH0
- SIMPL Cold Reset Handshake terminates correctly

---

## Section F: Recommendation

**Recommendation: ADOPT — `sv.sockets.imhs` → `sv.socket0.imh0` (NWP single IMH); `dmr.xml` → `nwp.xml`; `simpl_reset` PMx plugin; Policy 0 restore on cold reset is mandatory**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; reset cross-product is a P2 validation gate

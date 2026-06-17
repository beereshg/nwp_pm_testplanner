# Deep Analysis: SIMPL Cross Warm Reset

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421894 |
| **Title** | SIMPL Cross Warm Reset |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL reset cross-product — policy 0 restored on warm reset |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Same as TC 22022421891 but via **warm reset** (vs cold reset). After warm reset, SIMPL Warm Reset Handshake terminates and policy returns to 0.

NWP: single IMH (imh0) only.

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
| 1 | Initiate a Warm Reset | Platform warm reset (no power cycle) |
| 2 | After boot, read `current_policy` and `target_policy` | `sv.socket0.imh0.pcudata.patch_persistent.*` |
| 3 | Verify both = 0 | SIMPL Warm Reset Handshake terminates at Policy 0 |

### NWP Register Paths
```python
# NWP: sv.socket0.imh0 only (no imh1)
current = sv.socket0.imh0.pcudata.patch_persistent.current_policy
target  = sv.socket0.imh0.pcudata.patch_persistent.target_policy
assert current == 0 and target == 0
```

### Pass Criteria
- After warm reset: policy registers = 0 on IMH0
- SIMPL Warm Reset Handshake terminates correctly

---

## Section F: Recommendation

**Recommendation: ADOPT — Same as cold reset TC but warm reset; `nwp.xml`; `sv.socket0.imh0` only**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; warm reset SIMPL recovery is P2 gate

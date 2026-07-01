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

### Test Case Intent

Verify that after a **warm reset**, SIMPL **retains** (does not reset) its current policy state. Unlike cold reset (which restores Policy 0), warm reset should preserve the previously active policy. `ti_gate.b0` cross-product test. NWP: single IMH (imh0). ⚠️ SIMPL ZBB per NWP PM MAS §3; FV team: Runnable_On_N-1 pending confirmation.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable post-reset |
| SIMPL functional | SIMPL enabled and policy selection working |
| Pre-reset state | Record policy state before warm reset |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Drive SIMPL to non-Policy-0 by running IO/Mem-heavy workload. `current_pre = sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); print(f'Pre-reset policy={current_pre}')` | Non-zero policy active (e.g., Policy 2 or 3) | Policy stays 0 — workload insufficient; increase IO/Mem load |
| 2 | Initiate warm reset; wait for full boot. | Platform completes warm reset; SVOS boots | Boot failure |
| 3 | Read `current_policy` post warm reset. `current_post = sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); print(f'Post-reset policy={current_post}')` | Policy retained (matches pre-reset value OR returns to safe default per spec) | Unexpected policy value — verify warm reset SIMPL behavior in NWP HAS |
| 4 | Run PMx SIMPL warm reset test. `python runPmx.py -x nwp.xml -p simpl_reset -tM 60` | PMx PASS | PMx FAIL — collect log |

---

### Pass / Fail Criteria

- **PASS**: Warm reset policy behavior matches NWP HAS specification; PMx PASS.
- **FAIL**: Policy in unexpected state post warm reset; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| current_policy | sv.socket0.imh0.pcudata.patch_persistent.current_policy | Matches expected warm-reset behavior per NWP HAS |
| target_policy | sv.socket0.imh0.pcudata.patch_persistent.target_policy | Consistent with current_policy |

---

### Post-Process

Collect NLOG on unexpected policy state. Verify SIMPL HAS for warm vs cold reset behavior difference.

---

### References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — warm reset vs cold reset policy retention behavior
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP SIMPL ZBB; single IMH topology

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

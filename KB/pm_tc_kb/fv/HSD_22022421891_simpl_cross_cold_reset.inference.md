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

### Test Case Intent

Verify that after a **cold reset**, SIMPL reverts to **Policy 0** (default safe policy): `current_policy = 0` and `target_policy = 0` on IMH0. The SIMPL Cold Reset Handshake must terminate correctly. `NGA_MAIN` / `ti_gate.b0` cross-product test. NWP: **single IMH (imh0)** — no IMH1. ⚠️ SIMPL is ZBB per NWP PM MAS §3; FV team disposition Runnable_On_N-1 pending final confirmation.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable after reset |
| Platform S0 | Fully booted post cold-reset |
| Namespace | `imh0 = sv.socket0.imh0` alias set |
| SIMPL status | Confirm SIMPL functional (not disabled by fuse/BIOS) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | (Optional) Set SIMPL to non-default policy pre-reset via BIOS knob or override. | Non-zero policy active before reset | Skippable if SIMPL stays at Policy 0 by default |
| 2 | Initiate a cold reset and wait for full boot. | Platform completes cold reset; SVOS boots | Boot failure — unrelated issue |
| 3 | Read `current_policy` and `target_policy` post-boot. `current = sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); target = sv.socket0.imh0.pcudata.patch_persistent.target_policy.read(); print(f'current={current} target={target}')` | Both = 0 (Policy 0 restored by cold reset) | Non-zero — SIMPL Cold Reset Handshake did not terminate; check PH6 init |
| 4 | Run PMx SIMPL reset test. `python runPmx.py -x nwp.xml -p simpl_reset -tM 60` | PMx PASS | PMx FAIL — collect run log |

---

### Pass / Fail Criteria

- **PASS**: After cold reset `current_policy = 0` and `target_policy = 0` on IMH0; PMx simpl_reset PASS.
- **FAIL**: Either policy != 0 post cold reset; SIMPL Handshake stuck.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| current_policy | sv.socket0.imh0.pcudata.patch_persistent.current_policy | = 0 after cold reset |
| target_policy | sv.socket0.imh0.pcudata.patch_persistent.target_policy | = 0 after cold reset |
| NLOG SIMPL | peg_client --nlog --filter SIMPL | No handshake errors |

---

### Post-Process

Verify system stable post cold reset. Collect NLOG if policy stuck non-zero.

---

### References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — SIMPL cold reset handshake; policy-0 restore behavior; current_policy / target_policy registers
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP SIMPL ZBB status (MAS §3); single IMH topology

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

# Deep Analysis: SIMPL All Fuses Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421902 |
| **Title** | SIMPL - All Fuses Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL fuse verification — all 4 policy fuse values match spec for IMH0 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify all SIMPL policy fuse values for IMH0 are correctly programmed and propagated to `simpl_max_freq_*` pcudata registers. 4 policies, 2 domains (IO=0, Mem=1): fuse → register match required for correct SIMPL frequency ceiling enforcement. NWP: single IMH (imh0) only. `ti_gate.b0` / `PMSS_NWP_READINESS_CHECK`. ⚠️ SIMPL ZBB per NWP PM MAS §3.

**Expected fuse values (from DMR_Fabric_DVFS.xlsx):**

| Policy | IO Freq Fuse | Mem Freq Fuse |
|--------|-------------|---------------|
| 0 | 0xe | TBD |
| 1 | 0x14 | TBD |
| 2 | 0x14 | TBD |
| 3 | TBD | TBD |

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` and fuse paths reachable |
| Platform S0 | Fully booted post-PH6 |
| PMx | `python flexconPM.py` (NWPSV.ini) available |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read Policy 0 IO fuse and pcudata. `p0_f=sv.socket0.imh0.fuses.punit.pcode_simpl_policy_0_imh_cfcio_max_freq.read(); p0_p=sv.socket0.imh0.pcudata.simpl_max_freq_0_0.read(); assert p0_f==0xe; assert p0_f==p0_p` | Fuse=0xe; pcudata matches fuse | Fuse=0 or fuse!=pcudata — PrimeCode init failure |
| 2 | Read Policy 1 IO fuse and pcudata. `p1_f=sv.socket0.imh0.fuses.punit.pcode_simpl_policy_1_imh_cfcio_max_freq.read(); p1_p=sv.socket0.imh0.pcudata.simpl_max_freq_0_1.read(); assert p1_f==0x14; assert p1_f==p1_p` | Fuse=0x14; pcudata matches | Mismatch — PrimeCode init failure |
| 3 | Read Policy 2 IO fuse and pcudata. `p2_f=sv.socket0.imh0.fuses.punit.pcode_simpl_policy_2_imh_cfcio_max_freq.read(); p2_p=sv.socket0.imh0.pcudata.simpl_max_freq_0_2.read(); assert p2_f==0x14; assert p2_f==p2_p` | Fuse=0x14; pcudata matches | Mismatch |
| 4 | Read Policy 3 IO fuse and pcudata; verify Mem fuses for all policies. | All fuse values non-zero; all fuse==pcudata | Zero fuse or mismatch |
| 5 | Run flexconPM. `python flexconPM.py` | flexconPM PASS | PMx FAIL — collect log |

---

### Pass / Fail Criteria

- **PASS**: All 4 policy fuses match expected values; all fuse==pcudata; flexconPM PASS.
- **FAIL**: Any fuse=0, fuse!=expected, or fuse!=pcudata; flexconPM FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| simpl_policy_0 IO fuse | sv.socket0.imh0.fuses.punit.pcode_simpl_policy_0_imh_cfcio_max_freq | = 0xe |
| simpl_max_freq_0_0 | sv.socket0.imh0.pcudata.simpl_max_freq_0_0 | = fuse value |
| simpl_policy_1 IO fuse | sv.socket0.imh0.fuses.punit.pcode_simpl_policy_1_imh_cfcio_max_freq | = 0x14 |
| simpl_max_freq_0_1 | sv.socket0.imh0.pcudata.simpl_max_freq_0_1 | = fuse value |

---

### Post-Process

Read-only test. Collect fuse dump on failure.

---

### References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — SIMPL fuse structure; policy frequency tables; fuse-to-register propagation
- [DMR Fabric DVFS Data](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) — Policy definitions; BW→freq tables; fuse values (source of truth)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP SIMPL ZBB status; single IMH topology

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SIMPL fuse values for all 4 policies. Source TC lists both IMH0 and IMH1 — NWP has single IMH (imh0) only; only IMH0 fuses are verified.

Command: `flexconPM.py` (no NWP-specific XML change needed for fuse read; register paths updated for single IMH).

Tags: `DMR_PO`, `plc.ti_gate.b0`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Fuse Verification
```python
# NWP: single IMH → imh0 only (no imh1)
import sv

# Policy 0 fuse
p0_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_0_imh_cfcio_max_freq
p0_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_0
assert p0_fuse == 0xe, f"Policy 0 fuse: expected 0xe, got {hex(p0_fuse)}"
assert p0_pcud == 0xe, f"Policy 0 pcudata: expected 0xe, got {hex(p0_pcud)}"

# Policy 1 fuse
p1_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_1_imh_cfcio_max_freq
p1_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_1
assert p1_fuse == 0x14
assert p1_pcud == 0x14

# Policy 2 fuse
p2_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_2_imh_cfcio_max_freq
p2_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_2
assert p2_fuse == 0x14
assert p2_pcud == 0x14

# Policy 3 fuse
p3_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_3_imh_cfcio_max_freq
p3_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_3
assert p3_fuse == 0x17
assert p3_pcud == 0x17

print("All IMH0 SIMPL fuses verified.")
# NOTE: NWP has no IMH1 — do not check imh1 registers
```

### Expected Values (from source TC)

| Policy | Fuse / PcuData Register | Expected Value |
|--------|------------------------|----------------|
| Policy 0 | `pcode_simpl_policy_0_imh_cfcio_max_freq` | `0xe` |
| Policy 1 | `pcode_simpl_policy_1_imh_cfcio_max_freq` | `0x14` |
| Policy 2 | `pcode_simpl_policy_2_imh_cfcio_max_freq` | `0x14` |
| Policy 3 | `pcode_simpl_policy_3_imh_cfcio_max_freq` | `0x17` |

### Pass Criteria
- All 4 SIMPL policy fuses match expected values on IMH0
- `fuse == pcudata` (fuse correctly loaded into PcuData)

---

## Section F: Recommendation

**Recommendation: ADOPT — Skip IMH1 checks (NWP has no IMH1); verify IMH0 fuses only; fuse path: `sv.socket0.imh0.fuses.punit.*`; expected values as specified above**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; SIMPL fuse values determine frequency limits for IO/Mem fabric — wrong values affect entire PM correctness

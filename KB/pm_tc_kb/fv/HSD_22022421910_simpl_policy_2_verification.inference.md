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

### Test Case Intent

Verify **SIMPL Policy 2** is selected under heavy IO/Mem bandwidth demand and that frequency limits match Policy 2 spec (IO=0x14, typically same cap as Policy 1 but different Mem limit). `ti_gate.b0` / `NGA_MAIN`. NWP: single IMH (imh0). ⚠️ SIMPL ZBB per NWP PM MAS §3.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| SIMPL fuses | Verified (TC 22022421902) |
| Workload | High IO/Mem bandwidth tool (stream bandwidth, LINPACK) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Run high IO/Mem BW workload targeting Policy-2 BW range. | IO/Mem demand in Policy-2 range | Load intensity needs adjustment |
| 2 | Read `current_policy`. `cur = sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); assert cur==2, f'Expected Policy 2, got {cur}'` | `current_policy = 2` | Wrong policy |
| 3 | Read Policy 2 freq limits. `io_freq=sv.socket0.imh0.pcudata.simpl_max_freq_0_2.read(); assert io_freq==0x14` | IO freq = 0x14 | Freq mismatch |
| 4 | Run PMx SIMPL test. `python runPmx.py -x nwp.xml -p simpl -tM 60` | PMx PASS | PMx FAIL |

---

### Pass / Fail Criteria

- **PASS**: `current_policy=2`; freq limits match Policy 2 spec; PMx PASS.
- **FAIL**: Wrong policy; freq mismatch; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| current_policy | sv.socket0.imh0.pcudata.patch_persistent.current_policy | = 2 under high IO/Mem load |
| simpl_max_freq_0_2 | sv.socket0.imh0.pcudata.simpl_max_freq_0_2 | = 0x14 (Policy 2 IO freq) |

---

### Post-Process

Stop workload. Verify policy returns to 0 at idle.

---

### References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — Policy 2 BW threshold; freq limits
- [DMR Fabric DVFS Data](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) — Policy 2 freq values; BW table
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP SIMPL; single IMH

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

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

### Test Case Intent

Verify **SIMPL Policy 3** (most aggressive frequency reduction) is selected under maximum combined IO+Mem BW demand. Policy 3 = lowest IO/Mem fabric frequency limits protecting IccMax envelope. `ti_gate.b0` / `NGA_MAIN`. NWP: single IMH (imh0). ⚠️ SIMPL ZBB per NWP PM MAS §3.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| SIMPL fuses | Verified; Policy 3 fuse value confirmed |
| Workload | Maximum combined IO+Mem stress (LINPACK + stream) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Run maximum IO+Mem BW workload to cross Policy-3 BW threshold. | System under max IO+Mem fabric stress | Workload insufficient; increase both IO and Mem BW |
| 2 | Read `current_policy`. `cur = sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); assert cur==3, f'Expected Policy 3, got {cur}'` | `current_policy = 3` | Did not reach Policy 3 — increase workload BW |
| 3 | Read Policy 3 freq limits and verify most restrictive (lowest freq). `io_freq=sv.socket0.imh0.pcudata.simpl_max_freq_0_3.read(); mem_freq=sv.socket0.imh0.pcudata.simpl_max_freq_1_3.read(); print(f'Policy3 IO={hex(io_freq)} Mem={hex(mem_freq)}')` | IO and Mem freq limits = Policy 3 fuse values | Freq mismatch or too high |
| 4 | Run PMx SIMPL test. `python runPmx.py -x nwp.xml -p simpl -tM 60` | PMx PASS | PMx FAIL |

---

### Pass / Fail Criteria

- **PASS**: `current_policy=3` under max IO+Mem load; freq limits match Policy 3 spec (most restrictive); PMx PASS.
- **FAIL**: Policy 3 not reached; freq mismatch; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| current_policy | sv.socket0.imh0.pcudata.patch_persistent.current_policy | = 3 under max IO+Mem load |
| simpl_max_freq_0_3 | sv.socket0.imh0.pcudata.simpl_max_freq_0_3 | Policy 3 IO freq (lowest) |
| simpl_max_freq_1_3 | sv.socket0.imh0.pcudata.simpl_max_freq_1_3 | Policy 3 Mem freq (lowest) |

---

### Post-Process

Stop workload. Verify policy transitions back to 0 at idle. NLOG on policy-3 failure.

---

### References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — Policy 3 definition; maximum BW threshold; lowest freq limits
- [DMR Fabric DVFS Data](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) — Policy 3 freq values; BW→policy table
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP SIMPL; single IMH

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

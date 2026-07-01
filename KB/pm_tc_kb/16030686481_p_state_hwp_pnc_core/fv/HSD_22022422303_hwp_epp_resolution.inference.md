# Deep Analysis: HWP EPP Resolution

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422303 |
| **Title** | HWP EPP resolution |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP — Energy Performance Preference (EPP) source resolution |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **HWP EPP (Energy Performance Preference) resolution** from multiple sources in correct priority order: PECI override > package request > thread/core HWP request > EPB-derived EPP. EPP (0=max performance, 255=max energy saving) controls APS bias. NWP: verify resolution on single-IMH topology. `NGA_MAIN` priority.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| HWP | Enabled (`IA32_PM_ENABLE[0] = 1`) |
| SV session | Per-core MSR access available |
| PECI | Accessible for PECI override test step |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Write EPP=0 (performance) to core HWP request. `wrmsr 0x774 [EPP_field=0]` | Autonomous frequency biased toward P0; APS ramps aggressively | No frequency change — EPP field not being respected |
| 2 | Write EPP=255 (energy saving) to same core. | Autonomous frequency reduced; APS conservative | Frequency stays high — EPP=255 not reducing frequency |
| 3 | Set package HWP request (IA32_HWP_REQUEST_PKG) with different EPP; enable PACKAGE_CONTROL bit. `wrmsr 0x772; wrmsr 0x774 [PACKAGE_CONTROL=1]` | Core uses package EPP, overriding its own | Thread EPP still dominant — package control bit not working |
| 4 | Apply PECI EPP override (if PECI available); verify it supersedes both thread and package. | PECI EPP overrides both local and package requests | PECI not overriding — check PECI enable path |
| 5 | Remove PECI override; verify OS-programmed values restored. | Reverts to OS-programmed EPP | Stale PECI EPP still active |

---

### Pass / Fail Criteria

- **PASS**: EPP priority: PECI > Package > Thread; EPP 0 = performance bias, 255 = efficiency bias; PECI removal restores OS values.
- **FAIL**: Wrong priority; EPP has no effect; PECI not overriding or not restoring.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IA32_HWP_REQUEST | MSR 0x774 per core | EPP field (bits[31:24]) set correctly |
| IA32_HWP_REQUEST_PKG | MSR 0x772 | Package EPP applied when PACKAGE_CONTROL=1 |
| IA32_PERF_STATUS | MSR 0x198 | Frequency biased per EPP |

---

### Post-Process

Remove PECI override. Restore core EPP to default (balanced = 0x80).

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — EPP resolution priority; PECI override semantics; package control bit
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP EPP resolution; single IMH topology

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **HWP EPP resolution** — how APS uses the EPP value and from which source. Key algorithm properties:
- EPP range 0–255 divided into four buckets: [0–63], [64–127], [128–191], [192–255]
- Values in algorithm tables are same within each bucket
- **EPP shifting on multi-thread is disabled** (epp_shift_cutoff = 255) — irrelevant on NWP which is non-SMT
- EPP grouping should be disabled

EPP sources: OS (per-core MSR), BIOS (global), PECI (OOB). The test verifies APS behaves correctly for each EPP bucket.

On NWP (non-SMT), EPP shifting is not applicable (already disabled by epp_shift_cutoff=255). Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- HWP EPP resolution applicable on NWP
- `NGA_MAIN` tag: primary CI coverage
- `Ready_for_testing` + `PMSS_NWP_READINESS_CHECK`: confirmed ready

---

## Section B: NWP-Specific Test Procedure

### EPP Bucket Behavior

| EPP Range | Bucket | APS Behavior | NWP |
|-----------|--------|-------------|-----|
| 0–63 | Performance | Max turbo granted; frequency aggressive | Same |
| 64–127 | Balanced Performance | High turbo; slight bias to performance | Same |
| 128–191 | Balanced Power | Moderate; energy efficiency priority | Same |
| 192–255 | Power Saving | Minimum needed frequency; conservative | Same |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run HWP check | `python runPmx.py -x nwp.xml -p hwpm_check -tM 60` |
| 2 | Set EPP = 0 (bucket 0): verify aggressive turbo | Per-core `IA32_HWP_REQUEST.EPP = 0` |
| 3 | Set EPP = 64 (bucket 1): verify balanced performance | Same |
| 4 | Set EPP = 128 (bucket 2): verify balanced power | Same |
| 5 | Set EPP = 192 (bucket 3): verify power saving | Same |
| 6 | Verify algorithm tables consistent within each bucket | Check all EPP values 0–63 give same behavior |
| 7 | Verify EPP grouping disabled on NWP | Check CPUID.06.EAX[10] |

### NWP Pass Criteria
- APS frequency selection consistent within each EPP bucket
- No EPP shifting (non-SMT NWP; epp_shift_cutoff=255)
- EPP source priority: OS > BIOS > PECI (for non-OOB mode)
- CPUID.06.EAX[10] = 1 (HWP EPP supported on NWP)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; EPP bucket behavior identical, NWP non-SMT simplifies EPP resolution**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_check -tM 60`
2. NWP non-SMT: per-physical-core EPP (no thread aggregation or shifting)
3. Verify CPUID.06.EAX[10] on NWP (HWP EPP support bit)

**Priority**: High — `NGA_MAIN`; EPP resolution is foundational HWP algorithm input

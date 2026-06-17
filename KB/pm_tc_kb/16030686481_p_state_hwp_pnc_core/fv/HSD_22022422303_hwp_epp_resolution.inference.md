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

# Deep Analysis: HWP OOB Mode HWP Autonomous P-State Selection (APS)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422332 |
| **Title** | HWP OOB Mode HWP Autonomous P-state Selection (APS) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP OOB Mode — APS algorithm with PECI-sourced EPP |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test is the **OOB Mode equivalent of TC 22022422298** (HWP APS in native mode). In OOB mode, the APS algorithm is the same closed-loop utilization-based algorithm, but EPP is provided via PECI rather than OS. Key metrics are identical:
- Instantaneous Utilization (C0%)
- FreqUtil = Frequency × C0%
- InstantaneousIdleN
- EPP = PECI-sourced in OOB mode

On NWP, OOB mode APS with PECI EPP is the same mechanism.

**Key Justification:**
- HWP APS in OOB mode applicable on NWP
- `Ready_for_testing` + `plc.feature.p2` + `PMSS_NWP_READINESS_CHECK` tags
- Same APS algorithm as TC 22022422298; only EPP source differs (PECI not OS)

---

## Section B: NWP-Specific Test Procedure

### OOB APS vs Native APS Differences

| Aspect | Native Mode (TC 22022422298) | OOB Mode (This TC) |
|--------|------------------------------|---------------------|
| EPP source | OS (`IA32_HWP_REQUEST.EPP`) | PECI (BMC/management) |
| HWP request | Per-core OS writes | Package-level PECI writes |
| APS algorithm | Same | Same |
| Frequency selection | Same utilization-based | Same utilization-based |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Boot with OOB mode: `ProcessorHWPMEnable = 0x2` | Same BIOS knob |
| 2 | Set PECI EPP = 0 (Performance) | Use PECI tool/BMC |
| 3 | Run hwpm_aps_check in OOB mode | `python runPmx.py -x nwp.xml -p hwpm_aps_check -tM 60` |
| 4 | Verify high C0% → high turbo frequency (EPP=0 aggressive) | Per-core `IA32_PERF_STATUS` |
| 5 | Change PECI EPP to 128 (Balanced Power) | Dynamic PECI EPP change |
| 6 | Verify APS frequency adapts to new EPP bucket | Same verification |
| 7 | Verify PECI min/max performance override takes effect | `IA32_HWP_CAPABILITIES` respected |

### NWP Pass Criteria
- OOB APS frequency follows PECI EPP bucket
- APS utilization-based selection active in OOB mode
- Frequency within PECI-specified min/max bounds
- Dynamic PECI EPP changes reflected within APS slow loop interval
- No MCAs during OOB mode APS operation

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; OOB APS is same algorithm as native APS TC**

The OOB APS test is directly applicable on NWP with XML and PECI tooling adaptation.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_aps_check -tM 60`
2. Verify PECI access infrastructure on NWP (BMC or PECI debug utility)
3. OOB mode: `ProcessorHWPMEnable = 0x2` BIOS setting required

**Priority**: Medium — `Ready_for_testing` + `plc.feature.p2`; OOB APS validates server management EPP control path

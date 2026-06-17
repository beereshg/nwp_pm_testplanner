# Deep Analysis: HWP OOB Mode EPP Resolution

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422326 |
| **Title** | HWP OOB Mode EPP resolution |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP OOB Mode — EPP source from PECI (out-of-band management) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **HWP EPP resolution in OOB (Out-of-Band) Mode** — same algorithm as TC 22022422303 (HWP EPP resolution) but with EPP provided via PECI rather than OS. In OOB mode:
- EPP source = PECI (BMC/management controller sends EPP)
- OS `IA32_HWP_REQUEST.EPP` may be overridden by PECI EPP
- Same four EPP buckets (0–63, 64–127, 128–191, 192–255) and algorithm tables

On NWP, PECI OOB EPP delivery is the same mechanism (requires `fw_fuses_hwp_peci_support = 1`).

**Key Justification:**
- HWP OOB PECI EPP applicable on NWP
- `Ready_for_testing` + `plc.feature.p2` + `PMSS_NWP_READINESS_CHECK` tags
- Same APS algorithm; only EPP source differs

---

## Section B: NWP-Specific Test Procedure

### OOB EPP Source Priority

```
In OOB Mode (ProcessorHWPMEnable = 0x2):
    Effective EPP = PECI-provided EPP (from BMC/management)
    OS IA32_HWP_REQUEST.EPP may be ignored or have lower priority
```

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot with OOB mode: `ProcessorHWPMEnable = 0x2` | Same BIOS knob |
| 2 | Verify PECI EPP fuse: `fw_fuses_hwp_peci_support = 1` | `sv.socket0.imh0.fuses.*` |
| 3 | Send EPP value via PECI (use PECI tool or BMC) | Set EPP = 0 (Performance) via PECI |
| 4 | Run hwpm_check in OOB mode | `python runPmx.py -x nwp.xml -p hwpm_check -tM 60` |
| 5 | Verify APS uses PECI EPP (not OS-provided EPP) | Frequency behavior reflects PECI EPP bucket |
| 6 | Change PECI EPP to 192 (Power Save); verify APS adapts | Dynamic PECI EPP change |

### PECI EPP Tool

```bash
# Send EPP via PECI to NWP (BMC or PECI debug tool)
# PECI command: WritePkgConfig for HWP EPP setting
peci_util WritePkgConfig 0 host:0 0x1A 0x02 0x0000   # EPP = 0 (Performance)
peci_util WritePkgConfig 0 host:0 0x1A 0x02 0x00C0   # EPP = 192 (Power Save)
```

### NWP Pass Criteria
- `fw_fuses_hwp_peci_support = 1` (PECI EPP enabled)
- PECI EPP = 0: APS aggressive turbo frequency
- PECI EPP = 192: APS conservative frequency
- EPP bucket boundaries (64, 128, 192) trigger behavior changes
- OS-provided EPP does not override PECI EPP in OOB mode

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; OOB PECI EPP mechanism same on NWP**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_check -tM 60`
2. Verify PECI infrastructure on NWP (BMC with PECI access or use ipmitool/peci debug tool)
3. Verify `fw_fuses_hwp_peci_support = 1` on NWP fuse strap

**Priority**: Medium — `Ready_for_testing` + `plc.feature.p2`; OOB EPP critical for BMC-managed server deployments

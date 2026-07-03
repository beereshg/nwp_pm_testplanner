# Deep Analysis: SAPM-DLL Check

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422284 |
| **Title** | SAPM-DLL check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | SAPM-DLL — System Agent Power Management + Dynamic Load-Line |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

**SAPM-DLL** (System Agent Power Management — Dynamic Load-Line) dynamically switches the internal EPB to performance mode to boost performance or energy efficiency. HWP uses SAPM-DLL to dynamically switch EPB. The test has two parts:
1. **Input EPB and EPB resolution** (covered by separate TC 22022422281)
2. **SAPM-DLL specific behavior**: dynamic EPB switching when SAPM detects favorable load-line conditions

**SAPM-DLL HAS**: `https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#sapm-dll`

On NWP, SAPM-DLL is the same mechanism — HWP uses SAPM-DLL to adaptively switch EPB for performance gains.

**Key Justification:**
- SAPM-DLL is a server P-state feature present on NWP
- `DMR_PO` + `NGA_MAIN` tags: primary CI coverage
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run SAPM-DLL verification | `python runPmx.py -x nwp.xml -p sapmdll -tM 60` |
| 2 | Enable HWP (SAPM-DLL requires HWP enabled) | `ProcessorHWPMEnable = 0x1` BIOS |
| 3 | Configure EPB to Balanced Power (EPB = 8) | Per-core or BIOS EPB setting |
| 4 | Run workload where SAPM-DLL should trigger (performance-favorable) | Monitor EPB switching |
| 5 | Verify SAPM-DLL dynamically switches EPB to Performance (EPB = 0) | Read effective EPB from PCode |
| 6 | Verify frequency boost from EPB switch | `IA32_PERF_STATUS` ratio improves |
| 7 | Verify SAPM-DLL reverts EPB when load-line not favorable | EPB returns to configured value |

### SAPM-DLL Trigger Conditions
- Dynamic load-line favorable: VR voltage droop reduced → room for higher frequency
- EPB switched internally by PCode without OS intervention
- Transparent to OS: OS still sees programmed EPB, PCode uses dynamic EPB internally

### NWP Validation

```python
# NWP SAPM-DLL Verification

# Verify SAPM-DLL enabled
try:
    sapm_cfg = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.sapm_cfg.read()
    sapm_dll_en = (sapm_cfg >> 0) & 1  # Bit 0: SAPM_DLL_ENABLE (verify bit for NWP)
    print(f"SAPM_CFG: 0x{sapm_cfg:08X}")
    print(f"  SAPM_DLL_ENABLE: {sapm_dll_en}")
except Exception as e:
    print(f"SAPM_CFG: {e}")

# Monitor effective EPB during workload
try:
    power_ctl1 = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.power_ctl1.read()
    effective_epb = (power_ctl1 >> 0) & 0xF  # Effective EPB bits (verify for NWP)
    print(f"Effective EPB (SAPM-DLL may override): {effective_epb}")
except Exception as e:
    print(f"Effective EPB: {e}")
```

### NWP Pass Criteria
- SAPM-DLL enabled by default (or via BIOS knob)
- EPB dynamically switches to Performance (0) when load-line favorable
- Frequency increased during SAPM-DLL EPB boost
- EPB reverts after load-line conditions change
- No MCAs during dynamic EPB switching

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SAPM-DLL mechanism | HWP + load-line based | Same on NWP | Direct reuse |
| VR/load-line topology | DMR FIVR/SVID | NWP FIVR/SVID (same arch) | Same concept |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; SAPM-DLL is HWP-era server feature**

SAPM-DLL verification is directly applicable on NWP with XML adaptation.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p sapmdll -tM 60`
2. Get NWP SAPM-DLL HAS URL (substitute DMR URL for NWP equivalent)
3. Verify HWP enabled for SAPM-DLL to operate

**Priority**: High — `DMR_PO` + `NGA_MAIN`; EPB dynamic switching impacts frequency/power behavior

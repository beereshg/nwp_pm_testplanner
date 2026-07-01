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

### Test Case Intent

Verify **HWP EPP resolution in OOB mode**: when OOB mode is active, EPP sent via PECI/OOB path takes priority and overrides in-band OS-programmed EPP. Verify EPP source priority specifically in OOB context: OOB-PECI EPP > in-band thread EPP. `plc.feature.p2`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| HWP OOB | Mode enabled (per TC 22022422318) |
| PECI / IPMI | OOB management path accessible |
| SV session | Per-core MSR access |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Set in-band thread EPP=0 (performance) via IA32_HWP_REQUEST. | Thread request set | Write accepted |
| 2 | Send OOB EPP=255 (energy saving) via PECI HWP request. | Frequency drops toward energy-saving levels; OOB EPP overrides in-band | In-band EPP=0 still dominant — OOB not overriding |
| 3 | Remove OOB EPP override; verify in-band EPP=0 resumes control. | Frequency returns to performance levels | OOB EPP persists after removal |
| 4 | Send OOB EPP=0 (performance); in-band EPP=255. | Performance-biased behavior — OOB EPP dominates | In-band EPP=255 overriding — wrong priority |

---

### Pass / Fail Criteria

- **PASS**: OOB EPP overrides in-band; correct priority; removal restores in-band values.
- **FAIL**: In-band overrides OOB; priority inverted; stale OOB after removal.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — HWP OOB EPP source; PECI override semantics in OOB mode
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP OOB EPP resolution

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

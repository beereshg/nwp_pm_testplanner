# TC Description: RAPL MSR Checks - Negative Test Case

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422029](https://hsdes.intel.com/appstore/article-one/#/22022422029) |
| **Title** | RAPL MSR checks - Negative test case |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Deprecated RAPL MSR negative testing — reads=0, writes no-op |
| **Parent TCD** | [22022420821 -- Socket RAPL Registers Verification - CSR and TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **Deprecated MSR Negative Testing** scenario defined in [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) §5-C: "MSR 0x610, 0x611, 0x606: reads return 0; writes silently dropped; no TPMI side effect." DMR and NWP deprecated the legacy MSR RAPL interface. This TC is a negative test confirming that writes to deprecated MSRs have no effect on the active TPMI/CSR RAPL state, reads return 0, and no system fault (#GP) occurs. MSR 0xBC (IA32_MISC_PACKAGE_CTLS) is explicitly NOT deprecated and must remain writable.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment; rdmsr/wrmsr capability |
| BIOS | Default RAPL settings |
| Starting state | System booted; RAPL active via TPMI/CSR |
| TPMI PL1 path | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control |
| CSR PL1 path | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Record baseline TPMI state: read socket_rapl_pl1_control (PL1 power, tau, lock), socket_rapl_pl2_control, socket_rapl_energy_status. Also read CSR package_rapl_limit_cfg. | All registers readable; baseline values recorded. | Register read failure. |
| 2 | Read deprecated MSR 0x606 (IA32_PKG_POWER_SKU_UNIT). | Returns 0. No #GP exception. | Non-zero value returned (MSR not properly deprecated). |
| 3 | Read deprecated MSR 0x611 (IA32_PKG_ENERGY_STATUS). | Returns 0. No #GP. | Non-zero value returned. |
| 4 | Read deprecated MSR 0x610 (IA32_PKG_RAPL_LIMIT). | Returns 0. No #GP. | Non-zero value returned. |
| 5 | Write to deprecated MSR 0x610 with a valid PL1/PL2 encoding (e.g., 0x00DD800000EA8000). No #GP expected — write silently dropped. | Write completes without exception. | #GP or system crash on MSR write. |
| 6 | Read TPMI socket_rapl_pl1_control after MSR 0x610 write. Compare to baseline. | TPMI PL1_CONTROL unchanged from baseline. MSR write had no effect on TPMI state. | TPMI value changed — deprecated MSR write leaked to TPMI. |
| 7 | Read CSR package_rapl_limit_cfg after MSR 0x610 write. Compare to baseline. | CSR unchanged from baseline. MSR write had no effect on CSR state. | CSR value changed. |
| 8 | Write to deprecated MSR 0x606. Read back. | Returns 0 on read-back. Write silently dropped. No #GP. | Read-back non-zero or #GP. |
| 9 | Verify RAPL algorithm still operating: read socket_rapl_energy_status. Compare to baseline. | Energy counter has progressed (E_now > E_baseline). RAPL still active and unaffected by deprecated MSR writes. | Energy counter stale — RAPL algorithm disrupted by MSR writes. |
| 10 | Verify MSR 0xBC (IA32_MISC_PACKAGE_CTLS) is NOT deprecated: read, toggle bit 0, read back. | MSR 0xBC is writable. Bit 0 toggled successfully. This MSR is valid on NWP. | MSR 0xBC returns 0 or write fails — incorrectly deprecated. |

### Pass / Fail Criteria

- **PASS**: Per TCD 22022420821 §5-C — All deprecated RAPL MSRs (0x606, 0x610, 0x611) return 0 on read. Writes to deprecated MSRs silently dropped — no #GP, no TPMI/CSR side effect. RAPL algorithm continues operating via TPMI/CSR. MSR 0xBC remains writable (not deprecated). No MCA or system instability.
- **FAIL**: Any deprecated MSR returns non-zero. Any MSR write causes TPMI/CSR state change. #GP on MSR access. RAPL algorithm disrupted. MSR 0xBC incorrectly deprecated.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| MSR 0x606 | rdmsr 0x606 | Returns 0 |
| MSR 0x610 | rdmsr/wrmsr 0x610 | Returns 0; write silently dropped |
| MSR 0x611 | rdmsr 0x611 | Returns 0 |
| MSR 0xBC | rdmsr/wrmsr 0xBC | Writable; NOT deprecated |
| TPMI PL1_CONTROL | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control | Unchanged after deprecated MSR writes |
| CSR package_rapl_limit_cfg | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg | Unchanged after deprecated MSR writes |
| TPMI energy_status | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status | Still progressing (RAPL alive) |

### Post-Process

N/A

### References

- [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821)
- [PrimeCode RAPL DMR -- MSR Deprecation](https://docs.intel.com/documents/primecode/primecode_one/firmware%20architecture/ip%20drivers%20and%20libraries/rapl_dmr.html)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)

---

## Section A: NWP Delta

NWP carries forward DMR MSR deprecation. Same deprecated MSRs; same TPMI/CSR active paths. NIO replaces IMH.

## Section F: Recommendations

Recommendation: ADOPT — same deprecated MSRs on NWP; verify no TPMI/CSR side effects; confirm MSR 0xBC NOT deprecated. Priority: Medium — negative test validates deprecated interface isolation.
2. Write to each deprecated RAPL MSR; verify no change in TPMI or CSR RAPL registers
3. Confirms NWP correctly ignores MSR-based RAPL interface

**Priority**: Medium — `plc.feature.p2`; negative test validates that deprecated MSR paths are truly non-functional — important for software compatibility

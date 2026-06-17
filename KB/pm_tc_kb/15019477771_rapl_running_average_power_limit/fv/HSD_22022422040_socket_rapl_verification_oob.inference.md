# Deep Analysis: Socket RAPL Verification - OOB

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422040 |
| **Title** | Socket Rapl verification - OOB |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Validate all Socket RAPL TPMI registers via OOB (Out-of-Band) access |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **all TPMI Socket RAPL registers via OOB access** path (in-band via PythonSV + TPMI). The registers are in the `ptpcfsms` block, which aggregates the TPMI Socket RAPL domain.

All registers under NWP path: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*`

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Complete NWP Socket RAPL TPMI Register Set

| TPMI Register | NWP Path | Description |
|---------------|----------|-------------|
| `socket_rapl_domain_header` | `ptpcfsms.socket_rapl_domain_header` | Socket RAPL domain capability header |
| `socket_rapl_energy_status` | `ptpcfsms.socket_rapl_energy_status` | Socket energy counter |
| `socket_rapl_perf_status` | `ptpcfsms.socket_rapl_perf_status` | Throttle counter |
| `socket_rapl_pl1_control` | `ptpcfsms.socket_rapl_pl1_control` | PL1 limit, tau, lock, clamp, enable |
| `socket_rapl_pl2_control` | `ptpcfsms.socket_rapl_pl2_control` | PL2 limit, tau, enable |
| `socket_rapl_pl4_control` | `ptpcfsms.socket_rapl_pl4_control` | PL4 peak power limit |
| `socket_rapl_pl_info` | `ptpcfsms.socket_rapl_pl_info` | Min/max power information |
| `socket_rapl_power_unit` | `ptpcfsms.socket_rapl_power_unit` | Power/energy/time units |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | OOB read all Socket RAPL TPMI registers | Via PythonSV `ptpcfsms` accessor |
| 3 | Verify `socket_rapl_power_unit` encoding | Power/energy/time units match spec defaults |
| 4 | Verify `socket_rapl_pl_info` bounds | Min/max power per fuse-driven TDP |
| 5 | Verify `socket_rapl_domain_header` | Capability bits correct for NWP |
| 6 | Verify PL1/PL2/PL4 defaults | Match fuse-driven or BIOS-programmed defaults |
| 7 | Verify energy status incrementing | Non-zero and increasing |
| 8 | Cross-check PL1/PL2 vs CSR registers | TPMI should match CSR (`package_rapl_limit_cfg`) |

### Full OOB Register Dump

```python
# NWP: OOB dump of all Socket RAPL TPMI registers
ptpcfsms = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms

# All socket RAPL registers
rapl_regs = [
    "socket_rapl_domain_header",
    "socket_rapl_energy_status",
    "socket_rapl_perf_status",
    "socket_rapl_pl1_control",
    "socket_rapl_pl2_control",
    "socket_rapl_pl4_control",
    "socket_rapl_pl_info",
    "socket_rapl_power_unit",
]
for reg in rapl_regs:
    try:
        r = ptpcfsms.getbypath(reg)
        r.show()
    except Exception as e:
        print(f"{reg}: ERROR {e}")
```

### Pass Criteria
- All 8 Socket RAPL TPMI registers readable via OOB
- `socket_rapl_power_unit` fields match spec-defined encoding
- `socket_rapl_pl_info` min/max power bounds within spec
- `socket_rapl_domain_header` capability bits correct
- PL1/PL2 defaults consistent with fuse/BIOS settings
- TPMI registers agree with corresponding CSR registers

---

## Section F: Recommendation

**Recommendation: ADOPT — All ptpcfsms paths directly applicable to NWP; single imh0; enumerate all 8 RAPL TPMI registers**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. OOB access all 8 Socket RAPL TPMI registers via `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*`
3. Cross-check against CSR equivalents; verify power unit encoding and pl_info bounds

**Priority**: High — `plc.feature.p2`; comprehensive OOB register validation ensures TPMI Socket RAPL domain is fully accessible and correctly initialized

# Deep Analysis: RAPL PEM (PnP Excursion Monitor)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422032 |
| **Title** | RAPL PEM (PnP Excursion Monitor) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PEM (PnP Excursion Monitor) — verify PEM status bits for PL1/PL2/Fast RAPL |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **PEM (PnP Excursion Monitor) status** for RAPL throttle events. PEM tracks power excursions above PL1/PL2/Fast RAPL limits. Reference: Wave 3 Common HAS §PEM_STATUS-Gen3-DMR.

RAPL PEM registers (from test steps):
- `@sv.socket0.cbb0.base.tpmi.pem_control`
- `@sv.socket0.cbb0.base.tpmi.pem_status`

On NWP: 2 CBBs — verify PEM on both `cbb0` and `cbb1`. Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### PEM Registers (NWP)

| Register | NWP Path |
|----------|----------|
| PEM control (cbb0) | `sv.socket0.cbb0.base.tpmi.pem_control` |
| PEM status (cbb0) | `sv.socket0.cbb0.base.tpmi.pem_status` |
| PEM control (cbb1) | `sv.socket0.cbb1.base.tpmi.pem_control` |
| PEM status (cbb1) | `sv.socket0.cbb1.base.tpmi.pem_status` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Set PL1 below current power to trigger PL1 RAPL excursion | Active PL1 throttle |
| 3 | Read PEM status on cbb0 and cbb1 | `pem_status.rapl_pl1_excursion` bit set |
| 4 | Trigger PL2 excursion (burst power > PL2) | PL2 timer expires |
| 5 | Read PEM status for PL2 bit | `pem_status.rapl_pl2_excursion` |
| 6 | Trigger Fast RAPL excursion | `pem_status.fast_rapl_excursion` |
| 7 | Verify PEM status cleared after throttle ends | Status bits reset after excursion ends |

### NWP: Both CBBs
```python
# NWP PEM verification on both CBBs
for cbb_idx in range(2):
    pem = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.pem_status")
    pem.show()
```

### Pass Criteria
- PEM PL1 excursion bit set when PL1 is active throttle source
- PEM PL2 excursion bit set during PL2 burst
- PEM Fast RAPL bit set during Fast RAPL engagement
- PEM status bits correct on both cbb0 AND cbb1

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; PEM on both CBBs (`cbb0` and `cbb1`)**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Trigger PL1, PL2, Fast RAPL excursions; verify PEM status on both `cbb0` and `cbb1`
3. Reference: Wave 3 Common HAS §PEM_STATUS-Gen3-DMR

**Priority**: Medium — `plc.feature.p2`; PEM provides visibility into RAPL excursion events — critical for RAPL debug and monitoring

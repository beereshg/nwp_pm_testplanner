# Deep Analysis: EET Flow Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422276 |
| **Title** | EET flow verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Energy Efficient Turbo (EET) — coarse and fine-grained mode |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

**EET (Energy Efficient Turbo)** decides whether to grant turbo (coarse-grained) and how much turbo to grant based on workload scalability (fine-grained). Scalability is defined as: percentage performance increase per percentage frequency increase. Scalable workloads get more turbo; non-scalable workloads get less or none.

EET algorithm:
- **Coarse-grained**: Should turbo be granted at all?
- **Fine-grained**: How much turbo, based on scalability measurement

On NWP, EET is the same energy efficiency mechanism. Note: test step mentions "TBD: will EET in EMR follow server spec or LNL PAlpha algorithm" — this uncertainty was for EMR, not NWP. NWP follows server spec EET.

**Key Justification:**
- EET is present on NWP (server EET algorithm)
- `DMR_PO` + `NGA_MAIN` tags: primary CI coverage
- `plc.feature.p2` tag: P-state P2 feature level validation
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Verify EET BIOS knob enabled | Check `EETurbo = 0x1` in BIOS |
| 2 | Run EET verification test | `python runPmx.py -x nwp.xml -p eet -tM 60` |
| 3 | Run scalable workload (e.g., integer compute) | EET should grant full turbo |
| 4 | Verify turbo ratio granted = max turbo (high scalability) | `IA32_PERF_STATUS` per core |
| 5 | Run non-scalable workload (e.g., memory-bound) | EET should reduce or deny turbo |
| 6 | Verify turbo ratio reduced (low scalability) | Same register check |
| 7 | Verify EET scalability metric (APERF/MPERF, IPC) | EET internal telemetry |

### EET Configuration Registers (NWP)

```python
# NWP EET verification

# Check EET BIOS knob state
try:
    power_ctl = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.power_ctl.read()
    eet_disable = (power_ctl >> 19) & 1  # Bit 19: EET_DISABLE (0=EET enabled)
    print(f"POWER_CTL: 0x{power_ctl:08X}")
    print(f"  EET_DISABLE: {eet_disable} (0=EET active, 1=EET disabled)")
except Exception as e:
    print(f"POWER_CTL: {e}")

# EET scalability status
try:
    eet_status = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.eet_scalability_status.read()
    print(f"EET Scalability Status: 0x{eet_status:08X}")
except Exception as e:
    print(f"EET scalability: {e}")
```

### NWP Pass Criteria
- EET enabled via BIOS knob (`EETurbo = 1`)
- Scalable workloads granted higher turbo ratio
- Non-scalable workloads reduced to P1 or lower turbo
- EET coarse-grained: turbo denied when no scalability
- EET fine-grained: turbo scaled proportionally to scalability measurement

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| EET algorithm | Server EET (coarse + fine grain) | Same server EET on NWP | Direct reuse |
| Scalability metric | APERF/MPERF based | Same | Direct reuse |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |
| EMR uncertainty | TBD note in steps | NWP follows server spec | No issue |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; EET server algorithm same on NWP**

EET flow verification is directly applicable on NWP.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p eet -tM 60`
2. Verify NWP EET BIOS knob name (`EETurbo` or equivalent)
3. NWP CBB topology: 2 CBBs × 48 cores (script handles via XML)

**Priority**: High — `DMR_PO` + `NGA_MAIN`; energy efficiency turbo algorithm validation

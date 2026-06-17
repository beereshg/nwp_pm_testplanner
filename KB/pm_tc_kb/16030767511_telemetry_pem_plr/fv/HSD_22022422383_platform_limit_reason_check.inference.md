# Deep Analysis: Platform Limit Reason Check

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422383 |
| **Title** | Platform Limit Reason Check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | PLR (Performance Limiting Reason) — slow loop, TPMI interface, coarse/fine grain |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **PLR (Platform/Performance Limiting Reason)** mechanism:
- PLR runs in slow loop context (every 1ms)
- Collects limiting reasons from: Slow Limits, Fast Limits/WP4, TRL
- Resolves PLR per CCP and for the ring
- Reports via **TPMI interface** (MSR/PCS interfaces deprecated on DMR)
- Two granularity levels: Coarse Grain (aggregated) and Fine Grain (per-domain)

On NWP, PLR mechanism exists with TPMI-based reporting. PLR is a standard PCode feature.

**Key Justification:**
- PLR is PCode infrastructure; `dmr.xml` → `nwp.xml`
- `DMR_PO` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- TPMI interface paths may differ on NWP vs DMR

---

## Section B: NWP-Specific Test Procedure

### PLR Architecture

```
Slow Loop (1ms):
    Collect from Slow Limits, Fast Limits/WP4, TRL
    Resolve PLR per CCP + ring
    Report via TPMI interface

Coarse Grain PLR: High-level aggregated (thermal, power, platform)
Fine Grain PLR:   Per-domain detail (specific flow or event)
```

### TPMI Interface (NWP)

```python
# Read PLR via TPMI (NWP paths may differ from DMR)
# NWP: 2 CBBs; PLR per CCP

# Check TPMI PLR for each CBB
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        # PLR coarse grain (adjust path for NWP TPMI)
        plr_coarse = cbb.base.tpmi.plr_coarse_grain.read()
        print(f"CBB{cbb_idx} PLR Coarse: 0x{plr_coarse:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} PLR Coarse: {e}")

    try:
        plr_fine = cbb.base.tpmi.plr_fine_grain.read()
        print(f"CBB{cbb_idx} PLR Fine: 0x{plr_fine:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} PLR Fine: {e}")
```

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run turbo PMx with PLR check | `python runPmx.py -x nwp.xml -p turbo -tM 60` |
| 2 | Read PLR coarse grain via TPMI | NWP TPMI path TBD |
| 3 | Apply thermal throttle; verify thermal PLR set | Force TRC/TDC limit |
| 4 | Apply power limit; verify power PLR set | Force PL1 below TDP |
| 5 | Verify PLR cleared when limit removed | PLR = 0 in no-limit condition |

### NWP Pass Criteria
- PLR reported correctly via TPMI on NWP
- Coarse grain PLR: thermal, power, platform bits correct
- Fine grain PLR: specific domain identified
- PLR clears when limiting condition removed
- Ring PLR and CCP PLR both functioning

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; PLR is PCode infrastructure**

PLR is a PCode feature applicable on NWP. TPMI paths likely have same structure on NWP.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p turbo -tM 60`
2. NWP has 2 CBBs; PLR per CCP across 2 CBBs
3. Verify NWP TPMI PLR register paths (no MSR/PCS PLR on DMR+)

**Priority**: High — `DMR_PO` + `plc.feature.p1`; PLR essential for performance debug and TPMI interface verification

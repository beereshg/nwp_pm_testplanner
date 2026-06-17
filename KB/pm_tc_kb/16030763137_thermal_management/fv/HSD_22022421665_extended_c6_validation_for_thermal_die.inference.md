# Deep Analysis: [Thermal Reporting][BEAT] Extended C6 Validation for Thermal Die Level PLR

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421665 |
| **Title** | [Thermal Reporting][BEAT] Extended C6 validation for Thermal Die Level PLR |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | TPMI PERF_LIMIT_REASONS thermal bits while in Core C6 (EMTTM and PROCHOT) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **thermal PLR bits in TPMI PERF_LIMIT_REASONS** while cores are in C6 state:
- EMTTM (Enhanced Multi-Temperature Thermal Management) → PLR bit 3
- PROCHOT → PLR bit 4
- Verify frequency clipping to expected value when conditions met
- Core C6 is maintained; verify PLR bits set while idle

**Core C6** on NWP is functional (not ZBB — only Pkg C6 and Ring C6/MC6 are ZBB). The test uses core-level C6.

**Key Justification:**
- `Ready_for_testing` + `plc.feature.p1` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags
- TPMI PLR + thermal PLR while in C6 applicable on NWP

---

## Section B: NWP-Specific Test Procedure

### Thermal PLR Bits (TPMI PERF_LIMIT_REASONS)

| Bit | Condition | Trigger |
|-----|-----------|---------|
| [3] | EMTTM | Thermal throttle via EMTTM |
| [4] | PROCHOT | PROCHOT# assertion |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable TPMI, EMTTM; disable PROCHOT lock | BIOS or OS config |
| 2 | Force cores to C6 (disable wake events) | `stress-ng --io 0` or idle |
| 3 | Assert EMTTM thermal condition | Reduce fan speed or inject thermal |
| 4 | Verify PLR bit 3 (EMTTM) set while in C6 | TPMI PERF_LIMIT_REASONS read |
| 5 | Verify frequency clipped to expected thermal floor | `IA32_PERF_STATUS` |
| 6 | Assert PROCHOT#; verify PLR bit 4 | Platform PROCHOT signal |
| 7 | Release conditions; verify PLR bits clear | Thermal → normal |

### NWP TPMI PLR Read

```python
# NWP TPMI PERF_LIMIT_REASONS (2 CBBs)
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        plr = cbb.base.tpmi.perf_limit_reasons.read()
        emttm_bit = (plr >> 3) & 1
        prochot_bit = (plr >> 4) & 1
        print(f"CBB{cbb_idx} PLR: 0x{plr:08X}  EMTTM={emttm_bit}  PROCHOT={prochot_bit}")
    except Exception as e:
        print(f"CBB{cbb_idx} PLR: {e}")
```

### NWP Pass Criteria
- While in Core C6: PLR bits 3 (EMTTM) and 4 (PROCHOT) set when conditions active
- Frequency clipping to expected thermal floor
- PLR bits clear on condition removal
- Core C6 maintained during thermal condition (cores wake only on interrupt)

---

## Section F: Recommendation

**Recommendation: ADOPT — thermalManagement.py; Core C6 + TPMI PLR applicable on NWP**

Note: Do not use Pkg C6 (ZBB on NWP). Test explicitly uses core-level C6 ("Extended C6").

Required adaptations:
1. NWP: 2 CBBs; verify TPMI PLR per CBB
2. Verify NWP TPMI PERF_LIMIT_REASONS register path

**Priority**: Medium — `plc.feature.p1` + `NGA_MAIN`; BEAT thermal PLR in C6 cross-product

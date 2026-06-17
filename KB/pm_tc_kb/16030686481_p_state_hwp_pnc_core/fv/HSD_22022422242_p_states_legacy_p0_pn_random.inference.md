# Deep Analysis: [Solar] P-States-Legacy-P0_Pn_random

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422242 |
| **Title** | [Solar] P-States-Legacy-P0_Pn_random |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Solar tool — random Legacy P-state sweep (P0..Pn) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses the **Solar** automation tool to stress Legacy P-states by issuing random P-state requests from P0 to Pn. Solar is an Intel SVOS-based PM validation tool that drives P-states via SVOS mechanisms.

**Command**: `/usr/bin/solar/solar.sh /pstate -gvpoints P0..Pn -r /logpath .`

- `-gvpoints P0..Pn`: preset sweeping from maximum (P0) to minimum (Pn) ratio
- `-r`: random order (not sequential sweep)
- `/logpath .`: log to current directory

Solar operates at the SVOS OS level and does not require platform-specific XML. Pre-condition: Legacy P-states enabled (HWP disabled). The tool works platform-agnostically on any Intel platform running SVOS.

**Key Justification:**
- Solar tool runs on SVOS regardless of platform
- No `dmr.xml` reference — platform-agnostic tool
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP
- `plc.feature.p1` tag: P1 frequency feature validation

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- SVOS running on NWP silicon
- Solar tool installed at `/usr/bin/solar/`
- HWP disabled (`ProcessorHWPMEnable = 0` in BIOS)
- Legacy P-states enabled (SpeedStep/GV3 enabled)

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot NWP to SVOS | Standard NWP SVOS bring-up |
| 2 | Verify Solar is installed | `ls /usr/bin/solar/solar.sh` |
| 3 | Run Solar P-state random sweep | `/usr/bin/solar/solar.sh /pstate -gvpoints P0..Pn -r /logpath .` |
| 4 | Verify log output for PASS/FAIL | Check Solar output log for ratio validation results |
| 5 | Verify no MCAs/errors during sweep | Check `dmesg` and `mcelog` |

### NWP P-state Range
- P0: max turbo ratio (NWP-specific value from fuses)
- Pn: minimum ratio (NWP Pm from fuses)
- Solar queries platform for these values automatically

### NWP Pass Criteria
- Solar script exits with PASS status
- All requested ratios achieved (within Solar tolerance)
- No MCAs or IERR during random P-state sweep
- Platform stable after test completion

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Solar tool | Platform-agnostic | Same | No change |
| P-state range | DMR P0..Pn | NWP P0..Pn (different absolute values) | Solar queries platform automatically |
| Command line | Identical | Same command | Direct reuse |
| SVOS requirement | SVOS | SVOS on NWP | Same |

---

## Section F: Recommendation

**Recommendation: ADOPT — command is platform-agnostic; run as-is on NWP SVOS**

Solar P-state sweep requires no adaptation. Verify Solar is deployed on NWP SVOS image.

Required adaptations:
1. Verify Solar package installed on NWP SVOS: `apt list --installed | grep solar`
2. No command change needed

**Priority**: Medium — no `DMR_PO` tag; legacy P-state stress sweep via Solar tool

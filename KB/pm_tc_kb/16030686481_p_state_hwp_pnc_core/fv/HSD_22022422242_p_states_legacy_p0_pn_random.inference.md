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

### Test Case Intent

Verify **Solar tool** drives random Legacy P-state requests (P0…Pn sweep, random order) on NWP SVOS and system is stable throughout. Solar is platform-agnostic (no NWP-specific XML needed). Pre-condition: HWP disabled, Legacy P-states enabled. `plc.feature.p1` priority.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SVOS | Running on NWP silicon |
| Solar | Installed at `/usr/bin/solar/` |
| HWP | Disabled (`ProcessorHWPMEnable = 0`) |
| SpeedStep | Enabled in BIOS |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Verify Solar installed and HWP/SpeedStep preconditions. `ls /usr/bin/solar/solar.sh; rdmsr 0x1A0` | Solar present; HWP=0; SpeedStep=1 | Solar missing — install; HWP not disabled — BIOS knob |
| 2 | Run Solar P-state random sweep from P0 to Pn. `/usr/bin/solar/solar.sh /pstate -gvpoints P0..Pn -r /logpath .` | Solar completes; log shows PASS for all ratio steps | Solar FAIL — check output log for which ratio failed |
| 3 | Verify no MCAs during Solar sweep. `dmesg | grep -i mce; mcelog` | No MCA events logged | MCA present — collect mcelog and crash dump |

---

### Pass / Fail Criteria

- **PASS**: Solar P0…Pn random sweep completes; log PASS; no MCAs.
- **FAIL**: Solar FAIL; any MCA during sweep.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| Solar output log | /logpath/solar_*.log | All ratio validation entries = PASS |
| MCA events | dmesg / mcelog | No MCA during sweep |
| IA32_PERF_STATUS | Per-core MSR 0x198 | Executed ratio matches Solar target at each step |

---

### Post-Process

Collect Solar log on failure. Check mcelog for MCA details.

---

### References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP Legacy P-state support; SVOS operation
- Solar tool documentation — platform-agnostic SVOS-based P-state stress tool

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

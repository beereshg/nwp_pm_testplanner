# Deep Analysis: HWP BIOS Configuration

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422301 |
| **Title** | HWP Bios configuration |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP BIOS knob verification (HWPMEnable, Interrupt, APSrocketing) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **HWP BIOS knobs** are available and functional without causing hangs:
- `ProcessorHWPMEnable` = 1 (HWP enabled), 0x2 (HWP native mode variant)
- `ProcessorHWPMInterrupt` = 1/0 (HWP interrupt enable/disable)
- `ProcessorAPSrocketing` = 1/0 (APS rocketing/turbo algorithm enable)

Uses `flexcon` with `DMRSV.ini` config file and `flexconPM` module.

On NWP, the same HWP BIOS knobs exist. Primary adaptation: replace `DMRSV.ini` with `NWPSV.ini` for NWP platform.

**Key Justification:**
- HWP BIOS knobs present on NWP (`ProcessorHWPMEnable`, etc.)
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP
- Flexcon config needs NWP adaptation (`DMRSV.ini` → `NWPSV.ini`)

---

## Section B: NWP-Specific Test Procedure

### BIOS Knob Combinations

| Config | HWPMEnable | HWPMInterrupt | APSrocketing | Mode |
|--------|-----------|---------------|--------------|------|
| A | 1 | 1 | 1 | HWP native + interrupts + rocketing |
| B | 0x2 | 0x0 | 0x0 | HWP OOB mode, no interrupts |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Boot with Config A; run flexcon | `python flexcon.py -i NWPSV.ini --onlyspecifiedmodules -m flexconPM` |
| 2 | Verify no hangs; all knobs accepted | Same verification |
| 3 | Reboot with Config B; run flexcon again | Same |
| 4 | Verify OOB mode knobs functional | `ProcessorHWPMEnable = 0x2` = OOB mode |

### NWP Pass Criteria
- All BIOS knob combinations accepted without hang
- HWP mode correctly set per BIOS knob
- `flexcon` PM module passes on NWP with NWP config

---

## Section F: Recommendation

**Recommendation: ADOPT — `DMRSV.ini` → `NWPSV.ini`; HWP BIOS knobs same on NWP**

Required adaptations:
1. Replace `DMRSV.ini` with `NWPSV.ini` in flexcon command
2. Verify NWP flexcon PM module (`-m flexconPM`) supports NWP registers
3. Verify BIOS knob names match NWP BIOS

**Priority**: Medium — no `DMR_PO`; HWP BIOS baseline configuration verification

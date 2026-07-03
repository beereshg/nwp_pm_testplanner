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

### Test Case Intent

Verify HWP-related **BIOS knobs** are correctly exposed and take effect: `HWPMEnable` (enables HWP hardware support), `HWP Interrupt` (enables HWP interrupt on excursion), `APSrocketing` (enables aggressive frequency ramp in APS). NWP: verify knob presence and effect on NWP-specific register paths. `plc.feature.p1` priority.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| EFI Shell / BIOS | BIOS supports HWPMEnable, HWP Interrupt, APSrocketing knobs |
| SV session | `sv.socket0.cbb{0,1}` accessible post-boot |
| Baseline | Default BIOS settings recorded before test |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Boot with `HWPMEnable = Enabled`; read IA32_PM_ENABLE. `rdmsr 0x770` | IA32_PM_ENABLE.HWP_ENABLE[0] = 1 | = 0 — BIOS did not enable HWP |
| 2 | Boot with `HWPMEnable = Disabled`; read IA32_PM_ENABLE. | IA32_PM_ENABLE[0] = 0; legacy P-state mode | = 1 — BIOS knob not taking effect |
| 3 | Enable `HWP Interrupt` BIOS knob; verify IA32_HWP_INTERRUPT MSR programmed. `rdmsr 0x773` | HWP interrupt enable bits set per BIOS knob | Bits not set — BIOS not programming interrupt MSR |
| 4 | Enable `APSrocketing`; run workload; verify faster frequency ramp-up vs disabled state. | Frequency reaches P0 faster with APSrocketing enabled | No ramp-up difference — APSrocketing knob has no effect |
| 5 | Run flexconPM BIOS verification. `python flexconPM.py -i NWPSV.ini` | flexconPM PASS | flexconPM FAIL |

---

### Pass / Fail Criteria

- **PASS**: HWPMEnable controls IA32_PM_ENABLE; HWP Interrupt sets MSR 0x773; APSrocketing affects ramp speed; flexconPM PASS.
- **FAIL**: Any knob not reflected in registers; flexconPM FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IA32_PM_ENABLE | MSR 0x770 | HWP_ENABLE matches HWPMEnable BIOS knob |
| IA32_HWP_INTERRUPT | MSR 0x773 | Set when HWP Interrupt enabled |

---

### Post-Process

Restore BIOS knobs to defaults. Collect flexconPM log on failure.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — HWP BIOS knobs; HWPMEnable; APSrocketing; HWP interrupt enable
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP HWP BIOS configuration

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

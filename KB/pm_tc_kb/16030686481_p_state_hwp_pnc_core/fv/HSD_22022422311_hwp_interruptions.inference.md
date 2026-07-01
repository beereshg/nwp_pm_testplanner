# Deep Analysis: HWP Interruptions

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422311 |
| **Title** | HWP Interruptions |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP Notifications — excursion to min, guaranteed override, PCS override interrupts |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **HWP Notification interrupts** fire correctly on three trigger conditions: (1) excursion below HWP minimum, (2) guaranteed performance change, (3) PECS (PCS) override. Each condition must generate an interrupt visible via IA32_HWP_STATUS MSR and optionally via APIC thermal LVT. `plc.feature.p2`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| HWP | Enabled (`IA32_PM_ENABLE[0]=1`) |
| HWP Interrupt | BIOS knob `HWP Interrupt = Enabled` |
| IA32_HWP_INTERRUPT | MSR 0x773 bits[2:0] set to enable desired interrupts |
| APIC | Thermal LVT enabled if checking interrupt delivery |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Enable all HWP interrupt sources: `wrmsr 0x773 0x7` (bits 0=min excursion, 1=guaranteed change, 2=excursion to maximum) | IA32_HWP_INTERRUPT = 0x7 after write | Bits not set — BIOS not allowing interrupt enable |
| 2 | Force a frequency below HWP minimum (e.g., via aggressive power limit); read IA32_HWP_STATUS. `rdmsr 0x777` | IA32_HWP_STATUS.EXCURSION_TO_MINIMUM[0] = 1 | = 0 — below-min excursion not generating status bit |
| 3 | Trigger guaranteed ratio change (e.g., change RAPL PL1 to cause guaranteed ratio drop); read IA32_HWP_STATUS. | IA32_HWP_STATUS.CHANGE_TO_GUARANTEED[1] = 1 | = 0 — guaranteed change notification missing |
| 4 | Clear status bits by writing 1 to clear. `wrmsr 0x777 0x3` | Status bits clear to 0 | Bits sticky and not clearing |

---

### Pass / Fail Criteria

- **PASS**: All 3 interrupt sources generate status bits; bits clear on write-to-clear; interrupt delivery functional.
- **FAIL**: Any status bit not set on trigger; bits not clearing; interrupt not delivered.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IA32_HWP_INTERRUPT | MSR 0x773 | Interrupt enable bits settable |
| IA32_HWP_STATUS | MSR 0x777 | Status bits set on trigger conditions; WC (write-1-to-clear) |

---

### Post-Process

Clear IA32_HWP_STATUS. Restore IA32_HWP_INTERRUPT to default (0). Remove artificial power limits.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — HWP notification interrupts; IA32_HWP_INTERRUPT; IA32_HWP_STATUS; excursion-to-min; guaranteed change
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP HWP interrupt support

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **HWP Notification Interrupts** in HWP Native Mode — notifications sent to the OS when:
1. Frequency drops to minimum performance (excursion to min)
2. Core is throttled to guaranteed (P1) ratio
3. OS-requested performance capability (PCS) override interrupt

Requirements:
- Fuse: `core_core_fuse_misc_hwp_interrupt_enable = 1`
- CPUID Leaf 6 EAX bit 8 = 1 (HWP Notification supported)
- BIOS: `ProcessorHWPMEnable = 1` (native mode), `ProcessorHWPMInterrupt = 1`

On NWP, HWP interrupts are the same architectural feature. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- HWP interrupt capability present on NWP (fuse + CPUID)
- `DMR_PO` tag: bring-up priority
- `plc.feature.p2` + `PMSS_NWP_READINESS_CHECK` tags

---

## Section B: NWP-Specific Test Procedure

### HWP Notification Interrupt Types

| Notification | Trigger | `IA32_HWP_STATUS` bit |
|-------------|---------|----------------------|
| Excursion_to_min | Freq ≤ `IA32_HWP_CAPABILITIES.minimum` | Bit 0 |
| Guaranteed_Performance_Change | Freq ≤ guaranteed (P1) | Bit 2 |
| PCS_Override | OS-requested perf changed | Bit 3 |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Verify fuse: `core_core_fuse_misc_hwp_interrupt_enable = 1` | `sv.socket0.cbb0.compute0.cpu.module0.core0.fuses.*` |
| 2 | Verify CPUID.06.EAX[8] = 1 | Use `baseaccess.cpuid(6, 0)['eax'] >> 8 & 1` |
| 3 | Enable BIOS: `ProcessorHWPMEnable = 1`, `ProcessorHWPMInterrupt = 1` | Same |
| 4 | Run HWP check with interrupts | `python runPmx.py -x nwp.xml -p hwpm_check -tM 60` |
| 5 | Trigger excursion to min (thermal/RAPL throttle) | Force throttle to Pm |
| 6 | Verify interrupt received; `IA32_HWP_STATUS[0] = 1` | Per-core status check |
| 7 | Clear interrupt; verify clears properly | Write 0 to `IA32_HWP_STATUS` |

### NWP Fuse & CPUID Check

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

# CPUID check
hwp_notify_cpuid = (base.cpuid(6, 0)['eax'] >> 8) & 1
print(f"CPUID.06.EAX[8] HWP Notification: {hwp_notify_cpuid} (expected 1)")

# Fuse check (NWP CBB fuse hierarchy)
try:
    hwp_int_fuse = sv.socket0.cbb0.compute0.cpu.module0.core0.fuses.core_core_fuse_misc_hwp_interrupt_enable.read()
    print(f"hwp_interrupt_enable fuse: {hwp_int_fuse} (expected 1)")
except Exception as e:
    print(f"HWP interrupt fuse: {e}")

# HWP Status per core
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        hwp_status = cbb.compute0.cpu.module0.core0.ia32_hwp_status.read()
        print(f"CBB{cbb_idx} core0 IA32_HWP_STATUS: 0x{hwp_status:08X}")
    except Exception as e:
        print(f"CBB{cbb_idx} HWP_STATUS: {e}")
```

### NWP Pass Criteria
- HWP interrupt fuse = 1; CPUID Leaf 6 EAX bit 8 = 1
- HWP interrupts delivered to OS on excursion to min
- `IA32_HWP_STATUS` bits set correctly per trigger event
- Interrupts cleared by SW write

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; HWP interrupt mechanism architectural**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_check -tM 60`
2. Verify NWP fuse name: `core_core_fuse_misc_hwp_interrupt_enable` in CBB fuse hierarchy
3. NWP non-SMT: interrupts per physical core (no thread aggregation)

**Priority**: High — `DMR_PO` + `plc.feature.p2`; HWP notification interrupt bring-up check

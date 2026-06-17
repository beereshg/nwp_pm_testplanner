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

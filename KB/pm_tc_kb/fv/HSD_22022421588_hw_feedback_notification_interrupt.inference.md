# Deep Analysis: [Thermal Interrupts] HW_FEEDBACK_NOTIFICATION Interrupt

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421588 |
| **Title** | [Thermal Interrupts] HW_FEEDBACK_NOTIFICATION interrupt |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | IA32_HWP_INTERRUPT (Core MSR 0x773) — interrupt enable bits verification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **IA32_HWP_INTERRUPT (Core MSR 0x773)** — interrupt enable bits for:
- Guaranteed performance change interrupt
- Excursion to Min interrupt
- Max Performance Ratio change interrupt
- PECI override interrupt

Despite the title "HW_FEEDBACK_NOTIFICATION", the steps describe IA32_HWP_INTERRUPT field verification. The script: `HWP_Interrupt.py`.

On NWP, IA32_HWP_INTERRUPT is the same per-core MSR inside CBB perimeter.

**Key Justification:**
- `DMR_PO` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- Per-core MSR 0x773 directly applicable on NWP (non-SMT: 1 per physical core)

---

## Section B: NWP-Specific Test Procedure

### IA32_HWP_INTERRUPT (MSR 0x773) Bits

| Bit | Interrupt Enable | Description |
|-----|-----------------|-------------|
| [0] | `EN_EXCURSION_MIN` | Notify on excursion to minimum perf |
| [1] | `EN_HIGHEST_CHANGE` | Notify on max performance ratio change |
| [2] | `EN_GUARANTEED_CHANGE` | Notify on guaranteed perf ratio change |
| [3] | `EN_PECI_OVERRIDE` | Notify on PECI EPP override |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run HWP_Interrupt.py on NWP | Adapt script paths for NWP |
| 2 | Enable HWP Native mode | `ProcessorHWPMEnable = 1` |
| 3 | Enable interrupt bits: `IA32_HWP_INTERRUPT[0,1,2,3] = 1` | All interrupt enables |
| 4 | Verify fields read back correctly | No WO or reserved field issues |
| 5 | Trigger guaranteed perf change | Modify thermal/power limit |
| 6 | Verify interrupt delivered to LAPIC | OS thermal interrupt handler |

### NWP Per-Core Verification

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

# Read IA32_HWP_INTERRUPT per core
hwp_int_msr = 0x773
for cbb_idx in range(2):
    for core_idx in range(48):  # 48 cores per CBB on NWP
        abs_core = cbb_idx * 48 + core_idx
        try:
            hwp_int = base.rdmsr_on_core(hwp_int_msr, cbb_idx, core_idx)
            print(f"CBB{cbb_idx} Core{core_idx} IA32_HWP_INTERRUPT: 0x{hwp_int:08X}")
        except:
            pass  # Skip unresponsive cores
```

### NWP Pass Criteria
- IA32_HWP_INTERRUPT fields accessible and writable per core
- All 4 interrupt enable bits functional
- Interrupts delivered when corresponding HWP events occur
- No interrupt leakage (no spurious interrupts)

---

## Section F: Recommendation

**Recommendation: ADOPT — HWP_Interrupt.py; same MSR on NWP; adapt for NWP paths**

Required adaptations:
1. Update `HWP_Interrupt.py` script path for NWP PythonSV repo
2. NWP non-SMT: per-core MSR 0x773 (no thread index)
3. 2 CBBs × 48 cores = 96 interrupt enable registers to verify

**Priority**: High — `DMR_PO` + `plc.feature.p1`; HWP interrupt notification bring-up check

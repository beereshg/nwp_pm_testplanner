# Deep Analysis: [Thermal Reporting] Verify IA32_MISC_ENABLES (Thread vMSR 0x1a0)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421642 |
| **Title** | [Thermal Reporting] Verify IA32_MISC_ENABLES (Thread vMSR 0x1a0) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | Thermal Monitor enable; CPUID.06 thermal capability bits |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **IA32_MISC_ENABLES (MSR 0x1A0)** thermal monitor enable bit and associated **CPUID.06** thermal capability flags:
- `CPUID.06.EDX[29]`: Thermal Monitor supported
- `CPUID.06.EAX[0]`: Digital Thermal Sensor (DTS) supported
- `CPUID.06.EAX[5]`: Enhanced Clock Modulation Duty Cycle (ECMDC) supported
- `CPUID.06.EAX[6]`: Package Thermal Management (PTM) supported

On NWP (non-SMT), MSR 0x1A0 is a **Core MSR** (not per-thread — NWP has 1 thread per core). The test is directly applicable.

**Key Justification:**
- `No_content_required` + `plc.feature.p1` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags
- Thermal monitor MSR and CPUID bits present on all Intel server platforms

---

## Section B: NWP-Specific Test Procedure

### Key Fields

| MSR/CPUID | Field | Expected |
|-----------|-------|---------|
| MSR 0x1A0[18] | `Thermal Monitor Enable (TM1)` | 1 (TCC throttling enabled) |
| CPUID.06.EDX[29] | Thermal Monitor supported | 1 |
| CPUID.06.EAX[0] | DTS supported | 1 |
| CPUID.06.EAX[5] | ECMDC supported | 1 |
| CPUID.06.EAX[6] | PTM supported | 1 |

### NWP Non-SMT Note
Title says "Thread vMSR" — on NWP there is 1 thread per core, so per-core = per-thread. No thread aggregation needed.

### NWP Verification

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

# IA32_MISC_ENABLES thermal monitor bit
misc_enables = base.rdmsr(0x1A0)
tm_enable = (misc_enables >> 18) & 1
print(f"IA32_MISC_ENABLES[18] TM Enable: {tm_enable} (expected 1)")

# CPUID.06 thermal capability
cpuid6 = base.cpuid(6, 0)
print(f"CPUID.06.EAX[0] DTS: {(cpuid6['eax'] >> 0) & 1}")
print(f"CPUID.06.EAX[5] ECMDC: {(cpuid6['eax'] >> 5) & 1}")
print(f"CPUID.06.EAX[6] PTM: {(cpuid6['eax'] >> 6) & 1}")
print(f"CPUID.06.EDX[29] TM: {(cpuid6['edx'] >> 29) & 1}")
```

### NWP Pass Criteria
- `IA32_MISC_ENABLES[18] = 1` (TM enabled)
- All CPUID.06 thermal capability bits = 1
- Thermal monitor active (TCC throttling functional)

---

## Section F: Recommendation

**Recommendation: ADOPT — Manual/scripted; same thermal MSR on NWP**

Required adaptations:
1. NWP non-SMT: per-core MSR read (no per-thread loop)
2. 2 CBBs × 48 cores = 96 cores to verify

**Priority**: Medium — `plc.feature.p1` + `NGA_MAIN`; thermal monitor bring-up gate

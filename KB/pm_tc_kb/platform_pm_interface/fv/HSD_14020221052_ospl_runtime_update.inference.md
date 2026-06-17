# Deep Analysis: OSPL Runtime Update

| Field | Value |
|-------|-------|
| **HSD ID** | 14020221052 |
| **Title** | OSPL runtime update |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | (blank) |
| **Sub-Feature** | OSPL (OS-Present Live update) — microcode runtime update while OS is running |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

*Note: HSD template content is incomplete — only mandatory section headers are present with no test steps filled in.*

OSPL (OS-Present Live update) allows microcode update while the OS is running without a full reboot. This is functional on NWP (not ZBB).

---

## Section B: NWP-Specific Test Procedure

*Test content incomplete in source HSD. Below is inferred from OSPL feature context.*

### OSPL Runtime Update Flow

| Step | Action | Details |
|------|--------|---------|
| 1 | Boot to SVOS | Normal boot with existing MCU |
| 2 | Note current microcode revision | `cpuid.1.eax`, MSR 0x8B |
| 3 | Apply OSPL (live MCU update) | OS-initiated MCU update |
| 4 | Verify updated MCU revision | MSR 0x8B reflects new version |
| 5 | Verify PM features stable post-OSPL | RAPL, C-states, HWP functional |
| 6 | Optional: run `runPmx.py` post-OSPL | Regression check |

### Pass Criteria
- MCU revision updated without reboot
- System stable post-update (no hang, no MCA)
- PM features functional after MCU update

---

## Section F: Recommendation

**Recommendation: ADOPT — Template content incomplete in source HSD; implement basic OSPL flow; OSPL functional on NWP; collaborate with platform team for NWP OSPL package**

**Priority**: Medium — OSPL runtime update is a production servicing requirement

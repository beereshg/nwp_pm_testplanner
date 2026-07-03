# Deep Analysis: HGS Enabling and Discovery

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422197 |
| **Title** | HGS Enabling and Discovery |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | HGS (Hardware Guided Scheduling) — CPUID discovery, HFI table setup, OS notification |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

**Reason**: HGS (Hardware Guided Scheduling) is on the NWP ZBB list. HGS uses the Hardware Feedback Interface (HFI) to guide OS thread scheduling based on CPU efficiency recommendations.

Feature discovery flow:
- `CPUID.6.EAX[19]` = 1: HGS supported
- `CPUID6.EDX[11:8]`: HFI region size (in 4K pages - 1)
- `IA32_HW_FEEDBACK_PTR` (MSR 0x17D0): physical address of HFI table

This feature is not implemented on NWP initial silicon.

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section F: Recommendation

**Recommendation: SKIP — HGS is ZBB on NWP; CPUID discovery and HFI table setup not applicable; revisit for future NWP stepping**

**Priority**: N/A — ZBB blocker

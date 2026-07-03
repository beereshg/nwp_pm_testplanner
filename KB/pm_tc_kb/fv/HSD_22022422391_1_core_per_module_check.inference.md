# Deep Analysis: 1 Core Per Module Check

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422391 |
| **Title** | 1 Core Per Module Check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Module Turbo — 1CPM (1 Core Per Module) via SST-PP |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

This test verifies **Module Turbo** functionality under the **1 Core Per Module (1CPM)** condition. Module Turbo is an SST-PP (Speed Select Technology — Performance Profile) feature, as evidenced by:
- `SST_PP_MISC_STATUS.MODULE_TURBO_CAPABILITY` — SST-PP register namespace
- `SST_PP_MISC_CONTROL.MODULE_TURBO_CONTROL` — SST-PP control register

**SST-PP is a ZBB (Zero Bug Bounce) feature on NWP.** Module Turbo is gated by SST-PP capability and is therefore not available on NWP first silicon.

**Key Justification:**
- SST-PP is in the NWP ZBB feature list
- Module Turbo gated behind `SST_PP_MISC_STATUS.MODULE_TURBO_CAPABILITY` (SST-PP register)
- `plc.ti_gate.b0` tag confirms Ti-gate (B0 stepping) gate — further confirms future feature

---

## Section B: ZBB Feature Applicability on NWP

### What is Module Turbo / 1CPM?

Module Turbo allows a processor module to operate at higher turbo ratios when only 1 core per module is active. In DMR, each module contains 2 cores (CMT, Cluster Multi-Threading). The 1CPM (1 Core Per Module) condition means one core per 2-core cluster is active, enabling higher per-cluster turbo.

On NWP, modules have 2 physical cores but no SMT. Module Turbo via SST-PP is ZBB.

### Expected Steps on NWP (if ZBB is lifted)

| Step | Action | Notes |
|------|--------|-------|
| Pre-check | `SST_PP_MISC_STATUS.MODULE_TURBO_CAPABILITY` | Must = 1 (else skip) |
| Enable | `SST_PP_MISC_CONTROL.MODULE_TURBO_CONTROL = 1` | SST-PP control |
| Enable HWP | `IA32_PM_ENABLE[0] = 1` | MSR 0x770 |
| 1CPM | Pin single-threaded workload per module | `stress-ng --cpu 1` per module |
| Verify | Module turbo frequency > standard turbo | `IA32_PERF_STATUS` |

---

## Section F: Recommendation

**Recommendation: SKIP (ZBB) — SST-PP including Module Turbo is ZBB on NWP**

This test requires SST-PP capability which is not available on NWP first silicon. Test should be marked `Skip_ZBB` in the NWP test plan.

**Priority**: N/A (ZBB) — Re-evaluate if SST-PP support added to NWP in future stepping

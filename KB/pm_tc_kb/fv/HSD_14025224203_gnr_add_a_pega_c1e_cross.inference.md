# Deep Analysis: GNR Add PEGA C1e Cross-Product (PCIe INTx)

| Field | Value |
|-------|-------|
| **HSD ID** | 14025224203 |
| **Title** | [BEAT] [FV PM/UBOX] GNR: Add a PEGA C1e cross-product test case — PCIe card generating 38M+/sec INTx |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | GNR/DMR (from BEAT AR 14021948797) |
| **Feature** | (blank) |
| **Sub-Feature** | PEGA Fast C1E × PCIe INTx cross-product — TSC/performance impact under high-rate legacy interrupts |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This BEAT AR tests PEGA Fast C1E behavior when the system receives 38 million+/sec back-to-back PCIe legacy interrupts (INTx). Fast C1E is functional on NWP (not ZBB). The test originated as a GNR AR but is targeted at Diamond Rapids and NWP.

Tags: None (blank sub_feature).

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Install PCIe card capable of generating INTx interrupts | Platform setup |
| 2 | Enable PEGA Fast C1E on all cores | BIOS knob or MSR C1E enable |
| 3 | Configure PCIe card to generate 38M+/sec legacy INTx | Interrupt rate maximization |
| 4 | Run for sufficient duration (stability check) | Monitors: TSC, C-state residency |
| 5 | Verify system stability (no MCA, no hang) | No crash or thermal runaway |
| 6 | Verify Fast C1E entry/exit during interrupt storm | C1E residency should be low or zero |

### NWP Fast C1E Note
- Fast C1E: functional on NWP (TCs 14020416795/803/804 are Runnable)
- No SMT on NWP — each core is single-threaded
- INTx interrupt handling via UBOX/NCU (same architecture)

### Pass Criteria
- System stable under 38M+/sec INTx interrupt rate
- No MCAs or unexpected throttle
- Fast C1E behavior correct under interrupt pressure

---

## Section F: Recommendation

**Recommendation: ADOPT — PEGA C1E functional on NWP; PCIe INTx hardware setup required; NWP single-threaded cores (no SMT); adapt GNR BEAT AR test logic for NWP**

**Priority**: Medium — BEAT AR; important for validating C1E behavior under real-world high-IRQ workloads

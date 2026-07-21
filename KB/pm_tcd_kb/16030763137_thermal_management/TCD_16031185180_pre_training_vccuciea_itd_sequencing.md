# TCD: ITD-SCENARIO-003 - Pre-Training VCCUCIEA ITD Sequencing

| Field | Value |
|-------|-------|
| **TCD ID** | [16031185180](https://hsdes.intel.com/appstore/article-one/#/16031185180) |
| **Title** | ITD-SCENARIO-003 - Pre-Training VCCUCIEA ITD Sequencing |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | VCCUCIEA D2D VCCIO ITD |
| **NWP Disposition** | Needs_Adaptation (sequence same as DMR; NWP register paths and DTS mapping differ) |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | SOC HSD 22018755448; DMR Thermal HAS §ITD; D2D PM HAS §pre-training; UCIe Phy HAS §mbinit |
| **Co-Design T2 origin** | Table 2 row 4 (split-from 16031170075) — 2026-07-21 |
| **Re-homed TC** | [22022421534](https://hsdes.intel.com/appstore/article-one/#/22022421534) — Verify ITD during reset (partial coverage) |

---

## Definition Block

- **Layer:** 3 (Scenario)
- **Sentence:** VCCUCIEA ITD is applied using real-time DTS temperature before mainband training begins, remains frozen during training, and reverts to worst-case ITD after training completes until the kernel starts.
- **Gate:** ITD-CONTRACT-003 (Fabric/IO Domain Compensation — VCCUCIEA offset calculation correct)
- **Suspect:** IMH Primecode pre-training ITD sequence; Root PCode ready_for_d2d_mb_training HPM coordination; CBB→IMH sequencing
- **Setup:** System in reset flow. UCIe DTSs operational (Phase 3). RC set up with boot workpoint. D2D links not yet trained.
- **Check:** Observe VCCUCIEA voltage at three phase boundaries: (1) training start, (2) training complete, (3) kernel start.
- **Invariant:** Phase 1 (training start): VCCUCIEA = base + real-time ITD from UCIe DTS; Phase 2 (training complete → kernel): VCCUCIEA = worst-case ITD (safe work-point); Phase 3 (kernel start): periodic real-time ITD resumes. No VCCUCIEA change during the MB training window itself.

---

## Section 1: Architecture / Micro-architecture and Functionality

**Pre-Training VCCUCIEA ITD Sequencing** validates the 3-phase voltage behavior of VCCUCIEA around UCIe mainband training. UCIe Phy requires correct ITD voltage for successful MB training and optimal margins. The sequence coordinates across dies via HPM messages and must complete before training handshake begins.

> **Architecture overview:** See [TPF 16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) §2 Design Details

### NWP Delta

- Same 3-phase sequence as DMR; NWP IMH2 register paths differ
- UCIe DTS mapping to VCCUCIEA FIVRs (NWP-specific):

### VCCUCIEA FIVR → DTS Mapping (for pre-training temp read)

| FIVR Domain | DTSs to Read |
|---|---|
| VCCUCIEA_NW | dts_ucie_b |
| VCCUCIEA_NE | dts_ucie_a |
| VCCUCIEA_SW | dts_ucie_c, DTS_IMH_UCIE_temp_reg_0 |
| VCCUCIEA_SE | dts_ucie_d, DTS_IMH_UCIE_temp_reg_1 |

### Reset Sequence Timeline

```
IMH Reset PH3: UCIe DTSs operational
     │
     ├─ CBB waits for valid UCIe DTS temps
     ├─ CBB sends ready_for_d2d_mb_training HPM
     │
IMH Reset PH5: MB training begins
     │
     ├─ Root PCode waits for all CBBs ready_for_d2d_mb_training
     ├─ Root PCode acks ready_for_d2d_mb_training
     ├─ Each die reads UCIe DTS → applies real-time ITD to VCCUCIEA
     ├─ CBB: performs ITD on VCCUCIEA upon receiving ack, then starts training
     ├─ IMH: reads UCIE temp directly from DTS, performs ITD, starts training
     │
     ├─── MB TRAINING (~2ms) ─── NO VCCUCIEA CHANGES ───
     │
     ├─ Training complete → set worst-case ITD (safe work-point)
     ├─ [No mainband traffic between training complete and core boot]
     │
Kernel start: periodic real-time ITD resumes
```

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | UCIe DTSs operational before MB training (available at IMH Reset PH3) | SOC HSD 22018755448 §2 |
| FR2 | CBB waits for valid UCIe DTS temps before sending ready_for_d2d_mb_training | SOC HSD 22018755448 §3 |
| FR3 | Root PCode coordinates all CBBs via ready_for_d2d_mb_training HPM | SOC HSD 22018755448 §4-5 |
| FR4 | Each die applies real-time ITD using UCIe DTS temp before training starts | SOC HSD 22018755448 §6; DMR Thermal HAS §ITD |
| FR5 | No VCCUCIEA voltage change during MB training window | SOC HSD 22018755448 §10 |
| FR6 | After training: worst-case ITD (safe work-point) until kernel starts | SOC HSD 22018755448 §9 |
| FR7 | Both sides aligned via UCIe Phy handshake before training begins | UCIe Phy HAS §mbinit |
| FR8 | Primecode reads UCIE temp directly from DTS (not via RC pullout) | SOC HSD 22018755448 — "read directly without waiting for RC pullout" |
| FR9 | Shared FIVR uses coldest D2D stack temperature for ITD calculation | SOC HSD assumptions §4 |

---

## Section 3: Test Strategy

| Approach | Detail |
|---|---|
| Reset breakpoint | Set breakpoint at pre-training phase, observe VCCUCIEA voltage |
| Phase-boundary observation | Read VCCUCIEA VID at: pre-training, post-training, kernel start |
| DTS injection | Override UCIe DTS temperature to known value for deterministic ITD calc |
| Warm reset trigger | Trigger warm reset to exercise full sequence |
| Cross-die observation | Verify both IMH and CBB sides apply ITD before training starts |

---

## Section 4: Programming Model

**3-Phase VCCUCIEA voltage behavior:**

1. **Pre-training (after UCIe DTS valid, before MB training):**
   - Primecode reads UCIe DTS directly (no RC pullout dependency)
   - Computes real-time ITD: base + slope × (cutoff_v − base) × (cutoff_tj − temp)
   - Programs VCCUCIEA FIVR to computed real-time ITD target
   - For shared FIVRs (SW/SE): uses coldest temperature of connected D2D stacks

2. **During MB training (~2ms):**
   - VCCUCIEA FROZEN — no changes even if temperature drifts
   - Temperature may drift ±5°C during 2ms training window (acceptable per spec)

3. **Post-training (before kernel):**
   - Set worst-case ITD (safe work-point) — maximum voltage guard
   - No mainband traffic exists yet (safe to hold conservative voltage)
   - Remains at worst-case until kernel starts periodic real-time ITD

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Phase 1: real-time ITD applied | VCCUCIEA at training start = base + computed ITD from UCIe DTS | SOC HSD 22018755448 §6 |
| Phase 2: worst-case post-training | VCCUCIEA after training = worst-case ITD (conservative safe point) | SOC HSD 22018755448 §9 |
| Phase 3: real-time resumes | After kernel start, VCCUCIEA tracks periodic real-time ITD | DMR Thermal HAS §ITD |
| No change during training | VCCUCIEA VID unchanged throughout 2ms training window | SOC HSD 22018755448 §10 |
| DTS direct read | Primecode reads UCIe DTS directly, not via RC pullout path | SOC HSD 22018755448 §reading |
| Shared FIVR: coldest temp | For SW/SE (2 stacks), ITD uses coldest stack temperature | SOC HSD assumptions |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| Basic 3-phase sequence via warm reset | [22022421534](https://hsdes.intel.com/appstore/article-one/#/22022421534) (partial) | FV, HSLE | ⚠️ PARTIAL |
| UCIe DTS valid before training checkpoint | *(TC TBD)* | FV, VP | ⚠️ GAP |
| Shared FIVR: coldest temp selection (SW/SE) | *(TC TBD)* | FV | ⚠️ GAP |
| Cross-die coordination: both sides complete ITD before training handshake | *(TC TBD)* | FV, HSLE XOS | ⚠️ GAP |
| Temperature gradient between adjacent D2D stacks on same FIVR | *(TC TBD)* | FV | ⚠️ GAP |
| Post-training worst-case held until kernel (tens of ms gap) | *(TC TBD)* | FV | ⚠️ GAP |
| Direct DTS read (no RC pullout dependency) | *(TC TBD)* | FV, VP | ⚠️ GAP |

---

## Section 7: Dependencies

| Dependency | Impact |
|---|---|
| TCD ITD-CONTRACT-003 (steady-state) | ITD algorithm must be correct for pre-training calculation to be valid |
| TCD ITD-FUSE-001 (fuse checkout) | Fuse coefficients must be valid for ITD calculation |
| UCIe DTS operational | DTSs must be up at Reset PH3 — prerequisite for temp read |
| Root PCode HPM coordination | ready_for_d2d_mb_training HPM must work correctly |

---

## Section 8: Open Items

| Item | Status | Notes |
|---|---|---|
| HSD TCD ID | pending | Create in HSD under TPF 16031170066 |
| TC 22022421534 re-home | pending | Move parent from 16031170075 to this TCD; verify it covers Phase 1 |
| New TC: full 3-phase | pending | Author TC covering all three phase boundaries |
| Env feasibility: XOS | TBD-T7 | Cross-die coordination requires HSLE XOS — confirm model coverage |
| Worst-case ITD value | confirm | Determine expected worst-case VID for bar comparison |

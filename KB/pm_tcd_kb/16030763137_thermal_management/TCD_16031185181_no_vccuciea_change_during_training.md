# TCD: ITD-SCENARIO-004 - No VCCUCIEA Change During MB Training

| Field | Value |
|-------|-------|
| **TCD ID** | [16031185181](https://hsdes.intel.com/appstore/article-one/#/16031185181) |
| **Title** | ITD-SCENARIO-004 - No VCCUCIEA Change During MB Training |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | VCCUCIEA D2D VCCIO ITD |
| **NWP Disposition** | Needs_Adaptation (same invariant as DMR; NWP reset flow timing may differ) |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | SOC HSD 22018755448 §10; D2D PM HAS — "during MB training Primecode must not change VCCUCIEA"; UCIe electrical ITD table |
| **Co-Design T2 origin** | Table 2 row 5 (new) — 2026-07-21 |

---

## Definition Block

- **Layer:** 3 (Scenario)
- **Sentence:** During UCIe mainband training, no VCCUCIEA ITD voltage change occurs even if temperature changes; if reset entry occurs during training (surprise reset), VCCUCIEA is NOT reverted and post-reset-exit returns to boot defaults via HWRS.
- **Gate:** ITD-SCENARIO-003 (Pre-Training VCCUCIEA ITD Sequencing — normal pre-training flow works)
- **Suspect:** IMH Primecode ITD kernel suppression during training window; HWRS FIVR restore logic on surprise reset
- **Setup:** System in MB training phase. Temperature injection capability to drive ITD trigger during training window.
- **Check:** (1) Inject temperature change during training → verify no VCCUCIEA voltage change. (2) Trigger reset entry during training → verify no ITD reversal during training, and post-reset VCCUCIEA returns to boot defaults.
- **Invariant:** (1) VCCUCIEA VID is constant throughout the MB training window regardless of temperature change; (2) Reset entry during training does NOT trigger ITD reversal; (3) After reset exit, HWRS restores VCCUCIEA FIVR to default boot settings (not to the in-training ITD value).

---

## Section 1: Architecture / Micro-architecture and Functionality

**No VCCUCIEA Change During MB Training** is a **negative validation** TCD. It verifies the absence of ITD action during a critical window where VCCUCIEA changes would degrade UCIe link margins. During the ~2ms MB training window, Phy is calibrating terminations and delay lines — any voltage change would invalidate the calibration in progress.

> **Architecture overview:** See [TPF 16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) §2 Design Details

### NWP Delta

- Same negative invariant as DMR
- Training window ~2ms (±10%)
- Temperature can drift ±5°C during training — this is acceptable and must NOT trigger voltage change
- Surprise reset during training treated as link reset; HWRS restores FIVR to boot defaults

### Why This Is a Separate TCD

The pre-training sequencing TCD (ITD-SCENARIO-003) validates that the *correct* voltages are applied at phase boundaries. This TCD validates that *nothing happens* during the training window. The bar is fundamentally different:
- SCENARIO-003: voltage matches expected value (positive)
- SCENARIO-004: voltage does NOT change (negative)

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | During MB training, Primecode must not change VCCUCIEA even if temperature changes | SOC HSD 22018755448 §10 |
| FR2 | No ITD compensation during PHY link training | UCIe electrical ITD table |
| FR3 | Reset entry during training treated as surprise reset | SOC HSD 22018755448 — "reset will be treated as a surprise reset" |
| FR4 | No ITD reversal during surprise reset in training window | SOC HSD 22018755448 — "this scenario should not affect reset entry" |
| FR5 | After reset exit, HWRS restores VCCUCIEA FIVR to default boot settings | SOC HSD 22018755448 — "HWRS will restore the VCCUCIEA FIVR to its default boot settings" |
| FR6 | Surprise reset during training triggers link reset (UCIe perspective) | UCIe Phy HAS — link reset behavior |
| FR7 | Temperature drift during training acceptable (±5°C in 2ms) | SOC HSD 22018755448 — assumptions §mainband-training-temperatures-drifts |

---

## Section 3: Test Strategy

| Approach | Detail |
|---|---|
| Training window observation | Monitor VCCUCIEA VID continuously during MB training; verify no change |
| Temperature injection during training | Inject >5°C temp change during training window; verify VID unchanged |
| Surprise reset injection | Trigger reset entry while MB training is active |
| Post-reset verification | After surprise reset exit, verify VCCUCIEA at boot defaults (not training-time ITD) |
| Timing confirmation | Confirm training window is ~2ms; verify freeze covers entire window |

---

## Section 4: Programming Model

**Negative validation logic:**

1. **Normal case (temp change during training):**
   - MB training starts with VCCUCIEA at real-time ITD value (per SCENARIO-003)
   - Temperature changes during 2ms training window
   - Primecode detects temp change but ITD kernel is SUPPRESSED during training
   - VCCUCIEA VID remains at pre-training value throughout
   - After training completes: worst-case ITD applied (per SCENARIO-003)

2. **Surprise reset during training:**
   - Reset entry occurs while MB training active
   - Primecode has NOT started its kernel (no systematic ITD reversal logic)
   - VCCUCIEA is NOT at worst-case ITD (it's at pre-training real-time ITD)
   - This is acceptable — no data traffic exists during training anyway
   - After reset exit: HWRS restores VCCUCIEA FIVR to boot default settings
   - Next boot: normal pre-training ITD sequence runs again (SCENARIO-003)

**What does NOT happen:**
- No DVFS handshake during training (Phy enforces mutex)
- No ITD kernel execution during training
- No voltage reversal on surprise reset during training

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| VID frozen during training | VCCUCIEA VID at training-end == VID at training-start (no change) | SOC HSD 22018755448 §10 |
| Temp change ignored | With >5°C injected temp change during training, VID unchanged | SOC HSD assumptions |
| No surprise-reset reversal | Reset entry during training does NOT trigger VCCUCIEA VID change | SOC HSD 22018755448 |
| Post-reset boot defaults | After surprise-reset exit, VCCUCIEA = HWRS boot default (not training-time ITD) | SOC HSD 22018755448 — HWRS restore |
| Training window covers full duration | Freeze maintained for full ~2ms training window | SOC HSD 22018755448 |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| Temp change during training — no VID change (basic negative) | *(TC TBD)* | FV, HSLE XOS | ⚠️ GAP |
| Large temp drift (+5°C) during training — still no change | *(TC TBD)* | FV | ⚠️ GAP |
| Surprise reset mid-training — no ITD reversal | *(TC TBD)* | FV | ⚠️ GAP |
| Post-surprise-reset: VCCUCIEA at boot defaults | *(TC TBD)* | FV | ⚠️ GAP |
| Seamless patch within training window (race condition) | *(TC TBD)* | FV | ⚠️ GAP |
| Training completes normally → verify freeze lifts (boundary with SCENARIO-003) | *(TC TBD)* | FV, HSLE XOS | ⚠️ GAP |

---

## Section 7: Dependencies

| Dependency | Impact |
|---|---|
| TCD ITD-SCENARIO-003 (pre-training) | Normal pre-training ITD must work for the training-start voltage to be correct |
| MB training active state | Need to observe/control training window timing |
| Reset injection capability | Must be able to trigger reset entry during training (tight timing window) |
| HWRS FIVR restore | HWRS must correctly restore VCCUCIEA after surprise reset |

---

## Section 8: Open Items

| Item | Status | Notes |
|---|---|---|
| HSD TCD ID | pending | Create in HSD under TPF 16031170066 |
| TC authoring | pending | Need method to inject reset during 2ms training window |
| Training window detection | pending | How to confirm "in training" state for timing the reset injection |
| Env feasibility: HSLE XOS | TBD-T7 | Cross-die training requires both dies; confirm model supports surprise reset during training |
| Boot default VID value | confirm | Determine expected HWRS boot default for VCCUCIEA to compare post-reset |

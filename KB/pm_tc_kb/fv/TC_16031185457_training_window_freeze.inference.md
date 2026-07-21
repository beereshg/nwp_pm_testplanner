# TC 16031185457 — ITD-SCENARIO-004 / FV / training-window-freeze

## Test Case Intent

Validates two critical negative-validation invariants: (1) VCCUCIEA voltage does NOT change during the UCIe mainband training window, even when temperature changes occur; (2) if a surprise reset occurs during training, VCCUCIEA is NOT reverted during the training window, and post-reset-exit returns to HWRS boot defaults.

### Pre-Conditions

1. NWP silicon platform with UCIe D2D links capable of warm-reset retraining
2. ITD enabled with valid fuse coefficients (ITD-FUSE-001 passed)
3. Pre-training VCCUCIEA ITD sequencing working (ITD-SCENARIO-003 — TC 22022421534 passed)
4. PythonSV access to VCCUCIEA VID registers, reset control, and DTS override
5. Ability to trigger warm reset and observe VCCUCIEA during reset sequence
6. DTS override capability to inject temperature change during training window
7. Training window breakpoint or timing marker available (to confirm "in training" state)

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Trigger warm reset to initiate UCIe mainband retraining sequence | Reset sequence starts; observe pre-training ITD applied to VCCUCIEA | Reset does not trigger retraining |
| 2 | Set breakpoint/marker at MB training start; record VCCUCIEA VID at training entry | VID captured as V_training_start (= base + real-time ITD) | Cannot capture training-start VID |
| 3 | During MB training window (~2ms): inject DTS temperature change of +5°C via override | DTS readback confirms +5°C change; verify Primecode ITD kernel detects it | DTS override not reflected |
| 4 | Read VCCUCIEA VID during training (within the 2ms window) | VID unchanged from V_training_start — FROZEN despite temp change | VID changed during training (FAIL — spec violation) |
| 5 | Wait for training completion; read VCCUCIEA VID after training | VID = worst-case ITD (safe work-point) per ITD-SCENARIO-003 | VID still at training-start value or incorrect post-training |
| 6 | Verify freeze duration covers full training window | No VCCUCIEA VID change for entire ~2ms training period | VID changes before training complete |
| 7 | (Surprise reset scenario) Trigger a second warm reset | Reset sequence starts again | — |
| 8 | During MB training of the second reset: inject reset entry (surprise reset) | Surprise reset initiated while training is active | Unable to inject reset during training window |
| 9 | Observe VCCUCIEA during surprise-reset-in-training | VID does NOT change (no ITD reversal during training) | VID reverted or changed during surprise reset window |
| 10 | After surprise reset exit: read VCCUCIEA VID | VID = HWRS boot default (not the in-training ITD value) | VID at in-training value or unexpected voltage |
| 11 | Verify next boot performs normal pre-training ITD sequence | Normal 3-phase ITD behavior resumes on subsequent boot | Pre-training ITD sequence broken after surprise reset |

### Pass / Fail Criteria

**PASS:**
- VCCUCIEA VID at training-end == VID at training-start (zero change during training window)
- VID unchanged despite +5°C DTS injection during training
- Freeze maintained for full ~2ms training duration
- Surprise reset during training does NOT trigger VID change
- Post-surprise-reset-exit: VCCUCIEA = HWRS boot default
- Subsequent boot: normal pre-training ITD sequence resumes correctly

**FAIL:**
- Any VCCUCIEA VID change observed during the training window
- ITD reversal triggered by surprise reset during training
- Post-surprise-reset VCCUCIEA NOT at boot defaults (retains in-training ITD)
- Subsequent boot fails to perform pre-training ITD (sequence broken)

### Post-Process

N/A — FV automated comparison.

## References

- [TCD 16031185181 — ITD-SCENARIO-004](https://hsdes.intel.com/appstore/article-one/#/16031185181)
- [SOC HSD 22018755448 — VCCUCIEA ITD before mainband training](https://hsdes.intel.com/appstore/article/#/22018755448)
- [D2D PM HAS — "during MB training Primecode must not change VCCUCIEA"](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D_PM/D2D_PM.html)
- [DMR Thermal HAS §ITD](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#itd)

## Section E: Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Injecting reset during the 2ms training window requires precise timing | high | Use PythonSV breakpoint at training-start + timed reset injection; alternatively use HSLE XOS with controllable clock |
| Confirming "in training" state from outside the Phy is non-trivial | high | Use Primecode debug trace markers or VISA sideband capture to confirm training active |
| Post-reset HWRS boot default VID value must be known for comparison | medium | Determine from HWRS register spec or capture from a clean boot baseline |
| Temperature injection during training may not be reflected until next ITD cycle | low | Acceptable — test validates that even if detected, no action is taken |

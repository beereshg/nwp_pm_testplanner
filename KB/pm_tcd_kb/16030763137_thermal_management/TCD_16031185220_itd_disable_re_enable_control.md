# TCD: ITD-CONTRACT-001b - ITD Disable/Re-Enable Control

| Field | Value |
|-------|-------|
| **TCD ID** | [16031185220](https://hsdes.intel.com/appstore/article-one/#/16031185220) |
| **Title** | ITD-CONTRACT-001b - ITD Disable/Re-Enable Control |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | ITD Global Control |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | DMR CBB HAS ITD §disable; DMR thermal / ITD common controls |
| **Split from** | [16031170075](https://hsdes.intel.com/appstore/article-one/#/16031170075) (decomposed) |

---

## Definition Block

- **Layer:** 1 (Contract)
- **Sentence:** Setting ITD_SLOPE and ITD_SLOPE_2 to zero for a domain disables ITD compensation (0V offset), and restoring original slopes re-enables normal ITD behavior.
- **Gate:** ITD-FUSE-001 (Coefficient Fuse Configuration Validity — fuses are valid before we test disable)
- **Suspect:** IMH Primecode ITD kernel slope consumption; PCode vars slope update path; per-domain pcudata register write
- **Setup:** ITD enabled, all domains actively compensating (non-zero ITD offset observed). PythonSV access to pcudata slope registers.
- **Check:** Write all IMH pcudata slope registers to zero → observe ITD offset goes to 0 for all domains. Restore original slopes → observe compensation resumes.
- **Invariant:** While disabled (slopes=0): all domains report 0V ITD offset (voltage = uncompensated base only). After re-enable (slopes restored): all domains return to computed real-time ITD within one FW update cycle.

---

## Section 1: Architecture / Micro-architecture and Functionality

**ITD Disable/Re-Enable Control** validates the debug mechanism for suppressing ITD compensation. By writing ITD_SLOPE (and SLOPE_2 where applicable) to zero, the ITD algorithm computes 0V compensation — the domain runs at its uncompensated ACTIVE_VOLTAGE (fixed-freq) or VF voltage (variable-freq). This mechanism is for **debug only** — in production, ITD is always enabled for electrical correctness.

> **Architecture overview:** See [TPF 16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) §2 Design Details

### NWP Delta

- Same disable mechanism as DMR (slope zeroing)
- NWP new domains (VCCCAB, VCCC2CDIG) must also respond to disable

### Disable Mechanism

```
Normal operation:
  V_target = V_base + slope × f(temp, cutoff_v, cutoff_tj)

Disabled (slope = 0):
  V_target = V_base + 0 × f(...) = V_base
  → Domain runs at uncompensated active voltage
```

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | Setting ITD_SLOPE to 0 causes 0V ITD compensation for that domain | DMR CBB HAS ITD §disable |
| FR2 | Disabled domain runs at ACTIVE_VOLTAGE (fixed-freq) or VF voltage (variable-freq) | DMR thermal / ITD |
| FR3 | Restoring original slopes resumes normal ITD compensation | DMR CBB HAS ITD |
| FR4 | Disable is per-domain (disabling one domain does not affect others) | DMR thermal |
| FR5 | Re-enable takes effect within one FW update cycle | DMR thermal / ITD loop rate |

---

## Section 3: Test Strategy

| Approach | Detail |
|---|---|
| Baseline capture | Record voltage with ITD active (non-zero offsets) |
| Global disable | Write all IMH pcudata slope registers to zero |
| Observe suppression | Wait for FW update cycle; verify all domains return to base-only voltage |
| Re-enable | Restore original slopes |
| Observe restoration | Verify compensation resumes (voltage returns to base + ITD offset) |

---

## Section 4: Programming Model

ITD disable is achieved by writing slope registers to zero:
- **IMH domains:** Write `pcudata` slope registers for each RC (cfcio, cfcmem, mio, ucie, vinf)
- **CBB domains:** Write via PCode vars (`pcode.vars.ring.vf_curve.at{slice}.itd.slope`)
- **Effect:** ITD algorithm input slope=0 → output=0V compensation
- **Restoration:** Write back saved original slope values

Per the spec: "ITD for any domain can be disabled by setting its ITD_SLOPE and ITD_SLOPE_2 (if applicable) to 0. This will cause the ITD algorithm to always calculate a voltage compensation of 0V, and thus pass through the uncompensated voltage."

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Disable → zero offset | All domains show 0V ITD offset within FW update cycle after slope zeroed | DMR CBB HAS ITD §disable |
| Base-only voltage | Disabled domain voltage = ACTIVE_VOLTAGE (no compensation) within 26 mV | DMR thermal |
| Re-enable → restore | After slope restore, voltage returns to base + computed ITD within 26 mV | DMR thermal |
| Per-domain isolation | Disabling one domain does not suppress adjacent domains | DMR thermal |
| Latency | Transition completes within one FW update cycle (~1ms) | DMR thermal / loop rate |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| Global disable (all domains) → verify zero offset | [22022421528](https://hsdes.intel.com/appstore/article-one/#/22022421528) | FV, HSLE | ✅ |
| Re-enable after disable → verify compensation resumes | within 22022421528 | FV, HSLE | ✅ |
| Per-domain disable (single domain only) | *(TC TBD)* | FV | ⚠️ GAP |
| NWP new domain (VCCCAB) disable/re-enable | *(TC TBD)* | FV | ⚠️ GAP |
| Disable during active thermal stress (voltage stability) | *(TC TBD)* | FV | ⚠️ GAP |
| Rapid enable/disable toggle (no hang, no stale voltage) | *(TC TBD)* | FV | ⚠️ GAP |

---

## Section 7: Dependencies

| Dependency | Impact |
|---|---|
| TCD ITD-FUSE-001 (fuse validity) | Fuses must be valid so baseline ITD is active before testing disable |
| PythonSV pcudata write access | Must be able to write slope registers |
| FW update cycle timing | Need to wait for FW to consume new slope value |

---

## Section 8: Open Items

| Item | Status | Notes |
|---|---|---|
| Per-domain isolation TC | pending | Test disabling single domain without affecting others |
| NWP new domain coverage | pending | Verify VCCCAB and VCCC2CDIG respond to disable |

# TCD: ITD-CONTRACT-001 - ITD Global Enable/Disable & Reset

| Field | Value |
|-------|-------|
| **TCD ID** | [16031179275](https://hsdes.intel.com/appstore/article-one/#/16031179275) |
| **Title** | ITD-CONTRACT-001 - ITD Global Enable/Disable & Reset |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Global Enable/Disable & Reset Behavior |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | DMR CBB HAS ITD, Wave3_common Socket Thermal Mgmt HAS, NWP reset MAS |

---

## Definition Block

- **Layer:** 1 (Contract)
- **Sentence:** Disabling ITD zeroes compensation across all domains; reset re-initializes ITD from fuses with worst-case safe values before memory training and real-time values during training.
- **Gate:** ITD-FUSE-001 (Coefficient Fuse Checkout)
- **Suspect:** PCode ITD enable/disable logic; reset-time ITD initialization sequence
- **Setup:** ITD enabled, compensation active on at least one domain. Fuse checkout passed.
- **Check:** Disable ITD → read VID across all domains. Reset → observe ITD state transitions through boot phases.
- **Invariant:** Disabled: VID delta from ITD = 0 on all domains. Reset: pre-MB-training ITD at worst-case/safe values; during-MB-training ITD at real-time values; post-training ITD at safe values until reset complete.

---

## Section 1: Architecture / Micro-architecture and Functionality

**ITD Global Enable/Disable & Reset** validates the cross-domain ITD control mechanisms: global ITD enable/disable path and reset-time behavior (worst-case ITD during memory training phases). These are shared control/safety mechanisms that apply across ALL ITD-capable domains.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

### Key Behavioral Facts

- **Disable path:** ITD disable → compensation zeroed across all domains; VID returns to uncompensated baseline
- **Re-enable:** ITD re-enable → compensation resumes per fuse coefficients and current temperature
- **Reset-time behavior:** Before MB training = worst-case/safe ITD; during training = real-time ITD; after training = safe again until reset complete
- **MIN_ACCURATE_TEMP:** Guard — ITD compensation not applied below this temperature (unreliable DTS readings); uses `ITD_MIN_OVERRIDE_TEMP` instead

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | ITD disable → compensation zeroed across all domains | DMR CBB HAS ITD |
| FR2 | ITD re-enable → compensation resumes from current temp + fuse coefficients | DMR CBB HAS ITD |
| FR3 | Reset-time: worst-case/safe ITD before MB training | Wave3_common Socket Thermal Mgmt HAS |
| FR4 | Reset-time: real-time ITD during MB training | Wave3_common Socket Thermal Mgmt HAS |
| FR5 | Reset-time: safe ITD after MB training until reset complete | Wave3_common Socket Thermal Mgmt HAS |
| FR6 | MIN_ACCURATE_TEMP guard: no compensation below threshold; use override temp | DMR CBB HAS ITD |

---

## Section 3: Interfaces

| Interface | Direction | Description |
|---|---|---|
| ITD enable/disable control | Input | Global ITD enable/disable mechanism |
| DTS temperature sensors | Input | Temperature source for compensation calculation |
| MIN_ACCURATE_TEMP fuse | Input | Threshold below which DTS is unreliable |
| VID / FIVR voltage | Output | Compensated (or zeroed) voltage target per domain |

---

## Section 4: Programming Model

- **Enable/disable:** Platform-level ITD enable control (fuse + runtime override)
- **Fuses:** `MIN_ACCURATE_TEMP`, `ITD_MIN_OVERRIDE_TEMP`
- **Reset sequence:** FW phases set ITD state transitions (safe → real-time → safe → normal)

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Disable path | ITD disabled → VID delta from ITD = 0 on ALL domains; no residual compensation | DMR CBB HAS ITD |
| Re-enable | ITD re-enabled → compensation resumes within 1 RAPL cycle; VID matches expected for current temp | DMR CBB HAS ITD |
| Reset worst-case | During boot before MB training: ITD at worst-case/safe values (not real-time computed) | Wave3_common |
| Reset real-time | During MB training: ITD transitions to real-time computed values | Wave3_common |
| MIN_ACCURATE_TEMP | Below MIN_ACCURATE_TEMP: ITD uses override temp (not raw DTS); above: normal DTS | DMR CBB HAS ITD |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| ITD global disable — all domains zeroed | [22022421528](https://hsdes.intel.com/appstore/article-one/#/22022421528) | FV, HSLE | |
| ITD during reset — boot phase transitions | [22022421534](https://hsdes.intel.com/appstore/article-one/#/22022421534) | FV, HSLE, VP | |
| ITD disable → re-enable transition | within 22022421528 | FV, HSLE | |
| MIN_ACCURATE_TEMP boundary (at/below/above) | within 22022421528 or 22022421534 | FV, HSLE | ⚠️ PARTIAL |
| Reset-time: MB training exit → safe ITD restoration | within 22022421534 | FV, HSLE | |

---

## Section 8: Open Items

- Confirm MIN_ACCURATE_TEMP threshold value for NWP
- Verify ITD_MIN_OVERRIDE_TEMP expected value on NWP
- Check whether disable/re-enable latency is spec'd (potential timing bar addition)

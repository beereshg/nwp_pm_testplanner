# TCD: PEM Correlating Timings

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421012](https://hsdes.intel.com/appstore/article-one/#/22022421012) |
| **Title** | Correlating Timings |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [16030767512 — [NWP PM] PEM (Power and Energy Monitoring)](https://hsdes.intel.com/appstore/article-one/#/16030767512) |
| **Feature** | PEM — Counter Timing Accuracy |
| **Validation Phase** | **Alpha / Beta** — Feature enabling + functional validation |
| **Child TCs** | [22022422353](https://hsdes.intel.com/appstore/article-one/#/22022422353) — Correlating timings I3C<br>[22022422356](https://hsdes.intel.com/appstore/article-one/#/22022422356) — Correlating timings PCIe<br>[22022422358](https://hsdes.intel.com/appstore/article-one/#/22022422358) — Correlating timings TPMI<br>[22022422361](https://hsdes.intel.com/appstore/article-one/#/22022422361) — Correlating timings VP |
| **KB last updated** | 2026-07-19 |

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 16030767512 — PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512) §2 Design Details for EWMA algorithm, counter semantics, and interface matrix.

**PEM Correlating Timings** validates that PEM_COUNTER duration counters accurately track real throttle duration at the spec-defined 1 ms/count rate. The counter must start incrementing when EWMA-filtered excursion status transitions from 0→1, stop when excursion clears, and the accumulated count must correlate with independently measured throttle duration.

### Spec Refs

- PEM HAS §"EWMA Algorithm" — counter unit = 1 ms; wraparound at ~49 days
- PEM HAS §"PEM_COUNTER" — increments only while corresponding excursion is actively occurring

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| TPMI PEM_STATUS | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | Observe excursion assertion/de-assertion transitions |
| PMT PEM_COUNTER | Via PMT GUID readout | Duration counter — 1 ms/count |
| I3C / PCIe / TPMI / VP | Multiple paths | Cross-interface counter consistency |

---

## Section 3: Reset, Power, and Clocking

- PEM_COUNTER is not reset on PEM disable/re-enable — preserved across enable cycles
- Counter unit tied to PCode slowloop (~1 ms) — counter accuracy depends on slowloop cadence stability
- Wraparound at 2^32 ms (~49.7 days) — SW must handle

---

## Section 4: Programming Model

```python
# 1. Enable PEM, configure FET and TW
sv.socket0.cbb0.base.tpmi.pem_control.write(
    (FET_RATIO << 0) | (TW_VALUE << 8) | (1 << 31)
)

# 2. Record baseline counter
counter_before = read_pmt_pem_counter(event_id=10)  # PL1 INBAND

# 3. Inject throttle for exactly T seconds
import time
inject_rapl_pl1_throttle()
time.sleep(T)
release_rapl_pl1_throttle()

# 4. Read counter after
counter_after = read_pmt_pem_counter(event_id=10)

# 5. Validate timing accuracy
delta_ms = counter_after - counter_before
expected_ms = T * 1000
assert abs(delta_ms - expected_ms) / expected_ms < 0.10  # ±10%
```

---

## Section 5: Pass/Fail Bar

**Bar (counter timing accuracy):**

| Criterion | Threshold | Spec ref |
|-----------|-----------|----------|
| Counter increment rate | 1 ms/count ±10% of independently measured throttle duration | PEM HAS §"EWMA Algorithm" — counter unit = 1 ms |
| Counter start transition | Begins incrementing within 1 PCode slowloop (~1 ms) of EWMA excursion assertion | PEM HAS §"PEM_COUNTER" |
| Counter stop transition | Stops incrementing within 1 slowloop of excursion de-assertion | PEM HAS §"PEM_COUNTER" |
| Cross-interface consistency | Same counter value (±1 count jitter) read from I3C, PCIe, TPMI, VP | PEM HAS §"Interface Matrix" — single backing register |
| Counter monotonicity | Counter never decrements during active excursion | PEM HAS §"PEM_COUNTER" |

**FAIL:** Counter delta deviates > 10% from measured throttle duration; counter does not start/stop at excursion transitions; counter decrements; interface reads disagree by > 1 count.

---

## Section 6: TC Coverage Map & Corner Cases

| TC | Interface | Scope |
|----|-----------|-------|
| [22022422353](https://hsdes.intel.com/appstore/article-one/#/22022422353) | I3C (OOB) | Timing accuracy via BMC I3C counter read |
| [22022422356](https://hsdes.intel.com/appstore/article-one/#/22022422356) | PCIe (PMT) | Timing accuracy via PCIe MMIO counter read |
| [22022422358](https://hsdes.intel.com/appstore/article-one/#/22022422358) | TPMI (inband) | Timing accuracy via TPMI counter read |
| [22022422361](https://hsdes.intel.com/appstore/article-one/#/22022422361) | VP (Simics) | Timing accuracy via Simics model |

### Corner Cases

| Corner Case | Expected Behavior | Env |
|---|---|---|
| Very short throttle (< 5 ms) | Counter increments by ≤5 counts; timing tolerance wider for short durations | Si=Full |
| Very long throttle (> 300 s) | Counter continues incrementing at 1 ms/count without overflow | Si=Full |
| Throttle toggle (on-off-on rapidly) | Counter increments only during "on" intervals; "off" intervals not counted | Simics=Full, Si=Full |
| Counter read during active increment | Read returns stable value (no torn reads across 32-bit boundary) | Si=Full |
| TW change during active excursion | EWMA re-evaluates with new TW; counter behavior tracks updated threshold | Simics=Full |

---

## Section 7: Security / Safety / Policy

- PEM_COUNTER is read-only — no risk of counter manipulation
- Timing accuracy depends on PCode slowloop stability — any slowloop stall extends effective counter unit beyond 1 ms

---

## Section 8: References

| Reference | Link |
|-----------|------|
| PEM HAS (Wave3 common) | [PEM_HAS.html](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html) |
| DMR PM HAS — PEM | [DMR_PEM.html](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html) |
| NWP PM MAS | [nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| Parent TPF KB | [TPF_16030767512](../pm_tpf_kb/16030767511_nwp_pm_telemetry_pem_plr/TPF_16030767512_nwp_pm_pem_power_and_energy_monitoring.md) |
| KB Feature Article | [pem.md](../../pm_features/power_rapl/pem.md) |
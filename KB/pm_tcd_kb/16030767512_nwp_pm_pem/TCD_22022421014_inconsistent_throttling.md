# TCD: PEM Inconsistent Throttling

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421014](https://hsdes.intel.com/appstore/article-one/#/22022421014) |
| **Title** | Inconsistent Throttling |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [16030767512 — [NWP PM] PEM (Power and Energy Monitoring)](https://hsdes.intel.com/appstore/article-one/#/16030767512) |
| **Feature** | PEM — EWMA Transient Rejection & Intermittent Excursion Filtering |
| **Validation Phase** | **Alpha / Beta** — Feature enabling + functional validation |
| **Child TCs** | [22022422363](https://hsdes.intel.com/appstore/article-one/#/22022422363) — Inconsistent throttling I3C<br>[22022422372](https://hsdes.intel.com/appstore/article-one/#/22022422372) — Inconsistent throttling PCIe<br>[22022422374](https://hsdes.intel.com/appstore/article-one/#/22022422374) — Inconsistent throttling TPMI<br>[22022422377](https://hsdes.intel.com/appstore/article-one/#/22022422377) — Inconsistent throttling VP |
| **KB last updated** | 2026-07-19 |

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 16030767512 — PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512) §2 Design Details for EWMA algorithm, consistent vs inconsistent throttle classification, and PEM_STATUS semantics.

**PEM Inconsistent Throttling** validates PEM behavior under **intermittent or partial** throttle conditions — where power transiently exceeds the limit but returns below FET before the EWMA window fully converges, or where only a subset of cores are throttled. The EWMA filter (threshold = 0.9) must correctly reject transient events and only assert PEM_STATUS when the rolling average exceeds 0.9.

### Spec Refs

- PEM HAS §"EWMA Algorithm" — `avg_set_status[r] = EWMA(set_status[r])` over TW; assertion only when avg > 0.9
- PEM HAS §"Execution Flow" — EWMA runs continuously regardless of PEM_STATUS value; ensures re-detection after SW clears

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| TPMI PEM_STATUS | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | Observe that transient excursions are filtered |
| TPMI PEM_CONTROL | `sv.socket0.cbb{0,1}.base.tpmi.pem_control` | Configure FET, TW for transient filtering |
| PMT PEM_COUNTER | Via PMT GUID readout | Verify counter increments only during EWMA-asserted intervals |
| I3C / PCIe / TPMI / VP | Multiple paths | Cross-interface observation of filtering behavior |

---

## Section 3: Reset, Power, and Clocking

- EWMA state is maintained per-event regardless of PEM_STATUS read/clear — SW clearing PEM_STATUS does not reset the EWMA accumulator
- PEM_STATUS is RW0C — SW clear does not affect the underlying EWMA evaluation
- EWMA convergence time depends on TW: shorter TW = faster assertion/de-assertion

---

## Section 4: Programming Model

```python
# 1. Enable PEM with a moderate TW (e.g. TW=5 → ~74 ms window)
sv.socket0.cbb0.base.tpmi.pem_control.write(
    (FET_RATIO << 0) | (5 << 8) | (1 << 31)  # FET + TW=5 + ENABLE
)

# 2. Inject short throttle bursts (< EWMA window)
for burst in range(10):
    inject_rapl_pl1_throttle()
    time.sleep(0.020)  # 20 ms burst — shorter than TW
    release_rapl_pl1_throttle()
    time.sleep(0.100)  # 100 ms gap

# 3. Verify PEM_STATUS stays 0 (transient rejection)
status = sv.socket0.cbb0.base.tpmi.pem_status.read()
assert (status & (1 << 10)) == 0  # PKG_PL1_INBAND should NOT be set

# 4. Now inject sustained throttle (> TW) — should set
inject_rapl_pl1_throttle()
time.sleep(0.200)  # 200 ms > 74 ms TW
status = sv.socket0.cbb0.base.tpmi.pem_status.read()
assert status & (1 << 10)  # NOW PL1 should be set
```

---

## Section 5: Pass/Fail Bar

**Bar (EWMA transient rejection):**

| Criterion | Threshold | Spec ref |
|-----------|-----------|----------|
| Transient rejection | PEM_STATUS[reason] = 0 for throttle bursts where EWMA avg < 0.9 | PEM HAS §"EWMA Algorithm" — threshold = 0.9 |
| Eventual assertion | PEM_STATUS[reason] = 1 when intermittent throttle EWMA avg ≥ 0.9 | PEM HAS §"EWMA Algorithm" |
| Counter gating | PEM_COUNTER increments only during EWMA-asserted intervals, not during rejected transients | PEM HAS §"PEM_COUNTER" — increments only while excursion actively occurring |
| EWMA continuity | After SW clears PEM_STATUS (W0C), EWMA continues evaluating — re-assertion occurs without restart if excursion persists | PEM HAS §"EWMA Algorithm" — runs continuously |
| Per-CBB independence | Each CBB evaluates EWMA independently; one CBB may assert while other stays 0 | NWP topology — die-scoped PEM |

**FAIL:** PEM_STATUS asserts on single short burst (< TW); counter increments during rejected transient; EWMA resets after SW W0C clear; assertion does not occur even under sustained intermittent throttle with avg > 0.9.

---

## Section 6: TC Coverage Map & Corner Cases

| TC | Interface | Scope |
|----|-----------|-------|
| [22022422363](https://hsdes.intel.com/appstore/article-one/#/22022422363) | I3C (OOB) | Intermittent throttle transient rejection via I3C |
| [22022422372](https://hsdes.intel.com/appstore/article-one/#/22022422372) | PCIe (PMT) | Intermittent throttle transient rejection via PCIe |
| [22022422374](https://hsdes.intel.com/appstore/article-one/#/22022422374) | TPMI (inband) | Intermittent throttle transient rejection via TPMI |
| [22022422377](https://hsdes.intel.com/appstore/article-one/#/22022422377) | VP (Simics) | Intermittent throttle transient rejection via Simics |

### Corner Cases

| Corner Case | Expected Behavior | Env |
|---|---|---|
| Single 1ms throttle burst | EWMA avg << 0.9 → PEM_STATUS stays 0 | Simics=Full, Si=Full |
| 50% duty-cycle throttle (500ms on / 500ms off) | EWMA avg ~0.5 < 0.9 → PEM_STATUS stays 0 | Simics=Full, Si=Full |
| 95% duty-cycle throttle | EWMA avg ~0.95 > 0.9 → PEM_STATUS sets | Simics=Full, Si=Full |
| PEM bit set, load removed, bit self-clears | PEM_STATUS de-asserts when EWMA drops below 0.9 after load removal | Simics=Full, Si=Full |
| TW=0 (shortest window, ~2.3 ms) | Minimal filtering — even short bursts may assert | Simics=Full |
| TW=17 (longest window, ~302 s) | Maximum filtering — only very sustained excursions assert | Simics=Full |
| EWMA continuity across W0C clear | SW clears PEM_STATUS; EWMA re-asserts on next slowloop if still above 0.9 | Simics=Full, Si=Full |

---

## Section 7: Security / Safety / Policy

- EWMA filtering prevents false-positive PEM alerts on transient power spikes — critical for CSP SLA monitoring
- Misconfigured TW (too long) can mask real sustained throttling — validation must cover TW boundary values

---

## Section 8: References

| Reference | Link |
|-----------|------|
| PEM HAS (Wave3 common) | [PEM_HAS.html](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html) |
| DMR PM HAS — PEM | [DMR_PEM.html](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html) |
| NWP PM MAS | [nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| Parent TPF KB | [TPF_16030767512](../pm_tpf_kb/16030767511_nwp_pm_telemetry_pem_plr/TPF_16030767512_nwp_pm_pem_power_and_energy_monitoring.md) |
| KB Feature Article | [pem.md](../../pm_features/power_rapl/pem.md) |
| Sibling TCD (sustained) | [TCD 22022421010 — Consistent Throttling](https://hsdes.intel.com/appstore/article-one/#/22022421010) |
| Sibling TCD (timing) | [TCD 22022421012 — Correlating Timings](https://hsdes.intel.com/appstore/article-one/#/22022421012) |
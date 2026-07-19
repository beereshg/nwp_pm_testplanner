# TCD: PEM Consistent Throttling

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421010](https://hsdes.intel.com/appstore/article-one/#/22022421010) |
| **Title** | Consistent Throttling |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [16030767512 — [NWP PM] PEM (Power and Energy Monitoring)](https://hsdes.intel.com/appstore/article-one/#/16030767512) |
| **Feature** | PEM — Sustained Excursion Detection & Reporting |
| **Validation Phase** | **Alpha / Beta** — Feature enabling + functional validation |
| **Child TCs** | [22022422343](https://hsdes.intel.com/appstore/article-one/#/22022422343) — Consistent throttling I3C<br>[22022422346](https://hsdes.intel.com/appstore/article-one/#/22022422346) — Consistent throttling PCIe<br>[22022422348](https://hsdes.intel.com/appstore/article-one/#/22022422348) — Consistent throttling TPMI<br>[22022422351](https://hsdes.intel.com/appstore/article-one/#/22022422351) — Consistent throttling VP |
| **KB last updated** | 2026-07-19 |

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 16030767512 — PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512) §2 Design Details for full-stack cross-layer diagram, EWMA algorithm, PEM_STATUS bitfield, and interface matrix.

**PEM Consistent Throttling** validates that PCode correctly detects a **sustained** power excursion — where all cores are throttled below the Frequency Excursion Threshold (FET) by a single throttle source for the full EWMA time window — and sets the corresponding PEM_STATUS bit. The EWMA filter (threshold = 0.9) must converge to "asserted" and the PEM_COUNTER must accumulate duration at 1 ms/count.

### Spec Refs

- PEM HAS §"Execution Flow" — EWMA `avg_set_status[r] > 0.9` → `PEM_STATUS[r] = 1`; `PEM_COUNTER[r]` increment
- PEM HAS §"EWMA Algorithm" — TW formula ≈ 2.3 × 2^TW ms; threshold 0.9; continuous per-event evaluation

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| TPMI PEM_STATUS | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | Read excursion status bits (RW0C) |
| TPMI PEM_CONTROL | `sv.socket0.cbb{0,1}.base.tpmi.pem_control` | Configure FET, TW, ENABLE_PEM |
| PMT PEM_COUNTER | Via PMT GUID readout | Per-event duration counter (RO, 1 ms/count) |
| I3C | BMC ↔ CPU I3C bus | OOB PEM counter readback |
| PCIe | PMT via PCIe MMIO | OOB PEM counter readback |

---

## Section 3: Reset, Power, and Clocking

- PEM_STATUS and PEM_COUNTER are **not reset** on PEM disable/re-enable — Pcode preserves state across enable cycles
- Cold reset clears PEM_STATUS and PEM_COUNTER
- Warm reset behavior: counters preserved (implementation-dependent; verify on NWP)

---

## Section 4: Programming Model

```python
# 1. Configure PEM threshold and time window
sv.socket0.cbb0.base.tpmi.pem_control.write(
    (FET_RATIO << 0) | (TW_VALUE << 8) | (1 << 31)  # FET + TW + ENABLE_PEM
)

# 2. Inject sustained throttle (e.g. RAPL PL1 < workload power)
# ... workload runs for > TW duration ...

# 3. Read PEM_STATUS
status = sv.socket0.cbb0.base.tpmi.pem_status.read()
assert status & (1 << 10)  # PKG_PL1_INBAND bit set

# 4. Read PEM_COUNTER via PMT
counter = read_pmt_pem_counter(event_id=10)
assert counter > 0  # Duration counter accumulated
```

---

## Section 5: Pass/Fail Bar

**Bar (sustained excursion detection):**

| Criterion | Threshold | Spec ref |
|-----------|-----------|----------|
| PEM_STATUS[reason] assertion | = 1 after sustained throttle exceeds EWMA TW | PEM HAS §"Execution Flow" |
| PEM_STATUS.ANY (bit 0) | = 1 (OR of all active excursion bits) | PEM HAS §"PEM_STATUS" |
| PEM_COUNTER[reason] | > 0 and incrementing while throttle persists | PEM HAS §"PEM_COUNTER" |
| Counter accuracy | PEM_COUNTER delta within ±10% of actual throttle duration (1 ms/count) | PEM HAS §"EWMA Algorithm" — counter unit = 1 ms |
| Multi-interface consistency | Counter readable via I3C, PCIe, TPMI, VP — same value (±1 count jitter) | PEM HAS §"Interface Matrix" |
| Per-CBB independence | Each CBB (cbb0, cbb1) reports independently | NWP topology — die-scoped PEM |

**FAIL:** PEM_STATUS stays 0 after sustained throttle > TW; counter stuck at 0; counter value deviates > 10% from actual throttle duration; interface returns different counter values.

---

## Section 6: TC Coverage Map & Corner Cases

| TC | Interface | Scope |
|----|-----------|-------|
| [22022422343](https://hsdes.intel.com/appstore/article-one/#/22022422343) | I3C (OOB) | 60s sustained throttle; PEM counter via BMC I3C |
| [22022422346](https://hsdes.intel.com/appstore/article-one/#/22022422346) | PCIe (PMT) | 60s sustained throttle; PEM counter via PCIe MMIO |
| [22022422348](https://hsdes.intel.com/appstore/article-one/#/22022422348) | TPMI (inband) | 60s sustained throttle; PEM counter via TPMI |
| [22022422351](https://hsdes.intel.com/appstore/article-one/#/22022422351) | VP (Simics) | 60s sustained throttle; PEM counter via Simics model |

### Corner Cases

| Corner Case | Expected Behavior | Env |
|---|---|---|
| PL1 + PL2 simultaneous excursion | Both PEM_STATUS PL1 and PL2 bits set; ANY set | Simics=Full, HSLE=Full, Si=Full |
| PEM + PMAX concurrent throttle | All active limiter PEM bits set; PMAX ceiling priority | Si=Full |
| FastRAPL PEM bit during PL1 throttle | Both FAST_RAPL (bit 9) and PL1 (bit 10) set | Si=Full |
| PEM status RW0C race (FW write + SW clear) | SW clear must not lose FW-set bit on next slowloop | Simics=Full, Si=Full |
| Counter read at exact 1ms boundary | Counter ±1 count jitter acceptable | Si=Full |

---

## Section 7: Security / Safety / Policy

- PEM registers accessible via TPMI — requires Ring 0 or OOB privilege
- PEM_STATUS is RW0C — debug reads do NOT clear bits (only explicit 0-write clears)
- PEM_COUNTER is read-only — no write path exists (safe for telemetry consumers)

---

## Section 8: References

| Reference | Link |
|-----------|------|
| PEM HAS (Wave3 common) | [PEM_HAS.html](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html) |
| DMR PM HAS — PEM | [DMR_PEM.html](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html) |
| NWP PM MAS | [nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| Parent TPF KB | [TPF_16030767512_nwp_pm_pem_power_and_energy_monitoring.md](../pm_tpf_kb/16030767511_nwp_pm_telemetry_pem_plr/TPF_16030767512_nwp_pm_pem_power_and_energy_monitoring.md) |
| KB Feature Article | [pem.md](../../pm_features/power_rapl/pem.md) |
| Related TCD (RAPL PEM) | [TCD 16031169448 — Socket RAPL Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) |
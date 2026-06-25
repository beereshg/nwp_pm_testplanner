# TCD: [Memory Thermal Management] CLTT MR4 based

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420548](https://hsdes.intel.com/appstore/article-one/#/22022420548) |
| **Title** | [Memory Thermal Management] CLTT MR4 based |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | Memory Thermal |
| **Sub-Feature** | MR4-based CLTT |
| **NWP Disposition** | Partial — see individual TC dispositions |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CLTT MR4-based Memory Thermal** covers the hardware and firmware mechanisms that monitor, report, and respond to DIMM thermal events via **MR4-based Closed-Loop Thermal Throttling (CLTT)**. DIMMs report temperature via DDR5 MR4 reads; the Memory Controller collects these readings and compares them to programmed thresholds; Primecode / PCode thermal agents arbitrate and apply throttle limits to IMH and CBB dies.

On NWP: 2 CBBs + NIO/IMH-P root die (imh0 + imh1). Memory thermal is a **multi-die** function — the memory-side thermal source (DIMM MR4) propagates through IMH to compute-side CBBs.

### Block Diagram

```
  DIMMs / DDR5 Devices
         |  MR4 temperature data
         v
  Memory Controller (MC)
  (MR4 polling, CLTT threshold comparison)
         |  CLTT / mem thermal inputs
         v
  IMH Root Die (imh0 + imh1) <------- Thermal Sensors
         |                            (DTS / VR Hot / PROCHOT)
         |  telemetry / thermal events        |
         v                            CBB0 <--+-- Thermal Sensors
  PCode / Primecode                   CBB1 <--+-- Thermal Sensors
  Thermal Control Agents                      |
    - Evaluate vs thresholds                  |
    - Apply throttle policy        telemetry / events
    - Cross-die coordination              |
         |                                |
         +---- report -----> TPMI / MSR / PMSB
         |                  (status + control visibility)
         |
         +---- apply limits ----> IMH Root Die  (IMH thermal limit)
         +---- apply limits ----> CBB0           (CBB0 freq / throttle)
         +---- apply limits ----> CBB1           (CBB1 freq / throttle)
         |
         v
  Throttle Actions
  (freq reduction, bandwidth limit, thermal response)
```

### Feature Scope

| Layer | Component | Role |
|-------|-----------|------|
| Thermal source | DIMMs (DDR5 MR4) | Report DIMM temperature per JEDEC MR4 |
| Collection | Memory Controller | Poll MR4; compare to CLTT thresholds |
| Root die | IMH (imh0/imh1) | Aggregate memory thermal + local DTS inputs |
| Compute | CBB0, CBB1 | Receive propagated thermal limits; local DTS |
| Firmware | PCode / Primecode | Policy evaluation; throttle decisions; cross-die HPM |
| Observability | TPMI / MSR / PMSB | Status readback for validation |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421317](https://hsdes.intel.com/appstore/article-one/#/22022421317) | [MR4] Verify DIMM Thresholds match with default values progr | Revalidate (update config) |
| [22022421328](https://hsdes.intel.com/appstore/article-one/#/22022421328) | [MR4] Verify DIMM temp is updated by the MC | Runnable_On_N-1 |
| [22022421334](https://hsdes.intel.com/appstore/article-one/#/22022421334) | [MR4] Verify DIMM throttle levels values match with default  | Runnable_On_N-1 |
| [22022421341](https://hsdes.intel.com/appstore/article-one/#/22022421341) | [MR4] Verify end to end Functionality | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| TPMI | `sv.socket0.cbb0.punit.ptpcfsms.ptpcfsms.*` | Thermal status, throttle registers |
| MSR | Per-core/die MSRs (0x19C, 0x1A2, 0x1A3, 0x664, etc.) | Thermal status bits, DTS readings |
| PMSB | `sv.socket0.cbb0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| HPM | CBB ↔ IMH HPM messages | Cross-die thermal limit propagation |
| GPIO | IMH GPIO bumps | External VR Hot / Prochot input signals |

---

## Section 3: Reset, Power, and Clocking

- Thermal DTS sensors initialize during PH1 (BIOS TPMI init); readings valid after PH6
- TCC threshold programmed by BIOS; runtime update via TPMI
- VR Hot and Prochot signals are asynchronous; PCode responds within 1 slow-loop (~1 ms)
- Thermal state persists across warm reset; cold reset re-initializes all thresholds

---

## Section 4: Programming Model

- BIOS programs TCC thresholds and thermal knobs during CPL3
- PCode slow-loop (~1 ms) polls thermal telemetry and applies throttle decisions
- OS reads thermal data via MSRs and TPMI; writes to override registers require privilege
- Test methodology: PMx `prochot_thermal` / `thermal_mgt` plugin or direct register injection

---

## Section 5: Operational Behavior

Thermal events trigger a response chain:

1. **Thermal source activates:** DIMM temperature (MR4) exceeds CLTT threshold, or DTS / VR Hot / PROCHOT asserts
2. **Collection:** Memory Controller polls MR4 periodically; IMH aggregates memory-side and local thermal events
3. **Firmware detection:** PCode / Primecode detects via polling or interrupt within 1 slow-loop (~1 ms)
4. **Policy evaluation:** Firmware compares against programmed thresholds; selects throttle action (freq reduction, BW limit)
5. **Cross-die propagation:** IMH sends thermal limit to CBB0/CBB1 via HPM; CBBs apply freq/throttle accordingly
6. **Status reporting:** Updated thermal state visible via TPMI, MSR thermal bits, PMSB telemetry
7. **Event clear:** Thermal event deasserts; firmware removes mitigation per hysteresis policy; freq ramps back autonomously

All 4 TCs in this TCD validate different aspects of this chain:
- **TC 22022421317:** DIMM CLTT threshold default values (programming correctness)
- **TC 22022421328:** Live MR4 temperature update via MC (dynamic thermal reporting)
- **TC 22022421334:** Throttle level correctness (threshold-to-action mapping)
- **TC 22022421341:** End-to-end CLTT MR4 thermal response (full chain integration)

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Thermal event clears before firmware action applied | No false persistent throttle; system exits cleanly via hysteresis |
| Multiple simultaneous thermal sources (MR4 + DTS) | Most restrictive condition wins; priority arbitration per firmware policy |
| DIMM MR4 update stale or delayed | No invalid overreaction; firmware acts on last valid data per CLTT policy |
| Event sourced on IMH vs CBB die | Throttle and reporting correctly scoped to impacted domain(s) |
| Warm reset during active thermal condition | Thermal status re-established per boot/reset policy; no stuck throttle |
| DIMM threshold not programmed by BIOS | Firmware may use fused defaults; validate threshold readback |
| All DIMMs below threshold simultaneously | No throttle; confirm negative case (MR4 reading valid, no action) |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [NWP PM MAS -- Memory Thermal](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- CLTT MR4 scope, NWP memory thermal configuration
- [DMR DDR5/MCR HAS -- MR4 CLTT](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html) -- MR4-based CLTT/memhot/memtrip for DDR5/MCR thermal management
- [Primecode Feature HAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- SoC thermal flows; MR4-based CLTT as Primecode feature area; iMH thermal management
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP memory thermal feature applicability
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) -- Cross-die thermal limit propagation via HPM

# TPF 16030767512 — [NWP PM] PEM (Power and Energy Monitoring)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030767512](https://hsdes.intel.com/appstore/article-one/#/16030767512) |
| **Title** | [NWP PM] PEM (Power and Energy Monitoring) |
| **Parent TP** | [16030767511 — [NWP PM] Telemetry (PEM/PLR)](https://hsdes.intel.com/appstore/article-one/#/16030767511) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

**PEM (Power and Energy Monitoring)** is a hardware/firmware feature that monitors, reports, and responds to power and energy excursions at the core, uncore, and package levels. PEM tracks whether the processor is running within its power envelope and exposes excursion status bits (RW0C) that indicate which limiter caused a throttling event.

**Classification**: Firmware-heavy with silicon counter support. PCode/PrimeCode evaluates SVID IMON power telemetry, applies EWMA (Exponentially Weighted Moving Average) filtering, and sets PEM status bits when a power limiter is active. Hardware provides energy/activity counters and TPMI SRAM for register exposure.

**Gating mechanism**: PEM is **always active** on NWP when Socket RAPL is enabled (which is always-on). PEM status is accessible via TPMI MMIO; no fuse or BIOS knob gates PEM independently.

**NWP scope**: PEM on NWP covers Socket RAPL PL1/PL2 and FastRAPL excursion detection. DRAM RAPL PEM is fused off. Platform RAPL/Psys PEM is ZBB. PEM status bits are per-CBB (`sv.socket0.cbb{0,1}.base.tpmi.pem_status`).

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBB count | 2 (cbb0, cbb1) | NWP topology |
| Root die | NIO (`sv.socket0.nio.punit.*`) | NWP PM MAS |
| PEM_STATUS register | RW0C semantics (write-0-to-clear) | DMR PM HAS |
| PEM excursion sources | PL1, PL2, PPL1, PPL2, PMAX, THERMAL, EXT_PROCHOT, PBM, FAST_RAPL | DMR PM HAS |
| EWMA threshold default | 0.9 | DMR PM HAS |
| PEM FAST_RAPL bit | Bit 9 | DMR PM HAS |
| PEM ANY bit | Bit 0 — OR of all other excursion bits | DMR PM HAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / Tool / BMC</strong><br/>
    <small>turbostat · BMC/NM via PECI-over-MCTP · PMT telemetry · OOB I3C/PCIe</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: BIOS / UEFI Configuration</strong><br/>
    <small>TPMI OSXML defaults · PEM threshold configuration</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PrimeCode / PCode EWMA Evaluation</strong><br/>
    <small>EWMA power filter · excursion detection · PEM_STATUS bit set/clear · consistent/inconsistent throttle classification</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: CBB PCode Telemetry Reporting</strong><br/>
    <small>PERF_STATUS accounting · HPM 0x16 LEAF_PERF_STATUS feedback · per-CBB PEM_STATUS exposure via TPMI SRAM</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / HW Telemetry</strong><br/>
    <small>SVID IMON current measurement · energy/activity counters · core power meter · VR telemetry</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L5: OS / Tool / BMC | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS + turbostat / PMT driver |
| L4: BIOS / UEFI Configuration | ✅ safe | ❌ | ❌ | ✅ | ✅ | VP is safe for BIOS negative tests |
| L3: PrimeCode / PCode EWMA Evaluation | ✅ | ✅ | ✅ | ✅ | indirect | All pre-si tiers can validate EWMA logic |
| L2: CBB PCode Telemetry Reporting | ✅ | ✅ | ✅ | ✅ | indirect | TPMI PEM_STATUS accessible from all environments |
| L1: Silicon / HW Telemetry | ❌ | ❌ | ❌ | ✅ | ✅ | Real SVID IMON requires real silicon + VR |

### PEM Excursion Detection Flow

```
SVID IMON (real-time power) ──────┐
                                   │
                                   ▼
                ┌──────────────────────────────────────┐
                │  PrimeCode NN-PID Loop (1 ms / NIO)  │
                │  ┌──────────────────────────────────┐ │
                │  │  EWMA Filter (threshold = 0.9)   │ │
                │  │  Evaluate: P_actual > PL limit?  │ │
                │  └─────────────┬────────────────────┘ │
                │                │ YES → excursion       │
                │                ▼                       │
                │  Set PEM_STATUS bit (PL1/PL2/PMAX/..)│
                │  PEM_STATUS.ANY = OR(all bits)        │
                └──────────────┬───────────────────────┘
                               │
                   ┌───────────┴───────────┐
                   ▼                       ▼
        CBB0 TPMI PEM_STATUS     CBB1 TPMI PEM_STATUS
        (sv.socket0.cbb0.base.   (sv.socket0.cbb1.base.
         tpmi.pem_status)          tpmi.pem_status)
```

### PEM_STATUS Register Bitfield

| Bit | Field | Description | Clear Semantics |
|---|---|---|---|
| 0 | ANY | OR of all excursion bits | RW0C |
| 1 | THERMAL | Thermal throttle caused excursion | RW0C |
| 2 | EXT_PROCHOT | External PROCHOT assertion | RW0C |
| 3 | PBM | Power Budget Management limit | RW0C |
| 4 | PL1 | Socket RAPL PL1 limit exceeded | RW0C |
| 5 | PL2 | Socket RAPL PL2 limit exceeded | RW0C |
| 6 | PPL1 | Platform RAPL PL1 (ZBB on NWP) | RW0C |
| 7 | PPL2 | Platform RAPL PL2 (ZBB on NWP) | RW0C |
| 8 | PMAX | PMAX hard throttle | RW0C |
| 9 | FAST_RAPL | FastRAPL sub-ms excursion | RW0C |

### Consistent vs Inconsistent Throttling

PEM distinguishes between two throttling behaviors:

- **Consistent Throttling**: Power stays above limit for sustained period; PCode applies stable frequency ceiling. PEM_STATUS bit remains set. Validated by TCD 22022421010.
- **Inconsistent Throttling**: Power transiently exceeds limit but returns below before PID converges; PEM_STATUS bit is set briefly then cleared. Validated by TCD 22022421014.

### Interface & Register Matrix

| Register / MSR | Path | Description | Tier Validated |
|---|---|---|---|
| PEM_STATUS (gen1) | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | Excursion reason bitmask (RW0C) | FV, PSS |
| PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Throttle counter + reason | FV, PSS |
| ENERGY_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status` | Energy counter | FV, PSS |
| HPM 0x16 | LEAF_PERF_STATUS | CBB→NIO PEM/PLR feedback | FV |
| IA32_THERM_STATUS | MSR 0x19C | Per-core thermal + power limit status | FV |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| PEM_STATUS bits | TPMI register | `sv.socket0.cbb0.base.tpmi.pem_status.show()` | Which excursion source is active |
| PERF_STATUS throttle counter | TPMI register | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.show()` | Throttle accounting |
| ENERGY_STATUS | TPMI register | `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status.show()` | Cumulative energy consumption |
| turbostat --show PkgWatt | OS tool | `turbostat --show PkgWatt` (PV) | Package power at OS level |
| PMT telemetry | OOB | PMT via PCIe/I3C | External power/energy reporting |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| DRAM RAPL fused off | No DRAM PEM excursion bits | All — DRAM PEM bits always 0 |
| Platform RAPL ZBB | PPL1/PPL2 PEM bits inactive | All — PPL1/PPL2 bits always 0 |
| FastRAPL supported | FAST_RAPL PEM bit 9 active | 22022421010 (consistent), 22022421014 (inconsistent) |
| Single-socket vs dual-socket | Platform-level PEM aggregation | N/A — NWP is socket-scoped only |

---

## Section 3: Validation Strategy

PEM validation requires three tiers because the feature spans firmware logic (EWMA evaluation, status bit management), silicon telemetry (SVID IMON, energy counters), and OS/tool exposure (turbostat, PMT).

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | EWMA logic, PEM_STATUS bit set/clear timing, RW0C semantics |
| PSS — HSLE | Single-die RTL | PythonSV → TPMI RTL | Within-die PEM_STATUS register behavior |
| PSS — XOS | Both-die RTL (IMH+CBB) | PythonSV → full RTL | Cross-die PEM aggregation via HPM |
| FV | Post-silicon NWP | PythonSV → namednodes | Real SVID IMON + PEM_STATUS + multi-interface readback (I3C/TPMI/PCIE) |
| PV | Post-silicon NWP + Ubuntu | turbostat / PMT | End-to-end power reporting at OS/tool level |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| PEM_STATUS bit not set on excursion | ✅ | ⚠️ | ✅ | ✅ | indirect |
| PEM_STATUS bit not cleared (RW0C broken) | ✅ | ✅ | ✅ | ✅ | ❌ |
| EWMA threshold miscalculation | ✅ | ❌ | ✅ | ✅ | indirect |
| Cross-die PEM aggregation error (HPM) | ❌ | ❌ | ✅ | ✅ | indirect |
| Consistent vs inconsistent throttle misclassification | ✅ | ❌ | ✅ | ✅ | indirect |
| PEM readback inconsistency across interfaces | ❌ | ❌ | ❌ | ✅ | ✅ |
| Silicon SVID IMON measurement error | ❌ | ❌ | ❌ | ✅ | ✅ |
| OS/PMT PEM reporting bug | ❌ | ❌ | ❌ | ❌ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| PEM PL1 excursion detection | ✅ | ✅ | indirect | PSS: timing; FV: real power |
| PEM PL2 excursion detection | ✅ | ✅ | indirect | Same |
| PEM FastRAPL excursion (bit 9) | ✅ | ✅ | ❌ | Sub-ms detection |
| Consistent throttle timing | ✅ | ✅ | indirect | EWMA convergence |
| Inconsistent throttle detection | ✅ | ✅ | indirect | Transient excursion |
| Multi-interface PEM readback | ❌ | ✅ | ✅ | I3C/TPMI/PCIe consistency |

---

## Section 5: Risks & Dependencies

### Active Risks

- **SVID IMON accuracy**: PEM excursion detection depends on accurate IMON current measurement from VR. If VR telemetry has systematic offset, PEM thresholds may under/over-report.
- **FastRAPL PEM bit timing**: FastRAPL operates at 500 µs cadence; PEM_STATUS bit 9 update latency must be validated against the fast loop.
- **Cross-die HPM transport**: PEM aggregation from CBB to NIO via HPM 0x16 — any HPM transport issue masks CBB-local PEM events.

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Real SVID IMON power measurement | FV + PV only | SVID IMON requires real silicon + VR; no pre-si equivalent |
| **G-2** | OOB PMT PEM reporting via PCIe/I3C | PV only | Requires booted OS + OOB management stack |

---

## Section 6: DFX Considerations

- **PEM_STATUS RW0C**: Write-0-to-clear semantics — debug tools reading PEM_STATUS do NOT clear bits. Only explicit 0-write clears a bit.
- **PEM telemetry via VISA**: PEM status bits can be observed via ITH T2 VISA capture on TPMI SRAM access domain.
- **Trace correlation**: PEM excursion events should correlate with RAPL NN-PID throttle commands in PrimeCode firmware trace.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| PEM PL1 + PL2 simultaneous excursion | 22022421010, 22022421014 | Both PL1 and PL2 PEM bits set; ANY bit set |
| PEM + PMAX concurrent throttle | 22022421010 | PEM PL1/PL2 + PMAX bits all set; PMAX ceiling takes priority |
| PEM bit set but load removed | 22022421014 | Inconsistent throttle: bit self-clears when power drops below limit |
| FastRAPL PEM bit during PL1 throttle | 22022421010, 22022421014 | Both FAST_RAPL (bit 9) and PL1 (bit 4) set if both limiters active |
| PEM status clear-on-write race | 22022421010 | Concurrent FW write + SW clear: SW clear should not lose FW-set bit |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Owner | TC Count |
|---|---|---|---|
| [22022421010](https://hsdes.intel.com/appstore/article-one/#/22022421010) | Consistent Throttling | akurathi | 4 |
| [22022421012](https://hsdes.intel.com/appstore/article-one/#/22022421012) | Correlating Timings | akurathi | 4 |
| [22022421014](https://hsdes.intel.com/appstore/article-one/#/22022421014) | Inconsistent Throttling | akurathi | 4 |

### References

- [DMR PM HAS — PEM Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html) — PEM_STATUS bitfield, EWMA algorithm, excursion sources
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PEM applicability and scope
- [DMR RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — RAPL control loop that drives PEM events
- [TCD 16031169448 — Socket RAPL Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) — PEM/PLR reporting semantics in RAPL context
- [TCD 22022420794 — Fast RAPL](https://hsdes.intel.com/appstore/article-one/#/22022420794) — FastRAPL sub-ms PEM excursion

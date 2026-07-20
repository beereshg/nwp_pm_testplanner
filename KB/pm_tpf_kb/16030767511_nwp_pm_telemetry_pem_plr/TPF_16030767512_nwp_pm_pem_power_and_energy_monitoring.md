# TPF 16030767512 — [NWP PM] PEM (Power and Energy Monitoring)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030767512](https://hsdes.intel.com/appstore/article-one/#/16030767512) |
| **Title** | [NWP PM] PEM (Power and Energy Monitoring) |
| **Parent TP** | [16030767511 — [NWP PM] Telemetry (PEM/PLR)](https://hsdes.intel.com/appstore/article-one/#/16030767511) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-20 |

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
| PEM excursion sources (gen3) | ANY, FCT, PCS_TRL, MTPMAX, FAST_RAPL, PKG_PL1_{INBAND/CSR/OOB}, PKG_PL2_{INBAND/CSR/OOB}, PLATFORM_PL1_{INBAND/CSR/OOB}, PLATFORM_PL2_{INBAND/CSR/OOB}, RACL, PER_CORE_THERMAL, ICCMAX, XXPROCHOT, HOT_VR, PCS_PSTATE_NOT_SUPPORTED, RAS | PM HAS gen3 PEM §PEM_STATUS |
| EWMA threshold default | 0.9 | PM HAS §EWMA Algorithm |
| PEM_CONTROL bitfield | FET [7:0], TW [14:8], VERSION [23:16] (RO), ENABLE_PEM [31] | PM HAS §PEM_CONTROL |
| TW formula | Actual window ≈ 2.3 × 2^TW ms; valid range 0–17 (max ≈ 302 s) | PM HAS §EWMA Algorithm |
| PEM slowloop cadence | ~1 ms (per PCode slowloop) | PM HAS §Execution Flow |
| NWP scope exclusions | DRAM RAPL PEM = fused off; Platform RAPL PEM = ZBB | NWP PM MAS |

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

**EWMA Algorithm (formal):**
```
For each PEM event r, every ~1 ms (PCode slowloop):
  set_status[r] = 1  if core frequency < FET for reason r, else 0
  EWMA_n[r] = α × set_status[r] + (1 − α) × EWMA_{n-1}[r]
  where α is derived from TW: actual window ≈ 2.3 × 2^TW ms

  If EWMA_n[r] > 0.9  →  PEM_STATUS[r] = 1; PEM_COUNTER[r]++
  PEM_STATUS[r] stays set until SW writes 0 to clear (RW0C)
  EWMA continues evaluating regardless of PEM_STATUS — re-assertion without restart
```

```
SVID IMON (real-time power) ──────┐
                                   │
                                   ▼
                ┌──────────────────────────────────────┐
                │  PrimeCode NN-PID Loop (1 ms / NIO)  │
                │  ┌──────────────────────────────────┐ │
                │  │  EWMA Filter per event r         │ │
                │  │  α from TW; threshold = 0.9      │ │
                │  │  EWMA_n = α×status + (1-α)×prev  │ │
                │  │  If EWMA > 0.9 → excursion       │ │
                │  └─────────────┬────────────────────┘ │
                │                │ YES → set PEM bit    │
                │                ▼                       │
                │  PEM_STATUS[r] = 1 (RW0C)            │
                │  PEM_COUNTER[r]++ (1 ms/count)       │
                │  PEM_STATUS.ANY = OR(all bits)        │
                └──────────────┬───────────────────────┘
                               │
                   ┌───────────┴───────────┐
                   ▼                       ▼
        CBB0 TPMI PEM_STATUS     CBB1 TPMI PEM_STATUS
        (sv.socket0.cbb0.base.   (sv.socket0.cbb1.base.
         tpmi.pem_status)          tpmi.pem_status)
```

### PEM_STATUS Register Bitfield (gen3 — DMR/NWP)

| Bit | Field | Description | Clear Semantics | NWP Applicability |
|---|---|---|---|---|
| 0 | ANY | OR of all excursion bits (listed + unlisted) | RW0C | ✅ Active |
| 6 | FCT | Frequency limited due to FCT | RW0C | ✅ Active |
| 7 | PCS_TRL | OOB Turbo Ratio Limit override limiting frequency | RW0C | ✅ Active |
| 8 | MTPMAX | Frequency limited due to Pmax.app (SIMPL/DFC) limit | RW0C | ✅ Active |
| 9 | FAST_RAPL | Frequency limited due to Fast RAPL firing | RW0C | ✅ Active (if FastRAPL supported) |
| 10 | PKG_PL1_INBAND | Socket RAPL PL1 excursion — OS/SW interface | RW0C | ✅ Active |
| 11 | PKG_PL1_CSR | Socket RAPL PL1 excursion — BIOS CSR interface | RW0C | ✅ Active |
| 12 | PKG_PL1_OOB | Socket RAPL PL1 excursion — OOB SW interface | RW0C | ✅ Active |
| 13 | PKG_PL2_INBAND | Socket RAPL PL2 excursion — OS/SW interface | RW0C | ✅ Active |
| 14 | PKG_PL2_CSR | Socket RAPL PL2 excursion — BIOS CSR interface | RW0C | ✅ Active |
| 15 | PKG_PL2_OOB | Socket RAPL PL2 excursion — OOB SW interface | RW0C | ✅ Active |
| 16 | PLATFORM_PL1_INBAND | Platform RAPL PL1 excursion — OS/SW | RW0C | ❌ ZBB on NWP |
| 17 | PLATFORM_PL1_CSR | Platform RAPL PL1 excursion — BIOS | RW0C | ❌ ZBB on NWP |
| 18 | PLATFORM_PL1_OOB | Platform RAPL PL1 excursion — OOB | RW0C | ❌ ZBB on NWP |
| 19 | PLATFORM_PL2_INBAND | Platform RAPL PL2 excursion — OS/SW | RW0C | ❌ ZBB on NWP |
| 20 | PLATFORM_PL2_CSR | Platform RAPL PL2 excursion — BIOS | RW0C | ❌ ZBB on NWP |
| 21 | PLATFORM_PL2_OOB | Platform RAPL PL2 excursion — OOB | RW0C | ❌ ZBB on NWP |
| 22 | RACL | Frequency limited due to RACL condition | RW0C | ✅ Active |
| 23 | PER_CORE_THERMAL | Thermal throttling — core temp exceeds threshold | RW0C | ✅ Active |
| 24 | ICCMAX | Dynamic Frequency Capping (DFC/SIMPL) | RW0C | ✅ Active |
| 25 | XXPROCHOT | Platform PROCHOT# input pin triggered | RW0C | ✅ Active |
| 26 | HOT_VR | VR_HOT# input pin triggered | RW0C | ✅ Active |
| 29 | PCS_PSTATE_NOT_SUPPORTED | OOB Pstate override (not supported) | RW0C | TBD |
| 30 | RAS | Frequency limited due to RAS limit | RW0C | ✅ Active |

### Consistent vs Inconsistent Throttling

PEM distinguishes between two throttling behaviors:

- **Consistent Throttling**: Power stays above limit for sustained period; PCode applies stable frequency ceiling. PEM_STATUS bit remains set. Validated by TCD 22022421010.
- **Inconsistent Throttling**: Power transiently exceeds limit but returns below before PID converges; PEM_STATUS bit is set briefly then cleared. Validated by TCD 22022421014.

### Interface & Register Matrix

| Register / MSR | Path | Fields | Description | Tier Validated |
|---|---|---|---|---|
| PEM_CONTROL | `sv.socket0.cbb{0,1}.base.tpmi.pem_control` | FET [7:0], TW [14:8], VERSION [23:16] (RO), ENABLE_PEM [31] | Enable PEM, set excursion threshold and time window | FV, PSS |
| PEM_STATUS (gen3) | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | 20+ bits per excursion source (RW0C) — see bitfield table above | Excursion reason bitmask | FV, PSS |
| PEM_COUNTER | Via PMT GUID readout / TPMI | 32-bit per event, RO, 1 ms/count | Duration counter — increments only while EWMA > threshold | FV, PSS |
| PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Throttle counter + reason | Throttle accounting (RAPL-driven) | FV, PSS |
| ENERGY_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.energy_status` | Energy counter (RO) | Cumulative energy consumption | FV, PSS |
| HPM 0x16 | LEAF_PERF_STATUS | CBB→NIO feedback | CBB PEM/PLR telemetry feedback to NIO | FV |
| IA32_THERM_STATUS | MSR 0x19C | Per-core thermal + power limit status | Per-core thermal reporting | FV |

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
| Platform RAPL ZBB | PPL1/PPL2 PEM bits (16–21) inactive | All — PLATFORM_PL{1,2}_{INBAND/CSR/OOB} always 0 |
| FastRAPL supported | FAST_RAPL PEM bit 9 active | 22022421010, 22022421014 |
| Single-socket vs dual-socket | Platform-level PEM aggregation | N/A — NWP is socket-scoped only |
| PL1 interface variant (INBAND vs CSR vs OOB) | PEM tracks PL1 excursion per-interface (bits 10/11/12) | 22022421010, 22022421012 |
| PL2 interface variant (INBAND vs CSR vs OOB) | PEM tracks PL2 excursion per-interface (bits 13/14/15) | 22022421010, 22022421012 |
| ICCMAX / DFC / SIMPL active | ICCMAX PEM bit 24 active when DFC throttles frequency | 22022421010 |
| XXPROCHOT / HOT_VR external assertion | Bits 25/26 — platform pin-driven | 22022421010 |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| PrimeCode NIO PID / EWMA | `source/pcode/flows/rapl/` — PEM excursion evaluation in NN-PID loop |
| PrimeCode CBB PERF_STATUS | `source/pcode/flows/rapl/` — CBB telemetry reporting, HPM 0x16 |
| BIOS / OSXML | PEM_CONTROL defaults via TPMI OSXML template |
| OS / turbostat / PMT | Intel PMT driver + turbostat (out-of-tree) |

### Microarch→Scenario Coverage Matrix

| # | Element (from §2) | Category | Implied WHAT | Realized as TCD | TC(s) | Tier | Status |
|---|---|---|---|---|---|---|---|
| 1 | EWMA avg > 0.9 → PEM_STATUS[r] = 1 (sustained) | FSM transition | Sustained excursion correctly detected and reported | 22022421010 | 22022422343, 22022422346, 22022422348, 22022422351 | FV, PSS | ✓ |
| 2 | EWMA avg < 0.9 → PEM_STATUS stays 0 (transient rejection) | FSM transition | Transient excursion correctly filtered by EWMA | 22022421014 | 22022422363, 22022422372, 22022422374, 22022422377 | FV, PSS | ✓ |
| 3 | PEM_COUNTER increment rate = 1 ms/count ±10% | Counter accuracy | Counter tracks real throttle duration accurately | 22022421012 | 22022422353, 22022422356, 22022422358, 22022422361 | FV, PSS | ✓ |
| 4 | PEM_STATUS RW0C semantics (W0C clears, W1 no effect) | Register field (RW0C) | SW clear does not lose FW-set bit; EWMA continues after clear | 22022421010 | 22022422348 | FV, PSS | ✓ |
| 5 | PEM_COUNTER monotonicity during active excursion | Counter | Counter never decrements while excursion is active | 22022421012 | 22022422358 | FV, PSS | ✓ |
| 6 | PKG_PL1 per-interface bits (INBAND/CSR/OOB — bits 10/11/12) | Register field (RW) | Correct bit set depending on which interface set PL1 | GAP | — | FV | ⚠️ GAP |
| 7 | PKG_PL2 per-interface bits (INBAND/CSR/OOB — bits 13/14/15) | Register field (RW) | Correct bit set depending on which interface set PL2 | GAP | — | FV | ⚠️ GAP |
| 8 | Cross-die PEM aggregation (HPM 0x16 CBB→NIO) | Cross-die interface | CBB-local PEM events propagated to NIO correctly | GAP | — | FV, XOS | ⚠️ GAP |
| 9 | PEM_COUNTER wraparound at 2^32 (~49 days) | Counter rollover | Counter wraps without hang; SW detects wraparound | GAP | — | Simics | ⚠️ GAP |
| 10 | ICCMAX/DFC PEM bit 24 — excursion on DFC throttle | Register field (RW) | PEM_STATUS[ICCMAX] set when DFC caps frequency | GAP | — | FV | ⚠️ GAP |
| 11 | XXPROCHOT PEM bit 25 — platform pin assertion | Layer interface (platform → PCode) | PEM_STATUS[XXPROCHOT] set on PROCHOT# assertion | GAP | — | FV | ⚠️ GAP |
| 12 | HOT_VR PEM bit 26 — VR thermal event | Layer interface (VR → PCode) | PEM_STATUS[HOT_VR] set on VR_HOT# assertion | GAP | — | FV | ⚠️ GAP |
| 13 | PER_CORE_THERMAL PEM bit 23 — thermal throttle | Layer interface (thermal → PCode) | PEM_STATUS[PER_CORE_THERMAL] set on core thermal event | GAP | — | FV | ⚠️ GAP |
| 14 | FCT PEM bit 6 — FCT-driven excursion | Register field (RW) | PEM_STATUS[FCT] set when FCT limits frequency | GAP | — | FV, PSS | ⚠️ GAP |
| 15 | RACL PEM bit 22 — RACL condition | Register field (RW) | PEM_STATUS[RACL] set on RACL-driven throttle | GAP | — | FV | ⚠️ GAP |
| 16 | RAS PEM bit 30 — RAS frequency limit | Register field (RW) | PEM_STATUS[RAS] set on RAS-driven throttle | GAP | — | FV | ⚠️ GAP |
| 17 | FAST_RAPL PEM bit 9 — sub-ms excursion | Register field (RW) | PEM_STATUS[FAST_RAPL] set during fast-loop excursion | 22022421010 | 22022422351 | FV, PSS | ⚠️ PARTIAL — only validated as concurrent with sustained throttle |
| 18 | PEM_CONTROL FET boundary — FET at Pm (min) | Register boundary | FET at minimum ratio: all throttle events flagged | GAP | — | FV, PSS | ⚠️ GAP |
| 19 | PEM_CONTROL FET boundary — FET at P01 (max) | Register boundary | FET at maximum ratio: only severe throttle flagged | GAP | — | FV, PSS | ⚠️ GAP |
| 20 | PEM_CONTROL TW boundary — TW=0 (min, fastest) | Register boundary | Minimum TW: excursions detected with minimal smoothing | GAP | — | FV, PSS | ⚠️ GAP |
| 21 | PEM_CONTROL TW boundary — TW=17 (max, ~302s) | Register boundary | Maximum TW: only very sustained excursions detected | GAP | — | PSS (VP) | ⚠️ GAP |
| 22 | Multi-interface PEM readback consistency (I3C/PCIe/TPMI) | Layer interface | Same counter value ±1 across all interfaces | 22022421010, 22022421012 | 22022422343, 22022422346, 22022422348, 22022422353, 22022422356, 22022422358 | FV | ✓ |
| 23 | PEM enable/disable cycle — state preservation | BIOS knob | PEM_STATUS/COUNTER preserved across disable → re-enable | GAP | — | FV, PSS | ⚠️ GAP |

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
| PL1 + PL2 simultaneous excursion | 22022421010, 22022421014 | Both PKG_PL1_* and PKG_PL2_* PEM bits set; ANY bit set |
| PEM + PMAX concurrent throttle | 22022421010 | PEM PL1/PL2 + MTPMAX (bit 8) bits all set; PMAX ceiling takes priority |
| PEM bit set but load removed | 22022421014 | Inconsistent throttle: bit self-clears when power drops below limit |
| FastRAPL PEM bit during PL1 throttle | 22022421010, 22022421014 | Both FAST_RAPL (bit 9) and PKG_PL1_INBAND (bit 10) set if both limiters active |
| PEM status clear-on-write race | 22022421010 | Concurrent FW write + SW clear: SW clear should not lose FW-set bit |
| PKG_PL1 INBAND vs CSR vs OOB — distinct bits | 22022421010, 22022421012 | Only the interface that set the PL1 limit shows as excursion source (bit 10, 11, or 12) |
| XXPROCHOT + THERMAL concurrent assertion | 22022421010 | Both PER_CORE_THERMAL (bit 23) and XXPROCHOT (bit 25) set independently |
| PEM_COUNTER wraparound | 22022421012 | Counter wraps at 2^32 ms (~49 days); SW must detect and handle |
| PEM enable/disable cycle | All | PEM_STATUS and PEM_COUNTER preserved across disable → re-enable; cold reset clears |
| ICCMAX + PL1 concurrent throttle | 22022421010 | Both ICCMAX (bit 24) and PKG_PL1 set; independent excursion tracking |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Owner | TC Count |
|---|---|---|---|
| [22022421010](https://hsdes.intel.com/appstore/article-one/#/22022421010) | Consistent Throttling | akurathi | 4 |
| [22022421012](https://hsdes.intel.com/appstore/article-one/#/22022421012) | Correlating Timings | akurathi | 4 |
| [22022421014](https://hsdes.intel.com/appstore/article-one/#/22022421014) | Inconsistent Throttling | akurathi | 4 |

### References

- [PM HAS gen3 — PEM Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html) — PEM_STATUS gen3 bitfield (20+ bits), EWMA algorithm, PEM_CONTROL fields, FET/TW semantics
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PEM applicability and scope; DRAM fused off, Platform ZBB
- [DMR RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — RAPL control loop that drives PEM events
- [TCD 16031169448 — Socket RAPL Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) — PEM/PLR reporting semantics in RAPL context
- [TCD 22022420794 — Fast RAPL](https://hsdes.intel.com/appstore/article-one/#/22022420794) — FastRAPL sub-ms PEM excursion
- Co-Design Specs MCP query (2026-07-20) — Authoritative gen3 PEM_STATUS bitfield, EWMA formula, PEM_CONTROL register fields

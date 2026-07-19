# TPF 16030767513 — [NWP PM] PLR (Performance Limit Reasons)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030767513](https://hsdes.intel.com/appstore/article-one/#/16030767513) |
| **Title** | [NWP PM] PLR (Performance Limit Reasons) |
| **Parent TP** | [16030767511 — [NWP PM] Telemetry (PEM/PLR)](https://hsdes.intel.com/appstore/article-one/#/16030767511) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

**PLR (Performance Limit Reasons)** provides a software-readable log of the reasons why core or uncore frequency is currently limited (throttled). When a core runs below its maximum turbo frequency, PLR flags the responsible constraint — RAPL, thermal, electrical/ICCMAX, platform PROCHOT, QoS, or RAS — enabling debug, validation, and platform power optimization.

**Classification**: Firmware-heavy feature with silicon register support. PCode/PrimeCode evaluates each active limiter during the PID loop iteration, sets the corresponding PLR reason bits, and exposes them via TPMI registers and architectural MSRs. Hardware provides the register infrastructure (TPMI SRAM, MSR ports).

**Gating mechanism**: PLR is **always active** on NWP — no fuse or BIOS knob gates PLR reporting. PLR bits are updated every PID loop iteration (~1 ms for standard RAPL, ~500 µs for FastRAPL).

**NWP scope**: PLR on NWP supports both **die-level** (PLR_DIE_LEVEL) and **module-level** (PLR_MAILBOX_DATA) granularity. Die-level aggregates all limit reasons for the entire die. Module-level provides per-core-cluster detail via mailbox access. PLR is readable via TPMI, MSR 0x19C, and PECI.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBB count | 2 (cbb0, cbb1) | NWP topology |
| PLR_DIE_LEVEL register width | 64-bit (coarse bits 0–9, fine bits 32–63) | DMR PM HAS |
| PLR update cadence | ~1 ms (PID slow loop) / ~500 µs (FastRAPL) | DMR PM HAS |
| PLR priority (1-hot) | PlatPL2 > PlatPL1 > FastRAPL > SktPL2 > SktPL1 | DMR RAPL HAS |
| Per-core MSR | IA32_THERM_STATUS (0x19C) | Intel SDM |
| TPMI PLR path | `sv.socket0.cbb{0,1}.base.tpmi.perf_limit_reasons` | NWP PM MAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / Tool / BMC</strong><br/>
    <small>turbostat · perf · BMC/NM via PECI · TPMI sysfs · OOB I3C</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: BIOS / UEFI Configuration</strong><br/>
    <small>Power limit configuration that drives PLR — no direct PLR BIOS knob</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PrimeCode / PCode Limiter Evaluation</strong><br/>
    <small>NN-PID loop → identify active limiter → set PLR reason bits → 1-hot priority resolution</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: CBB PCode PLR Register Update</strong><br/>
    <small>PLR_DIE_LEVEL coarse/fine bits · PLR_MAILBOX_DATA per-module · PERF_STATUS reason fields</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / HW Register Infrastructure</strong><br/>
    <small>TPMI SRAM for PLR registers · MSR 0x19C per-core port · HPM 0x16 transport</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L5: OS / Tool / BMC | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS + turbostat / perf |
| L4: BIOS / UEFI Configuration | ✅ safe | ❌ | ❌ | ✅ | ✅ | PLR reflects BIOS power limit config |
| L3: PrimeCode / PCode Limiter Evaluation | ✅ | ✅ | ✅ | ✅ | indirect | All tiers validate limiter→PLR bit mapping |
| L2: CBB PCode PLR Register Update | ✅ | ✅ | ✅ | ✅ | indirect | TPMI PLR register accessible from all environments |
| L1: Silicon / HW Register Infrastructure | ❌ | ❌ | ❌ | ✅ | ✅ | Real silicon MSR path + TPMI SRAM |

### PLR Architecture

```
Active Limiters (PCode / PrimeCode PID loop)
┌──────────────────────────────────────────────────┐
│  RAPL PL1 ────────────> POWER bit (2)            │
│  RAPL PL2 ────────────> POWER bit (2)            │
│  FastRAPL ────────────> (fine-grain FastRAPL bit) │
│  Thermal (Tj) ────────> THERMAL bit (3)          │
│  ICCMAX / Pmax ───────> CURRENT bit (1)          │
│  PROCHOT/VRHOT ───────> PLATFORM bit (4)         │
│  MCP (external die) ──> MCP bit (5)              │
│  RAS ─────────────────> RAS bit (6)              │
│  OOB SW (BMC) ────────> MISC bit (7)             │
└──────────────────┬───────────────────────────────┘
                   │ sets reason bits in
                   ▼
┌──────────────────────────────────────────────────┐
│  PLR_DIE_LEVEL (TPMI, 64-bit)                    │
│  Coarse (bits 0–9): FREQUENCY, CURRENT, POWER,  │
│    THERMAL, PLATFORM, MCP, RAS, MISC, QOS        │
│  Fine (bits 32–63): PL1, PL2, PPL1, PPL2,       │
│    FastRAPL, SST-CP, etc.                        │
│                                                   │
│  PLR_MAILBOX_DATA (per-module detail)            │
└──────────────────┬───────────────────────────────┘
                   │ also visible via
                   ▼
┌──────────────────────────────────────────────────┐
│  MSR 0x19C — IA32_THERM_STATUS (per-core)        │
│  Bit 11: POWER_LIMITATION_STATUS                 │
│  Bit 12: CURRENT_LIMIT_STATUS                    │
│  Bit 14: CROSS_DOMAIN_LIMIT_STATUS               │
│                                                   │
│  TPMI PERF_STATUS fine/coarse throttle reason    │
└──────────────────────────────────────────────────┘
```

### PLR Coarse-Grain Bitfield (PLR_DIE_LEVEL bits 0–9)

| Bit | Field | Description |
|---|---|---|
| 0 | FREQUENCY | Limited by Cdyn level or FCT |
| 1 | CURRENT | Limited by Pmax or Iccmax (RACL) |
| 2 | POWER | Limited by Socket/Platform RAPL or SST-CP |
| 3 | THERMAL | Limited by in-die thermal conditions |
| 4 | PLATFORM | Limited by XXPROCHOT or VRHOT |
| 5 | MCP | External die-based feedback |
| 6 | RAS | Limited by RAS |
| 7 | MISC | Out-of-band SW (e.g., BMC) |
| 8 | QOS | Quality of Service (reserved on NWP) |
| 9 | Reserved | — |

### PLR Fine-Grain Bitfield (PLR_DIE_LEVEL bits 32–63)

| Bit | Field | Description |
|---|---|---|
| 32 | PL1 | Socket RAPL PL1 is active limiter |
| 33 | PL2 | Socket RAPL PL2 is active limiter |
| 34 | PPL1 | Platform RAPL PL1 (ZBB on NWP) |
| 35 | PPL2 | Platform RAPL PL2 (ZBB on NWP) |
| 36 | FAST_RAPL | FastRAPL 500 µs loop is active limiter |
| 37 | SST_CP | SST-CP limit |
| 38+ | Reserved | — |

### Interface & Register Matrix

| Register / MSR | Path | Description | Tier Validated |
|---|---|---|---|
| PLR_DIE_LEVEL | `sv.socket0.cbb{0,1}.base.tpmi.perf_limit_reasons` | Die-level coarse+fine PLR | FV, PSS |
| PLR_MAILBOX_DATA | Via PCode mailbox | Per-module PLR detail | FV, PSS |
| IA32_THERM_STATUS | MSR 0x19C | Per-core power/current/cross-domain limit bits | FV |
| IA32_PERF_STATUS | MSR 0x198 | Current operating ratio (compare to max for throttle) | FV |
| PERF_STATUS (TPMI) | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | RAPL throttle reason fine/coarse | FV, PSS |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| PLR_DIE_LEVEL | TPMI register | `sv.socket0.cbb0.base.tpmi.perf_limit_reasons.show()` | Coarse + fine throttle reasons |
| MSR 0x19C per-core | MSR | `pd.debug.access_to_msr(0x19C, core=N)` | Per-core limit status bits |
| PERF_STATUS | TPMI register | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status.show()` | RAPL throttle reason + counter |
| turbostat PLR | OS tool | `turbostat` (PV) | Freq limitation reasons at OS level |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| Platform RAPL ZBB | PPL1/PPL2 fine-grain PLR bits (34,35) inactive | 22022421017 — those bits always 0 |
| SST-CP supported | SST_CP PLR fine-grain bit (37) may be active | 22022421017 — if SST-CP is enabled |
| FastRAPL supported | FAST_RAPL PLR fine-grain bit (36) active | 22022421017 — 500 µs limiter visible |
| NWP 2-CBB topology | PLR_DIE_LEVEL is per-CBB; read both cbb0 and cbb1 | 22022421017 — iterate both CBBs |

---

## Section 3: Validation Strategy

PLR validation requires multiple tiers because PLR accuracy depends on the correct identification of the active limiter (firmware logic) and correct register exposure (silicon infrastructure). The priority ordering (PlatPL2 > PlatPL1 > FastRAPL > SktPL2 > SktPL1) must be validated under real power conditions.

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | PLR bit set/clear logic, priority ordering, mailbox access |
| PSS — HSLE | Single-die RTL | PythonSV → TPMI RTL | Within-die PLR register behavior |
| PSS — XOS | Both-die RTL (IMH+CBB) | PythonSV → full RTL | Cross-die PLR aggregation, HPM PLR transport |
| FV | Post-silicon NWP | PythonSV → namednodes | Real limiter→PLR mapping, all interfaces, priority under load |
| PV | Post-silicon NWP + Ubuntu | turbostat / perf | OS-visible PLR reporting |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| Wrong PLR reason bit set for limiter | ✅ | ⚠️ | ✅ | ✅ | indirect |
| PLR priority ordering wrong | ✅ | ❌ | ✅ | ✅ | indirect |
| PLR bit not cleared when limiter removed | ✅ | ✅ | ✅ | ✅ | ❌ |
| PLR_MAILBOX_DATA per-module mismatch | ✅ | ❌ | ✅ | ✅ | ❌ |
| MSR 0x19C vs TPMI PLR inconsistency | ❌ | ❌ | ❌ | ✅ | ✅ |
| Cross-die PLR aggregation error | ❌ | ❌ | ✅ | ✅ | indirect |
| PLR fine-grain vs coarse-grain mismatch | ✅ | ❌ | ✅ | ✅ | indirect |
| OS PLR reporting bug (turbostat) | ❌ | ❌ | ❌ | ❌ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| Single limiter → correct PLR bit | ✅ | ✅ | indirect | Baseline correctness |
| Multiple simultaneous limiters | ✅ | ✅ | indirect | Priority ordering |
| PLR transition (limiter added/removed) | ✅ | ✅ | indirect | Timing accuracy |
| Per-module PLR via mailbox | ✅ | ✅ | ❌ | Module-level granularity |
| Cross-interface PLR consistency | ❌ | ✅ | ✅ | MSR vs TPMI vs PECI |

---

## Section 5: Risks & Dependencies

### Active Risks

- **PLR priority ordering under FastRAPL**: FastRAPL operates at 500 µs; PLR priority when FastRAPL + SktPL1 both active needs explicit validation.
- **PLR transition accuracy**: PLR reason bits must update within one PID iteration when limiter state changes. Stale bits cause incorrect debug conclusions.
- **PEM ↔ PLR correlation**: PEM excursion events (TPF 16030767512) should correlate with PLR reason bits. A PEM PL1 excursion without PLR POWER bit set is a reporting gap.

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Per-core MSR 0x19C PLR readback | FV + PV only | MSR port requires real silicon |
| **G-2** | PECI PLR readback | PV only | PECI requires booted OS + BMC |

---

## Section 6: DFX Considerations

- **PLR sticky LOG bits**: MSR 0x19C has sticky LOG bits (e.g., bit 11 LOG) that persist until SW clears via 0-write. Debug tools should distinguish between transient STATUS and sticky LOG.
- **PLR mailbox access**: Module-level PLR (PLR_MAILBOX_DATA) uses PCode mailbox. Mailbox race conditions between FW and validation reads must be avoided.
- **PLR via VISA**: PLR register updates can be observed via ITH T2 VISA on TPMI SRAM domain.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| RAPL PL1 + PL2 both active | 22022421017 | Both POWER coarse + PL1 fine + PL2 fine bits set |
| Thermal + RAPL simultaneous | 22022421017 | Both THERMAL and POWER coarse bits set |
| FastRAPL active alone | 22022421017 | POWER coarse + FAST_RAPL fine bit set |
| All limiters removed | 22022421017 | All PLR bits clear within next PID iteration |
| PLR read during PID update | 22022421017 | No torn reads — 64-bit atomicity on TPMI path |
| PLR per-module: different limiters per module | 22022421017 | PLR_MAILBOX_DATA shows different bits per module; DIE_LEVEL is OR |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Owner | TC Count |
|---|---|---|---|
| [22022421017](https://hsdes.intel.com/appstore/article-one/#/22022421017) | Performance Limit Reason | mps | 1 |

### References

- [DMR PM HAS — PLR Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) — PLR coarse/fine bitfield definitions
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PLR applicability
- [Intel SDM — IA32_THERM_STATUS](https://www.intel.com/sdm) — MSR 0x19C power/current/cross-domain limit bits
- [TCD 16031169448 — Socket RAPL Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) — PLR priority ordering and reporting semantics in RAPL context
- [TCD 22022421017 — Performance Limit Reason](https://hsdes.intel.com/appstore/article-one/#/22022421017) — PLR verification TCD
- [TPF 16030767512 — PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512) — PEM excursion events that correlate with PLR reason bits

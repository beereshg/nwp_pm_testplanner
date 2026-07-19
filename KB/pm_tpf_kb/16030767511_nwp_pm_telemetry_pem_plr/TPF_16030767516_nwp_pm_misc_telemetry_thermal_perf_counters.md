# TPF 16030767516 — [NWP PM] Misc Telemetry (Thermal, Perf Counters)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030767516](https://hsdes.intel.com/appstore/article-one/#/16030767516) |
| **Title** | [NWP PM] Misc Telemetry (Thermal, Perf Counters) |
| **Parent TP** | [16030767511 — [NWP PM] Telemetry (PEM/PLR)](https://hsdes.intel.com/appstore/article-one/#/16030767511) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

**Misc Telemetry** is a catch-all TPF covering telemetry features related to power management that are not PEM (excursion monitoring) or PLR (limit reason reporting). This includes **thermal telemetry** (DTS sensor readback, package thermal reporting, thermal threshold interrupts) and **PM performance counters** (PMon/PMON counters for power management events, C-state residency accounting, ring scalability counters).

**Classification**: Silicon-heavy (DTS sensors, thermal diodes, hardware counters) with firmware reporting (PCode thermal telemetry aggregation, PMON configuration, counter readback via TPMI/MSR).

**Gating mechanism**: Thermal telemetry (DTS) is **always active** — no fuse or BIOS knob gates DTS sensors. PM performance counters (PMON) are individually enabled/disabled via programming model registers.

**NWP scope**: NWP inherits DMR thermal sensor topology with NWP-specific delta: additional MR4-related telemetry pulls, expanded RC telemetry indexing, and NIO PM telemetry updates for Newport. PMON counters are present on both CBB and NIO/IMH dies.

> **Note**: This TPF currently has **0 TCDs / 0 TCs**. Content is defined to scope future TCD creation as the test plan matures.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBB DTS: always-on DTS | 1 per CBB (in CGU) | DMR PM HAS |
| CBB DTS: core DTS | 2 per DCM module (1 per core) | DMR PM HAS |
| CBB DTS: cluster DTS | Variable per compute cluster | DMR PM HAS |
| NIO DTS count | DTS per IMH subunit | NWP PM MAS |
| THERMTRIP_N | Catastrophic thermal shutdown | DMR PM HAS |
| PROCHOT_N | Programmable thermal throttle threshold | DMR PM HAS |
| TT1/TT2 thresholds | Customer-programmable offsets below Tprochot | Intel SDM |
| PMON counter width | 48-bit (typical) | DMR PM HAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / Tool / BMC</strong><br/>
    <small>lm-sensors · turbostat · perf · BMC/NM PECI thermal reads · PMT OOB</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: BIOS / UEFI Configuration</strong><br/>
    <small>DTS threshold programming · PMON enable/config · Thermal interrupt config</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PCode Thermal Aggregation + PMON Management</strong><br/>
    <small>DTS sampling · EWMA thermal filtering · min/max reporting · PMON start/stop/overflow</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: PMA / PMSB Telemetry Transport</strong><br/>
    <small>Core PMA push telemetry · short telemetry messages · GPSB telemetry path</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / HW Sensors + Counters</strong><br/>
    <small>DTS diodes · always-on DTS (CGU) · thermal daisy chain · THERMTRIP_N · HW PMON counters</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L5: OS / Tool / BMC | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS + thermal tools |
| L4: BIOS / UEFI Configuration | ✅ safe | ❌ | ❌ | ✅ | ✅ | BIOS thermal threshold programming |
| L3: PCode Thermal Aggregation + PMON | ✅ | ✅ | ✅ | ✅ | indirect | FW logic validated across all tiers |
| L2: PMA / PMSB Telemetry Transport | ❌ | ✅ | ✅ | ✅ | indirect | RTL or real silicon for PMA transport |
| L1: Silicon / HW Sensors + Counters | ❌ | ❌ | ❌ | ✅ | ✅ | Real DTS sensors require real silicon |

### Thermal Telemetry Architecture

```
DTS Sensors (per core, per module, always-on)
   │
   ▼ (analog → digital conversion)
Core PMA Push Telemetry (short telemetry messages)
   │
   ▼
PCode Thermal Aggregation (CBB / NIO)
   ├── min/max per CCP domain
   ├── EWMA filtering
   ├── Thermal monitor status computation
   └── SOCKET_THERMAL HPM message → Primecode (package-level)
   │
   ▼
Reporting Interfaces
   ├── MSR 0x19C (IA32_THERM_STATUS) — per-core thermal status
   ├── MSR 0x1B1 (IA32_PACKAGE_THERM_STATUS) — package thermal
   ├── MSR 0x1A2 (MSR_TEMPERATURE_TARGET) — Tjmax / TCC offset
   ├── MSR 0x1A3/0x1A4 (MCP_THERMAL_REPORT_1/2) — PMT mirror
   ├── TPMI thermal status registers
   └── PECI GetTemp / RdPkgConfig — OOB thermal reads
```

### PM Performance Counters (PMON) Architecture

```
Hardware Events (core idle, ring BW, C-state transitions, etc.)
   │
   ▼
PMON Counter HW (48-bit per counter, per unit)
   ├── CBB: CBO/SBO/Ring counters (ring BW, distress, LLC)
   ├── CBB: PMX counters (C-state residency, telemetry)
   ├── NIO: uncore PMON (memory BW, IO events)
   └── Per-core: IA32_FIXED_CTR* (C0/C1/C6 residency)
   │
   ▼
PMON Configuration/Readback
   ├── TPMI PMON registers: sv.socket0.cbb{0,1}.base.tpmi.pmon.*
   ├── MSR-based PMON: IA32_FIXED_CTR0/1/2 (residency)
   └── PythonSV: sv.socket0.cbb0.compute*.pma*.gpsb (PMA telemetry)
```

### Interface & Register Matrix

| Register / MSR | Path | Description | Tier Validated |
|---|---|---|---|
| IA32_THERM_STATUS | MSR 0x19C | Per-core thermal status + threshold interrupts | FV |
| IA32_PACKAGE_THERM_STATUS | MSR 0x1B1 | Package-level thermal status | FV |
| MSR_TEMPERATURE_TARGET | MSR 0x1A2 | Tjmax and TCC activation offset | FV |
| MCP_THERMAL_REPORT_1/2 | MSR 0x1A3/0x1A4 | PMT telemetry mirror | FV |
| IA32_THERM_INTERRUPT | MSR 0x19B | TT1/TT2 threshold interrupt config | FV |
| PMON counters | TPMI `sv.socket0.cbb{0,1}.base.tpmi.pmon.*` | CBB PM counters | FV, PSS |
| IA32_FIXED_CTR0/1/2 | MSR 0x309/0x30A/0x30B | C-state residency counters | FV |
| PMA GPSB telemetry | `sv.socket0.cbb0.compute*.pma*.gpsb` | PMA-level thermal telemetry | FV, PSS |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| Package temperature | MSR | `pd.debug.access_to_msr(0x1B1)` | Package thermal status + margin |
| Per-core temperature | MSR | `pd.debug.access_to_msr(0x19C, core=N)` | Core thermal status + digital readout |
| PMON counters | TPMI register | `sv.socket0.cbb0.base.tpmi.pmon.*.show()` | PM event counts |
| C-state residency | MSR | `pd.debug.access_to_msr(0x309)` | Core C0/C1/C6 residency |
| turbostat thermal | OS tool | `turbostat --show CoreTmp,PkgTmp` (PV) | Package and core temperatures |

---

## Section 3: Validation Strategy

Misc Telemetry validation requires multiple tiers because thermal sensors are silicon-only (FV/PV), but thermal aggregation logic and PMON configuration are firmware-validatable in PSS.

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | PMON config, thermal threshold FW logic |
| PSS — HSLE | Single-die RTL | PythonSV → RTL | PMA push telemetry transport, counter logic |
| PSS — XOS | Both-die RTL | PythonSV → full RTL | Cross-die thermal aggregation (SOCKET_THERMAL HPM) |
| FV | Post-silicon NWP | PythonSV → namednodes | Real DTS sensors, real counters, multi-interface |
| PV | Post-silicon NWP + Ubuntu | lm-sensors / turbostat / perf | OS-visible thermal + counter reporting |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| DTS sensor measurement error | ❌ | ❌ | ❌ | ✅ | ✅ |
| Thermal EWMA miscalculation | ✅ | ❌ | ✅ | ✅ | indirect |
| THERMTRIP_N assertion threshold wrong | ❌ | ❌ | ❌ | ✅ | ✅ |
| TT1/TT2 threshold interrupt missed | ✅ | ❌ | ✅ | ✅ | ✅ |
| PMON counter not incrementing | ✅ | ✅ | ✅ | ✅ | ✅ |
| PMON overflow handling | ✅ | ✅ | ✅ | ✅ | ❌ |
| Cross-die thermal aggregation error | ❌ | ❌ | ✅ | ✅ | indirect |
| PMA push telemetry transport error | ❌ | ✅ | ✅ | ✅ | indirect |
| C-state residency counter inaccuracy | ✅ | ✅ | ✅ | ✅ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| DTS temperature readback accuracy | ❌ | ✅ | ✅ | Real sensors |
| Thermal threshold interrupt | ✅ | ✅ | ✅ | FW + OS layer |
| PMON enable/disable/read | ✅ | ✅ | ✅ | All environments |
| C-state residency counting | ✅ | ✅ | ✅ | Counter accuracy |
| Package thermal aggregation | ✅ | ✅ | indirect | FW min/max logic |

---

## Section 5: Risks & Dependencies

### Active Risks

- **No TCDs defined yet**: This TPF has 0 child TCDs. Coverage is currently provided indirectly by thermal TCDs under TP 16030763137 (Thermal Management) and PMON TCDs under CBB CCF PM (22022420505). Risk: orphaned coverage — no direct traceability from this TPF to test execution.
- **NWP-specific thermal delta**: NWP adds MR4-related telemetry pulls and expanded RC telemetry indexing that differ from DMR baseline. These deltas need explicit TCD coverage.

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Real DTS sensor accuracy | FV + PV only | Physical thermal diodes require real silicon |
| **G-2** | THERMTRIP_N destructive test | FV only (controlled) | Catastrophic shutdown — cannot test in production |

---

## Section 6: DFX Considerations

- **DTS via VISA**: Thermal telemetry can be observed via ITH T2 VISA on thermal PMSB domain.
- **PMON freeze-on-overflow**: PMON counters can be configured to freeze on overflow — useful for capturing exact count before wrap.
- **Thermal daisy chain**: DTS instances are chained for thermtrip signal aggregation. Debug requires verifying chain continuity.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| DTS reading during C6 (core power-gated) | *(TCD TBD)* | Always-on DTS (CGU) continues; per-core DTS unavailable |
| PMON counter overflow at 48-bit boundary | *(TCD TBD)* | Counter wraps or freezes (config-dependent) |
| Thermal threshold interrupt during C-state transition | *(TCD TBD)* | Interrupt delivered after core wakes |
| THERMTRIP_N vs PROCHOT_N priority | *(TCD TBD)* | THERMTRIP overrides all — causes immediate shutdown |
| NWP MR4 thermal pull timing | *(TCD TBD)* | MR4 thermal data available within RC telemetry cycle |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

*(No child TCDs currently defined. Future TCD candidates:)*

| Proposed TCD | Scope | Priority |
|---|---|---|
| DTS Thermal Readback Accuracy | DTS sensor readback and reporting correctness | M |
| PM Performance Counter Control | PMON enable/disable/read/overflow | M |
| Thermal Threshold Interrupts (TT1/TT2) | Programmable threshold interrupt generation | M |
| NWP Thermal Telemetry Delta | NWP-specific MR4 pulls, RC telemetry indexing | L |

### References

- [DMR PM HAS — Thermal Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Thermal.html) — DTS, PROCHOT, THERMTRIP, thermal telemetry
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP thermal telemetry deltas
- [TCD 22022420582 — CBB DTS & Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022420582) — CBB thermal sensing topology (under Thermal Management TP)
- [TCD 22022420593 — IMH DTS & Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022420593) — IMH thermal sensing topology (under Thermal Management TP)
- [TCD 22022421190 — CBB CCF PMON](https://hsdes.intel.com/appstore/article-one/#/22022421190) — CBB PMON counters (under CBB CCF PM TP)
- [Intel SDM — IA32_THERM_STATUS](https://www.intel.com/sdm) — MSR 0x19C thermal status / interrupt / threshold

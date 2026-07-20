# TPF 16031169422 — [NWP PM] Mistletoe PRT (Platform Runtime Test)

| Field | Value |
|-------|-------|
| **TPF ID** | [16031169422](https://hsdes.intel.com/appstore/article-one/#/16031169422) |
| **Title** | [NWP PM] Mistletoe PRT (Platform Runtime Test) |
| **Parent TP** | [16030765561 — [NWP PM] PM Interfaces (OS2P/TPMI/PECI/PMT)](https://hsdes.intel.com/appstore/article-one/#/16030765561) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-20 |

---

## Section 1: Feature Classification & Introduction

**Mistletoe PRT (Platform Runtime Test)** is a platform-level runtime test infrastructure designed to validate power management interfaces and flows during actual system operation on NWP. PRT exercises PM features, state transitions, and interface interactions in real-world runtime scenarios to ensure hardware and firmware cooperate correctly under dynamic conditions.

**Classification**: Test infrastructure / methodology (not a silicon feature). PRT orchestrates test execution across PM features (P-states, C-states, thermal protection, SST profiles, RAPL) using vManager and automation tools. NWP PRT reuses DMR infrastructure with NWP-specific adaptations.

**Gating mechanism**: PRT requires a **fully booted system** with PM features enabled. PRT itself has no fuse/BIOS gate — it exercises the gating mechanisms of other features.

**NWP scope**: NWP PRT adapts DMR test infrastructure (vManager config, Raccoon defaults, emulation configs) for NWP topology (2 CBB, 2 IMH, NIO root die). PRT covers single-socket and dual-socket configurations. Accelerator integration tests are included for NWP-supported accelerators.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Test orchestration | vManager + Raccoon automation | NWP PRT plan |
| Platform topologies | Single-socket, dual-socket | NWP platform spec |
| CBB count | 2 (cbb0, cbb1) | NWP topology |
| IMH count | 2 (imh0, imh1) | NWP topology |
| Root die | NIO | NWP architecture |
| PM features exercised | P-states, C-states, PkgC, Thermal, SST, RAPL | PRT test plan |
| Accelerator coverage | DSA, IAA, QAT (if present) | NWP PRT plan |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: Test Orchestration / Automation</strong><br/>
    <small>vManager · Raccoon · PRT scripts · test scheduling · result collection</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: OS / Driver Runtime Environment</strong><br/>
    <small>Linux kernel · intel_pstate · intel-speed-select · cpuidle · thermal_zone</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PM Interface Access</strong><br/>
    <small>TPMI MMIO · OS2P Mailbox · PECI-over-MCTP · PMT telemetry · MSR access</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: PrimeCode / PCode Firmware</strong><br/>
    <small>State machine execution · transition handling · telemetry reporting · error response</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / Platform HW</strong><br/>
    <small>VR · thermal sensors · clock distribution · power gates · accelerator IPs</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L5: Test Orchestration | ❌ | ❌ | ❌ | ❌ | ✅ | PRT requires full automation stack |
| L4: OS / Driver Runtime | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS + driver stack |
| L3: PM Interface Access | ✅ | ✅ | ✅ | ✅ | ✅ | All tiers can exercise interfaces |
| L2: PrimeCode / PCode FW | ✅ | ✅ | ✅ | ✅ | indirect | All tiers validate FW logic |
| L1: Silicon / Platform HW | ❌ | ❌ | ❌ | ✅ | ✅ | Real HW required for full PRT |

### PRT Test Architecture

`
┌─────────────────────────────────────────────────────────┐
│ vManager Test Orchestration                             │
│ - Test plan definition (PM feature matrix)              │
│ - Configuration management (BIOS knobs, platform)       │
│ - Result collection and pass/fail aggregation           │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ Raccoon Runtime Test Engine                             │
│ - PM state transition injection (C-state, P-state)      │
│ - Workload generation (stress, idle, mixed)             │
│ - Interface exerciser (TPMI, OS2P, PECI, PMT)           │
│ - Thermal event injection (ProcHot, Thermtrip)          │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ NWP Platform Under Test                                 │
│ - Single-socket / Dual-socket configs                   │
│ - All PM interfaces active                              │
│ - Accelerators (DSA, IAA, QAT) if populated             │
└─────────────────────────────────────────────────────────┘
`

### PM Flows Exercised by PRT

| PM Flow | Interfaces Used | State Transitions |
|---|---|---|
| P-states (HWP) | TPMI UFS, MSR IA32_HWP_REQUEST | Pn → P1 → P0n → P04 |
| Core C-states | MSR IA32_MWAIT, cpuidle | C0 → C1 → C1e → C6 |
| Package C-states | PrimeCode PkgC FSM | PC0 → PC2 → PC6 |
| Thermal protection | DTS, PROCHOT, Thermtrip | Normal → throttle → shutdown |
| SST profiles | TPMI SST-CP/TF, intel-speed-select | Profile switch, PCT enable/disable |
| RAPL | TPMI RAPL, OS2P mailbox | PL1/PL2 limit → throttle → recover |
| Accelerator PM | TPMI, device PM | Active → idle → power-gate |

### Interface & Register Matrix

| Register / MSR | Path | Description | Tier Validated |
|---|---|---|---|
| All TPMI feature registers | `sv.socket0.nio.punit.tpmi.*` | TPMI-accessible PM state | FV, PV |
| OS_MAILBOX_INTERFACE | MSR 0xB0 | OS2P mailbox | FV, PV |
| PMT counters | `sv.socket0.nio.punit.tpmi.pmt_*` | Telemetry data | FV, PV |
| OOBMSM PECI | `sv.socket0.nio.oobmsm.peci.*` | PECI interface status | FV, PV |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| PM state transitions | OS kernel | `turbostat`, `powertop` | Real-time P/C state residency |
| TPMI register state | PythonSV | `sv.socket0.nio.punit.tpmi.*.show()` | Current PM register values |
| PRT test results | Automation | vManager dashboard | Pass/fail per test case |
| Thermal events | sysfs | `/sys/class/thermal/thermal_zone*/temp` | Temperature + trip point status |

---

## Section 3: Validation Strategy

PRT is inherently a **PV-tier** activity — it requires a fully booted system with all PM features active. However, individual PM interfaces tested by PRT are also validated at PSS and FV tiers independently. PRT adds the **integration dimension**: concurrent PM flows, state transitions under load, and cross-interface interactions.

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP/HSLE/XOS | Pre-silicon | PythonSV | Individual PM interface correctness (not PRT) |
| FV | Post-silicon NWP | PythonSV → namednodes | Individual interface + limited integration |
| PV (PRT) | Post-silicon NWP + Ubuntu | vManager + Raccoon | Full runtime integration, concurrent flows, stress |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS | FV | PV (PRT) |
|---|---|---|---|
| Individual PM interface bug | ✅ | ✅ | ✅ |
| Cross-interface interaction bug | ❌ | ⚠️ | ✅ |
| PM state transition under stress | ❌ | ⚠️ | ✅ |
| Concurrent PM flow conflict | ❌ | ❌ | ✅ |
| Accelerator PM + CPU PM interaction | ❌ | ❌ | ✅ |
| Thermal event during state transition | ❌ | ⚠️ | ✅ |
| Long-duration PM stability | ❌ | ❌ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV (PRT) | Unique value |
|---|---|---|---|---|
| P-state transition under load | ✅ | ✅ | ✅ | PRT: real workload |
| C-state entry/exit cycling | ❌ | ✅ | ✅ | PRT: OS scheduler driven |
| Thermal throttle during turbo | ❌ | ⚠️ | ✅ | PRT: real thermal |
| RAPL + SST concurrent operation | ❌ | ❌ | ✅ | PRT: integration |
| Multi-socket PM coordination | ❌ | ❌ | ✅ | PRT: real multi-socket |

---

## Section 5: Risks & Dependencies

### Active Risks

- **Platform availability**: PRT requires fully functional NWP platform with all PM features enabled; limited by hardware availability.
- **Test infrastructure migration**: vManager/Raccoon configs need NWP-specific adaptation from DMR; migration gaps may delay PRT readiness.
- **Accelerator PM coverage**: NWP accelerator PM integration depends on accelerator silicon readiness.
- **Multi-socket platform**: Dual-socket PRT requires dual-socket platform availability.

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | PRT inherently PV-only | PV only | Runtime integration requires full system; PSS/FV cover individual interfaces |
| **G-2** | Accelerator PM integration | PV + accelerator present | Requires accelerator silicon on NWP platform |
| **G-3** | Multi-socket coordination | Dual-socket PV only | Requires dual-socket platform |

---

## Section 6: DFX Considerations

- **PRT logging**: vManager collects comprehensive test logs including dmesg, turbostat, TPMI dumps.
- **Failure triage**: PRT failures are triaged via TPMI register dump + FW trace + dmesg correlation.
- **Performance baseline**: PRT establishes PM performance baselines (P-state transition latency, C-state residency targets).
- **Regression detection**: PRT run-to-run comparison detects PM performance regressions.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| Thermal event during P-state transition | 16031169423 | Throttle takes priority; P-state converges after thermal clears |
| C-state entry blocked by accelerator | 16031169423 | PkgC entry deferred; no hang; accelerator completes then PkgC proceeds |
| RAPL limit hit during SST profile switch | 16031169423 | RAPL throttle applies first; SST profile switch completes after RAPL settles |
| OS2P mailbox timeout under stress | 16031169423 | OS retries; no system hang; mailbox eventually responds |
| PMT counter read during PM transition | 16031169423 | Returns consistent snapshot (no torn read) |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| [16031169423](https://hsdes.intel.com/appstore/article-one/#/16031169423) | Mistletoe PRT - Platform Runtime Test Verification | open | TBD |

### References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PM architecture overview
- [DMR PRT Infrastructure](https://docs.intel.com/documents/pm_doc/src/server/DMR/PRT/PRT_Infrastructure.html) — PRT test methodology (DMR baseline)
- [vManager Documentation](https://wiki.ith.intel.com/display/vManager) — Test orchestration platform
- [Raccoon Test Engine](https://wiki.ith.intel.com/display/Raccoon) — Runtime test automation

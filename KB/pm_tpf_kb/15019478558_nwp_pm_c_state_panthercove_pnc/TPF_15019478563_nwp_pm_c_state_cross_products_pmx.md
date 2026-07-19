# TPF 15019478563 - [NWP PM] C-State Cross Products & PMX

| Field | Value |
|-------|-------|
| **TPF ID** | [15019478563](https://hsdes.intel.com/appstore/article-one/#/15019478563) |
| **Title** | [NWP PM] C-State Cross Products & PMX |
| **Parent TP** | [15019478558 - [NWP PM] C-State PantherCove PNC](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

This cross-product TPF validates C-state behavior under composite stress and observability frameworks, including PMX telemetry and scenario suites such as BEAT learnings, AshTree PRT, PMX checks, and Solar. It is integration-heavy and exercises interactions across PM features.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBB topology | 2 CBB with 48 cores each | NWP deltas in local TCD cache |
| PkgC6 expectation | Must remain zero on NWP ZBB platforms | Local cross-product TCD notes |
| Common automation family | runPmx cstates variants and framework scripts | Existing TCD text and local scripts |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #1f2937;border-radius:8px;padding:12px;max-width:700px;font-family:Arial,sans-serif;">
  <div style="background:#1d4ed8;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 5: Test Framework Orchestration</strong> (Solar, AshTree, PMX scripts)</div>
  <div style="background:#ea580c;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 4: OS and Tool Interaction</strong> (SVOS runtime and command control)</div>
  <div style="background:#7c3aed;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 3: Firmware Policy and Telemetry Routing</strong></div>
  <div style="background:#16a34a;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 2: PMX/PM Hardware Counters</strong></div>
  <div style="background:#dc2626;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 1: Silicon C-state Realization</strong></div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| Test framework orchestration | No | Yes | Yes | Framework execution needs platform runtime |
| OS and tool interaction | No | Yes | Yes | Full tool path mostly in FV/PV |
| Firmware policy and telemetry routing | Yes | Yes | Partial | Deep internal visibility reduced in PV |
| PMX/PM counters | Yes | Yes | Yes | Core observability path across tiers |
| Silicon realization | Yes | Yes | Partial | PV validates via external signatures |

### Cross-Product Validation Flow

1. Select scenario lane (BEAT, AshTree PRT, PMX-focused, Solar stress).
2. Execute workload/idle pattern for target scope.
3. Collect PMX and residency evidence.
4. Correlate C-state behavior with expected policy and invariants.
5. Confirm health checks and no regressions.

### Interface & Register Matrix

| Register / Signal | Purpose | Expected behavior |
|---|---|---|
| PMX core cstate signals | Runtime cstate classification | Align with workload-induced transitions |
| PMX package cstate signal | Package-level check | No unintended PkgC6 on NWP ZBB |
| Core C6 residency MSR views | Per-core deep-idle evidence | Increments where expected |

### Observability

| Observable | Tool / Command | What it confirms |
|---|---|---|
| PMX state telemetry | runPmx.py -p cstates | Runtime state reporting correctness |
| Scripted stress behavior | Solar/AshTree style flows | Stability under aggressive transition patterns |
| Error-free execution | NLOG/MCA + hang checks | No critical side effects across scenarios |

---

## Section 3: Validation Strategy

Use multi-scenario decomposition so each cross-product lane targets a different risk pattern: stress-only, combined PM interaction, telemetry fidelity, and regression catch. Require at least one telemetry-plus-residency correlation checkpoint per lane.

---

## Section 4: Tier Coverage

| Scenario | PSS | FV | PV | Evidence |
|---|---|---|---|---|
| BEAT learnings replay | Yes | Yes | Partial | Known issue replay and signature match |
| AshTree PRT | Yes | Yes | Partial | C-state and P-state interaction |
| PMX telemetry validation | Yes | Yes | Yes | PMX vs residency coherence |
| Solar stress loops | Yes | Yes | Partial | High-rate transition stability |

---

## Section 5: Risks & Dependencies

| Risk / Dependency | Impact | Mitigation |
|---|---|---|
| Framework version mismatch | Non-reproducible failures | Pin test package and command-line profile |
| Combined feature interaction noise | Difficult root cause | Isolate failing lane and replay minimal reproducer |
| PMX readback timing skew | False mismatch against MSR | Time-align collection points and repeat sample |

Accepted coverage limitations: some cross-product combinations are too expensive for full PV sweep and remain sampled.

---

## Section 6: DFX Considerations

- Save scenario lane identifier and exact command line in every log bundle.
- Keep PMX snapshot plus MSR snapshot in same capture epoch.
- Track per-lane flakiness to identify infrastructure vs silicon regressions.

---

## Section 7: Common Corner Cases

| Corner case | Why it matters | Check |
|---|---|---|
| PMX indicates C-state but residency static | Telemetry mismatch risk | Re-read both sources with synchronized window |
| Solar stress causes intermittent hangs | Transition-path robustness issue | Collect NLOG, MCA, and last-state checkpoints |
| Cross-product lane passes individually but fails combined | Interaction bug | Execute combined sequence with staged enables |

---

## Section 8: TCD Coverage Summary & References

### TCD Coverage Map

| TCD ID | Title | Coverage role |
|---|---|---|
| [22022421269](https://hsdes.intel.com/appstore/article-one/#/22022421269) | BEAT learnings | Historical issue replay and guardrails |
| [22022421289](https://hsdes.intel.com/appstore/article-one/#/22022421289) | AshTree PRT | Cross-product integrated validation |
| [22022421293](https://hsdes.intel.com/appstore/article-one/#/22022421293) | PMX | PM telemetry and state observability |
| [22022421307](https://hsdes.intel.com/appstore/article-one/#/22022421307) | Solar | Stress framework for transition robustness |

### Reference Context

| Item | Value |
|---|---|
| Parent TP | [15019478558](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| Scope | Cross-product C-state behavior and PMX-backed observability |

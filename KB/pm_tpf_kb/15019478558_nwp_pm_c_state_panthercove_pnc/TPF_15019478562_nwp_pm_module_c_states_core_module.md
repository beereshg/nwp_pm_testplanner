# TPF 15019478562 - [NWP PM] Module C-States (Core-Module)

| Field | Value |
|-------|-------|
| **TPF ID** | [15019478562](https://hsdes.intel.com/appstore/article-one/#/15019478562) |
| **Title** | [NWP PM] Module C-States (Core-Module) |
| **Parent TP** | [15019478558 - [NWP PM] C-State PantherCove PNC](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

Module C-states validate the relationship between per-core low-power behavior and module-level MC6 behavior. This is a silicon-observable feature with strict topology assumptions because module counters and state transitions must align with core-side residency behavior.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| DCM/module count | 12 modules per socket on NWP | NWP delta notes in local TCD cache |
| Core topology | 96 cores (2 CBB x 48) | NWP architecture constants |
| Primary metric | MC6 residency counter progression | Child MC6 residency TCD |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #1f2937;border-radius:8px;padding:12px;max-width:700px;font-family:Arial,sans-serif;">
  <div style="background:#1d4ed8;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 5: OS Idle Distribution</strong> (core-level idle demand)</div>
  <div style="background:#ea580c;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 4: BIOS Module Power Policy</strong></div>
  <div style="background:#7c3aed;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 3: Firmware Aggregation Logic</strong> (core to module conditions)</div>
  <div style="background:#16a34a;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 2: Module MC6 Controller</strong></div>
  <div style="background:#dc2626;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 1: Hardware Residency Counters</strong> (module and core views)</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| OS idle distribution | No | Yes | Yes | Requires runtime workload placement |
| BIOS module policy | Yes | Yes | Yes | Configuration visible in all tiers |
| Firmware aggregation | Yes | Yes | Partial | PV has less direct internal visibility |
| Module MC6 controller | Yes | Yes | Partial | Mostly inferred in PV |
| Hardware counters | Yes | Yes | Yes | Counter-based confirmation possible |

### Core-to-Module State Relationship

1. Core-side idle and residency behavior is induced per scenario.
2. Firmware aggregates qualifying core conditions for module-level transition.
3. Module enters or exits MC6 accordingly.
4. Module residency counters are compared against expected state occupancy.

### Interface & Register Matrix

| Register / Signal | Purpose | Expected behavior |
|---|---|---|
| Module MC6 residency counter | Module dwell in MC6 | Must increment during eligible idle windows |
| Per-core C-state counters | Source behavior for aggregation | Correlates with module-level transitions |
| PMX module state reports | Runtime observability | Consistent with MC6 residency trend |

### Observability

| Observable | Tool / Command | What it confirms |
|---|---|---|
| Module-state and residency | PythonSV PM paths | MC6 entry/exit and dwell |
| Core-state preconditions | runPmx cstates plus counter reads | Conditions that drive module behavior |
| Cross-check logic | Counter correlation script | Core and module data coherence |

---

## Section 3: Validation Strategy

Validation uses staged idle depth to observe when module-level transitions become eligible. The strategy verifies that module-state movement is neither too aggressive nor missing when core prerequisites are met.

---

## Section 4: Tier Coverage

| Scenario | PSS | FV | PV | Evidence |
|---|---|---|---|---|
| MC6 residency counter behavior | Yes | Yes | Partial | Counter increments tied to induced idle |
| Core-to-module correlation | Yes | Yes | Partial | Core and module counter trend alignment |
| Multi-module consistency | Yes | Yes | No | Broad module sweep across topology |

---

## Section 5: Risks & Dependencies

| Risk / Dependency | Impact | Mitigation |
|---|---|---|
| Incorrect module indexing | Missing or mis-attributed data | Use NWP-specific module loops and index maps |
| Core activity leakage | Prevents expected MC6 residency | Isolate workloads and control interrupts |
| PMX path mismatch across environments | Debug friction | Keep PythonSV and PMX mapping notes in triage packet |

Accepted coverage limitations: complete module-sweep stress is strongest in PSS/FV, with reduced depth in PV.

---

## Section 6: DFX Considerations

- Capture module-level and core-level counters in the same timestamp window.
- Preserve topology map used by script loops to avoid index confusion.
- Add debug snapshot trigger when core/module correlation diverges.

---

## Section 7: Common Corner Cases

| Corner case | Why it matters | Check |
|---|---|---|
| Module never enters MC6 despite deep core idle | Aggregation logic issue | Verify core preconditions and firmware policy state |
| Module enters too frequently | Potential false-positive eligibility | Compare against workload activity and interrupt trace |
| One module behaves differently | Topology or local controller defect | Sweep and compare all module counters |

---

## Section 8: TCD Coverage Summary & References

### TCD Coverage Map

| TCD ID | Title | Coverage role |
|---|---|---|
| [22022421260](https://hsdes.intel.com/appstore/article-one/#/22022421260) | CStates MC6 residency counter | Module C-state residency behavior |

### Reference Context

| Item | Value |
|---|---|
| Parent TP | [15019478558](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| Scope | Core-to-module state relationship and MC6 coverage |

# TPF 15019478560 - [NWP PM] Fast C1E

| Field | Value |
|-------|-------|
| **TPF ID** | [15019478560](https://hsdes.intel.com/appstore/article-one/#/15019478560) |
| **Title** | [NWP PM] Fast C1E |
| **Parent TP** | [15019478558 - [NWP PM] C-State PantherCove PNC](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

Fast C1E is a firmware-orchestrated, latency-sensitive idle feature layered on C1 behavior. It validates autopromotion, start/end flow, and voltage-aware exit timing so idle power is reduced without violating wake latency expectations.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Enable control | MSR power control C1E enable bit (0x1FC[1]) | Local Fast C1E TCD content |
| Latency objective | Fast exit path target in low-microsecond range | Fast C1E start/end flow notes |
| Topology basis | 2 CBB, 48 cores per CBB | NWP local architecture constants |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #1f2937;border-radius:8px;padding:12px;max-width:700px;font-family:Arial,sans-serif;">
  <div style="background:#1d4ed8;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 5: OS Idle Trigger</strong> (HALT or MWAIT)</div>
  <div style="background:#ea580c;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 4: BIOS C1E Policy</strong> (autopromotion enable)</div>
  <div style="background:#7c3aed;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 3: PCode/Firmware Flow</strong> (start/end sequencing)</div>
  <div style="background:#16a34a;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 2: FIVR Voltage Transition</strong> (ramp-down and ramp-up)</div>
  <div style="background:#dc2626;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 1: Core Clock Gate/Ungate</strong> (resume correctness)</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| OS idle trigger | No | Yes | Yes | Needs OS runtime context |
| BIOS C1E policy | Yes | Yes | Yes | Enable-state validation in all tiers |
| Firmware flow | Yes | Yes | Partial | Internal sequencing visibility reduced in PV |
| FIVR transition | Yes | Yes | Partial | Precise telemetry mainly in PSS/FV |
| Core gate/ungate | Yes | Yes | Yes | Observable via behavior and counters |

### Fast C1E Start/End Flow

1. Core receives idle instruction and enters C1 path.
2. If C1E enabled, voltage ramps down to C1E target.
3. Core remains in low-power gated state and residency accumulates.
4. Interrupt arrives, voltage ramps up, clock ungates, and execution resumes.

### Interface & Register Matrix

| Register / Signal | Purpose | Expected behavior |
|---|---|---|
| MSR 0x1FC bit[1] | C1E enable control | Must remain asserted during test |
| C1 residency counters | Dwell visibility | Increment in C1/C1E idle windows |
| FIVR telemetry path | Voltage ramp evidence | Ramp-down on entry, ramp-up on exit |

### Observability

| Observable | Tool / Command | What it confirms |
|---|---|---|
| C1E enable bit per core | PythonSV msr_power_ctl read | Global policy propagated correctly |
| Start/end behavior | runPmx.py -p cstates | Entry and exit happen without hang |
| Post-run health | NLOG/MCA checks | No firmware or hardware error side effects |

---

## Section 3: Validation Strategy

Use a two-lane strategy: lane A validates policy enablement and start/end transitions; lane B validates timing-sensitive behavior under repeated wake events. PSS and FV carry root-cause observability, while PV verifies stable behavior under production software stack conditions.

---

## Section 4: Tier Coverage

| Scenario | PSS | FV | PV | Evidence |
|---|---|---|---|---|
| C1E autopromotion | Yes | Yes | Partial | Enable bit and idle-path behavior |
| C1E basic functionality | Yes | Yes | Yes | Enter, dwell, exit without regressions |
| C1E start/end flow | Yes | Yes | Partial | Voltage and clock sequence correctness |

---

## Section 5: Risks & Dependencies

| Risk / Dependency | Impact | Mitigation |
|---|---|---|
| Wrong BIOS C1E configuration | Invalid baseline behavior | Enforce known-good BIOS recipe per run |
| Timer/interrupt noise | Exit latency variance | Use controlled synthetic wake sources |
| FIVR telemetry unavailability | Harder triage in PV | Rely on indirect evidence and FV reproducer |

Accepted coverage limitations: PV does not always expose internal FIVR ramp checkpoints with the same granularity as FV/PSS.

---

## Section 6: DFX Considerations

- Capture pre/post MSR snapshots for C1E enable and residency evidence.
- Preserve command line and timing profile used during latency checks.
- Store a compact failure packet: BIOS knobs, wake source, core scope, NLOG excerpt.

---

## Section 7: Common Corner Cases

| Corner case | Why it matters | Check |
|---|---|---|
| Autopromotion enabled but no deeper behavior | Policy latch issue | Cross-check bit state vs observed behavior |
| Fast wake bursts | May reveal ramp race | Repeated short idle and wake loops |
| Uneven per-core behavior | Potential per-core configuration skew | Compare all core samples across both CBBs |

---

## Section 8: TCD Coverage Summary & References

### TCD Coverage Map

| TCD ID | Title | Coverage role |
|---|---|---|
| [22022421276](https://hsdes.intel.com/appstore/article-one/#/22022421276) | CState Fast C1E: C1E autopromotion | Policy enable and autopromotion behavior |
| [22022421282](https://hsdes.intel.com/appstore/article-one/#/22022421282) | CState Fast C1E: C1E basic functionaity | Baseline feature functionality |
| [22022421287](https://hsdes.intel.com/appstore/article-one/#/22022421287) | CState Fast C1E: C1E start/end flow | Entry/exit flow and timing validation |

### Reference Context

| Item | Value |
|---|---|
| Parent TP | [15019478558](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| Scope | Fast C1E policy, flow, and observability on NWP |

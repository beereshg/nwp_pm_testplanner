# TPF 15019478559 - [NWP PM] Core C1/C6 (Entry/Exit/Residency)

| Field | Value |
|-------|-------|
| **TPF ID** | [15019478559](https://hsdes.intel.com/appstore/article-one/#/15019478559) |
| **Title** | [NWP PM] Core C1/C6 (Entry/Exit/Residency) |
| **Parent TP** | [15019478558 - [NWP PM] C-State PantherCove PNC](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

Core C1/C6 validation is a silicon-heavy flow with firmware and OS orchestration. The feature validates entry actions, exit actions, and residency accumulation for per-core idle transitions on PantherCove (NWP).

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Total cores | 96 (2 CBB x 48 cores) | NWP topology in TP/TCD cache |
| Deep package C6 behavior | PkgC6 is disabled on NWP (ZBB expectation) | Local TCD deltas |
| Core C-state residency signal | IA32 residency counter family (0x660-0x669) and C6 residency MSRs | TCD C1/C6 residency content |
| Typical automation | runPmx cstates and PythonSV checks | Existing local TCD text |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #1f2937;border-radius:8px;padding:12px;max-width:700px;font-family:Arial,sans-serif;">
  <div style="background:#1d4ed8;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 5: OS Workload / Idle Instruction</strong> (HALT or MWAIT)</div>
  <div style="background:#ea580c;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 4: BIOS and Policy Enablement</strong> (C-state enable knobs)</div>
  <div style="background:#7c3aed;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 3: PCode Coordination</strong> (entry sequencing and wake conditions)</div>
  <div style="background:#16a34a;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 2: Acode / Core Power Controller</strong> (clock and power gating)</div>
  <div style="background:#dc2626;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 1: Silicon Enforcement</strong> (residency counters and state latches)</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| OS workload / idle | No | Yes | Yes | Requires booted OS and workload control |
| BIOS and policy enablement | Yes | Yes | Yes | Knob validation and feature gating |
| PCode coordination | Yes | Yes | Partial | Deep timing mainly covered in FV/PSS |
| Acode/core power controller | Yes | Yes | Partial | Direct register observability stronger pre-Si and FV |
| Silicon enforcement | Yes | Yes | No | PV usually validates behavior indirectly |

### Core C1/C6 Flow

1. OS issues HALT or MWAIT for idle core.
2. Core enters C1 quickly; deeper policy allows C6 transition under conditions.
3. Entry actions trigger cache and fabric-side sequencing where applicable.
4. Residency counters increase while core remains in state.
5. Interrupt or wake event exits state and resumes execution.

### Interface & Register Matrix

| Register / Signal | Purpose | Expected behavior |
|---|---|---|
| MSR 0x660-0x669 family | Core C-state residency accumulation | Must increment during idle windows |
| IA32 C6 residency view | Deep C6 residency evidence | Increment correlates with induced idle |
| PM state indicators in PythonSV | Current state checkpoint | Matches expected C1/C6 transitions |

### Observability

| Observable | Tool / Command | What it confirms |
|---|---|---|
| Core residency counters | PythonSV register reads | Entry/exit happened and dwell time exists |
| C-state status in PMX path | runPmx.py -p cstates | Runtime state transitions are visible |
| Error health | dmesg/NLOG/MCA checks | No hang or fault during deep-idle cycling |

---

## Section 3: Validation Strategy

Validation combines directed idle scenarios and telemetry correlation. PSS validates deterministic sequencing and state transitions with register visibility; FV validates on real platform timing and interrupt behavior; PV confirms production-level observability and no regressions under realistic software stacks.

---

## Section 4: Tier Coverage

| Scenario | PSS | FV | PV | Evidence |
|---|---|---|---|---|
| Core C6 basic functionality | Yes | Yes | Partial | C6 entry/exit and state confirmation |
| Entry action correctness | Yes | Yes | No | Ordered action checkpoints |
| Exit action correctness | Yes | Yes | Partial | Wake flow and resume checks |
| C1 residency accounting | Yes | Yes | Yes | Counter progression under idle |

---

## Section 5: Risks & Dependencies

| Risk / Dependency | Impact | Mitigation |
|---|---|---|
| BIOS defaults differ across labs | False failures in state entry | Lock BIOS recipe per run and archive knob dump |
| Background interrupts distort residency | Noisy counter deltas | Use controlled idle windows and repeated sampling |
| PM telemetry path drift | Missing observability in one tier | Cross-check PMX and MSR views |

Accepted coverage limitations: PV may not expose every low-level internal state used in PSS/FV debug.

---

## Section 6: DFX Considerations

- Use PythonSV snapshots before/after workload to preserve pre-fail state.
- Capture NLOG and MCA error scan at start and end of test loop.
- Keep a minimal triage bundle: BIOS knobs, command line, core-scope selection, and residency deltas.

---

## Section 7: Common Corner Cases

| Corner case | Why it matters | Check |
|---|---|---|
| Rapid idle/wake ping-pong | Can expose unstable entry/exit handling | Repeat short dwell cycles across all cores |
| Asymmetric core behavior | One core stuck out of expected state | Compare per-core residency spread |
| Deep idle under low activity | Can mask latent wake bugs | Inject periodic wake interrupts and verify resume |

---

## Section 8: TCD Coverage Summary & References

### TCD Coverage Map

| TCD ID | Title | Coverage role |
|---|---|---|
| [22022421247](https://hsdes.intel.com/appstore/article-one/#/22022421247) | CState C6 basic functionality | Primary C6 entry/exit behavior |
| [22022421250](https://hsdes.intel.com/appstore/article-one/#/22022421250) | CState Entry Actions | Entry micro-sequence correctness |
| [22022421253](https://hsdes.intel.com/appstore/article-one/#/22022421253) | CState Exit Actions | Exit and wake sequence correctness |
| [22022421257](https://hsdes.intel.com/appstore/article-one/#/22022421257) | CStates C1 residency counter | C1 residency accounting |

### Reference Context

| Item | Value |
|---|---|
| Parent TP | [15019478558](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| Scope | C1/C6 entry, exit, and residency validation on NWP |

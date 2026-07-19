# TPF 15019478561 - [NWP PM] C-State Demotion/Undemotion

| Field | Value |
|-------|-------|
| **TPF ID** | [15019478561](https://hsdes.intel.com/appstore/article-one/#/15019478561) |
| **Title** | [NWP PM] C-State Demotion/Undemotion |
| **Parent TP** | [15019478558 - [NWP PM] C-State PantherCove PNC](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

Demotion/undemotion is policy-heavy C-state control that trades power against latency by selecting shallower or deeper states based on platform conditions. This TPF captures C6/C1 policy configuration and verifies that behavior follows programmed control, not random fallback.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Primary policy scope | C6 and C1 demotion/undemotion | Child TCD title and TP context |
| Validation focus | Configuration correctness plus runtime response | Local TCD behavior conventions |
| NWP platform baseline | 96 cores across 2 CBBs | NWP architecture constants |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #1f2937;border-radius:8px;padding:12px;max-width:700px;font-family:Arial,sans-serif;">
  <div style="background:#1d4ed8;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 5: Workload and Latency Demand</strong></div>
  <div style="background:#ea580c;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 4: BIOS Demotion Policy Inputs</strong></div>
  <div style="background:#7c3aed;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 3: PCode Policy Engine</strong> (demote or undemote decision)</div>
  <div style="background:#16a34a;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 2: C-state Entry Selector</strong> (effective target state)</div>
  <div style="background:#dc2626;color:#fff;padding:8px;border-radius:4px;text-align:center;margin:4px 0;"><strong>Layer 1: Core State Realization</strong> (observed residency)</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| Workload and latency demand | No | Yes | Yes | Dynamic behavior needs runtime load control |
| BIOS policy inputs | Yes | Yes | Yes | Config can be checked in all tiers |
| PCode policy engine | Yes | Yes | Partial | Internal decision trace strongest pre-Si/FV |
| Entry selector | Yes | Yes | Partial | PV mostly infers from external effects |
| Core state realization | Yes | Yes | Yes | Residency and state outcomes observable |

### Demotion/Undemotion Behavioral Flow

1. Platform policy programs demotion and undemotion controls.
2. Runtime conditions are evaluated (latency pressure, wake behavior, activity).
3. Firmware may demote target from deep to shallow state or restore deeper entry.
4. Resulting state distribution is observed through counters and PM telemetry.

### Interface & Register Matrix

| Register / Signal | Purpose | Expected behavior |
|---|---|---|
| Demotion/undemotion control fields | Policy activation | Reflect configured policy |
| Core residency counters | Effective state depth evidence | Counter mix shifts with policy |
| PMX cstate reports | Runtime state interpretation | Align with policy-intended behavior |

### Observability

| Observable | Tool / Command | What it confirms |
|---|---|---|
| Policy configuration | PythonSV configuration reads | Correct setup before runtime |
| Effective state behavior | runPmx cstates plus residency checks | State depth follows programmed policy |
| Health checks | NLOG/MCA scan | No unexpected demotion side effects |

---

## Section 3: Validation Strategy

Use controlled A/B runs: baseline without aggressive demotion tuning and policy-enabled runs with identical workload conditions. Compare state-depth and residency signatures to prove policy effect. Triangulate with PMX and MSR evidence.

---

## Section 4: Tier Coverage

| Scenario | PSS | FV | PV | Evidence |
|---|---|---|---|---|
| C6/C1 demotion configuration | Yes | Yes | Yes | Control fields and setup confirmation |
| Runtime demotion behavior | Yes | Yes | Partial | Residency shift under stress/load |
| Undemotion recovery behavior | Yes | Yes | Partial | Return-to-deeper-state under relaxed conditions |

---

## Section 5: Risks & Dependencies

| Risk / Dependency | Impact | Mitigation |
|---|---|---|
| Incorrect baseline policy | Ambiguous results | Capture initial policy snapshot and enforce reset recipe |
| Workload not representative | False pass on policy behavior | Use deterministic stress and idle phases |
| Limited internal telemetry in PV | Harder attribution | Require FV reproducer for policy bugs |

Accepted coverage limitations: direct firmware policy-decision traces may not be available in PV.

---

## Section 6: DFX Considerations

- Keep before/after policy dumps and residency histogram snapshots.
- Add regression checkpoint for unexpected persistent shallow-state behavior.
- Correlate failing runs with configuration blob and BIOS profile.

---

## Section 7: Common Corner Cases

| Corner case | Why it matters | Check |
|---|---|---|
| Persistent demotion despite relaxed load | Undemotion path stuck | Observe deep-state return after idle dwell |
| Rapid toggling between shallow/deep | Oscillation can destabilize latency | Evaluate transition stability across loops |
| Asymmetric policy behavior across CBBs | Potential topology-specific bug | Compare CBB0 vs CBB1 state distributions |

---

## Section 8: TCD Coverage Summary & References

### TCD Coverage Map

| TCD ID | Title | Coverage role |
|---|---|---|
| [22022421266](https://hsdes.intel.com/appstore/article-one/#/22022421266) | CStates: C6/C1 Demotion/Undemotion Configuration | Policy programming and runtime behavior |

### Reference Context

| Item | Value |
|---|---|
| Parent TP | [15019478558](https://hsdes.intel.com/appstore/article-one/#/15019478558) |
| Scope | C-state policy demotion and undemotion validation |

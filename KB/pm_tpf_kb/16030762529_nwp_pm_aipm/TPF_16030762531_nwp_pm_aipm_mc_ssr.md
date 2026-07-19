# TPF 16030762531 — [NWP PM] AIPM - Memory Trunk Clock Gating & SSR

| Field | Value |
|-------|-------|
| **TPF ID** | [16030762531](https://hsdes.intel.com/appstore/article-one/#/16030762531) |
| **Title** | [NWP PM] AIPM - Memory Trunk Clock Gating & SSR |
| **Parent TP** | [16030762529 — [NWP PM] Autonomous Idle PM (AIPM)](https://hsdes.intel.com/appstore/article-one/#/16030762529) |
| **Status** | rejected (ZBB) |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**MC Shallow Self-Refresh (SSR)** and **Memory Trunk Clock Gating** are idle power management features within the AIPM (Autonomous Idle PM) framework. The MC detects sustained memory idle, enters DRAM into self-refresh (SSR — without clock stop on LPDDR6), and gates trunk clocks to reduce power. On server platforms with LPDDR6, the SSR variant is `sref_sx` (self-refresh without clock stop) because the LPDDR6 PHY requires WCK always-on mode.

**Classification**: Silicon/firmware hybrid feature. AIPM is managed autonomously by the RC (Resource Controller) which sends P-channel requests to the MC via MEM_ISA. PrimeCode/BIOS configures SSR policy and timers.

**Gating mechanism**: MC team architecture decision + PkgC6 dependency. SSR entry requires MC idle detection → PActive de-assertion → DRAM self-refresh. On NWP, SSR is disabled by MC team decision (per NWP Memory Feature Set Delta); PkgC6 is also ZBB'd, compounding the SSR path closure.

**NWP Status: REJECTED — ZBB.** Memory PM features (APD, PPD, LPM1/2/3, SSR, SR) are **not enabled** on NWP per MC team architecture decision and confirmed by co-design MCP (2026-06-22). The HAS feature table lists "SREF No Clock Stop = Yes" as a spec compliance entry, **not** a validation enablement indicator. All 5 child TCDs (14 total TCs) are rejected.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| SSR support on NWP | **Disabled** (MC team ZBB) | NWP Memory Feature Set Delta; co-design MCP 2026-06-22 |
| PkgC6 support on NWP | **ZBB'd** | NWP HAS; compounding factor for SSR path |
| LPDDR6 Self-Refresh variant | `sref_sx` (SR without clock stop) | LPDDR6 HAS |
| LPDDR6 Clock Stop | **Not supported** (WCK always-on) | LPDDR6 HAS |
| LPDDR6 PHY Power Down | **Not supported** (WCK always-on) | LPDDR6 HAS |
| WCK Always-On Mode | Yes (required for LPDDR6) | LPDDR6 HAS |
| CLTT (MR4 thermal) | **Active on NWP** (independent of SSR) | NWP HAS |
| TSOD polling | Not used on LPDDR6 | NWP HAS |
| SSR Residency PMON | Counter stays 0 (SSR never entered) | MC PM architecture |
| SSR maintenance timer | 125 ms default, 3 ms guardband (spec) | NWP iMH MAS |
| PActive signal | HW present; SR entry never triggered on NWP | MC PM architecture |
| Memory PM features not enabled | APD, PPD, LPM1/2/3, SSR, SR | NWP Memory Feature Set Delta |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram (Reference — Not Active on NWP)

> **Note:** This diagram shows the MC SSR / trunk clock gating architecture as specified. On NWP, all layers are inactive because SSR is ZBB'd by MC team decision and PkgC6 is not supported.

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / PMT Observability</strong><br/>
    <small>SSR_RESIDENCY PMON counter · MC idle state telemetry</small><br/>
    <small style="color:#ffd700">⚠️ NWP: counter stays 0 (SSR never entered)</small>
  </div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: BIOS / PrimeCode Policy</strong><br/>
    <small>SSR enable knob · AIPM timer configuration · P-channel SSR flow enable</small><br/>
    <small style="color:#ffd700">⚠️ NWP: SSR knobs not programmed; AIPM SSR flows not enabled</small>
  </div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: RC / MEM_ISA (AIPM Autonomous Controller)</strong><br/>
    <small>Idle detection → P-channel request to MC · SSR entry/exit via AMBA LPI</small><br/>
    <small style="color:#ffd700">⚠️ NWP: RC never sends SSR P-channel request</small>
  </div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: MC / DRAM Interface</strong><br/>
    <small>PActive de-assert → DRAM sref_sx entry · SSR residency timer · Maintenance wake</small><br/>
    <small style="color:#ffd700">⚠️ NWP: PActive never de-asserts for SR; sref_sx never issued</small>
  </div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: LPDDR6 PHY / DRAM Silicon</strong><br/>
    <small>WCK always-on · No clock stop · No PHY power-down · MR4 thermal (active)</small><br/>
    <small style="color:#ffd700">⚠️ NWP: PHY always-on; CLTT via MR4 is the only active MC PM function</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

> **All layers inactive on NWP** — SSR ZBB'd. Table retained for reference if feature is re-enabled on a future stepping or successor program.

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| OS / PMT Observability | ❌ | ❌ | ❌ | SSR_RESIDENCY counter stays 0; no observable SSR state |
| BIOS / PrimeCode Policy | ❌ | ❌ | ❌ | SSR knobs not programmed on NWP |
| RC / MEM_ISA (AIPM) | ❌ | ❌ | ❌ | RC never sends SSR P-channel request |
| MC / DRAM Interface | ❌ | ❌ | ❌ | PActive never de-asserts for SR entry |
| LPDDR6 PHY / DRAM Silicon | ❌ | ❌ | ❌ | PHY always-on; clock stop not supported |

### MC SSR Entry / Exit Flow (Reference Architecture)

```
┌───────────────────────────────────────────────────────────────┐
│                     MC SSR Entry Flow (Spec)                  │
│                                                               │
│  MC detects sustained idle                                    │
│       │                                                       │
│       ▼                                                       │
│  AIPM timer expires (programmable idle threshold)             │
│       │                                                       │
│       ▼                                                       │
│  RC sends P-channel request to MC via MEM_ISA                 │
│       │                                                       │
│       ▼                                                       │
│  MC de-asserts PActive → DRAM enters sref_sx                  │
│       │                                                       │
│       ▼                                                       │
│  SSR_RESIDENCY PMON counter starts accumulating               │
│  MEM_ISA maintenance timer starts (125 ms default)            │
│                                                               │
│  ─── NWP: Flow stops at step 1 ─── SSR entry ZBB'd ───       │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                     MC SSR Exit Flow (Spec)                   │
│                                                               │
│  Trigger: memory access OR maintenance timer expiry (125 ms)  │
│       │                                                       │
│       ▼                                                       │
│  MC asserts PActive → RC exits SSR state                      │
│       │                                                       │
│       ▼                                                       │
│  PHY + DRAM resume normal operation                           │
│  SSR_RESIDENCY PMON counter stops                             │
│                                                               │
│  ─── NWP: Never reached (SSR never entered) ───              │
└───────────────────────────────────────────────────────────────┘
```

### LPDDR6 Power Mode Support Matrix

| Power Mode | LPDDR6 HW Support | NWP Enabled | Notes |
|---|---|---|---|
| Self-Refresh (sref_sx) | ✅ Yes | ❌ ZBB'd | SR without clock stop; MC team disabled |
| Clock Stop during SR | ❌ No | N/A | WCK always-on; no CK/WCK tristate |
| PHY Power Down | ❌ No | N/A | LPDDR6 PHY always-on |
| Deep Sleep Mode | ❌ No | N/A | Not supported on LPDDR6 |
| APD / PPD | ❌ No | ❌ ZBB'd | Not specified for NWP LPDDR6 |
| LPM1 / LPM2 / LPM3 | ❌ No | ❌ ZBB'd | Not specified for NWP LPDDR6 |
| WCK Always-On | ✅ Yes | ✅ Active | Required for LPDDR6 |
| CLTT (MR4 thermal) | ✅ Yes | ✅ Active | Replaces TSOD polling; independent of SSR |

### Interface & Register Matrix

| Register / Interface | Description | NWP Status |
|---|---|---|
| MC SSR enable knob | BIOS/PCode enable for SSR entry | ZBB'd — not programmed |
| PActive signal | MC→DRAM: de-asserted to signal SR entry | HW present; never de-asserts for SR on NWP |
| sref_sx command | MC DRAM command for SR without clock stop | HW present; never issued on NWP |
| DRAM MR4 | Thermal readout register; polled by MC for CLTT | ✅ Active on NWP |
| SSR_RESIDENCY PMON | Perfmon counter tracking SSR residency time | Not applicable (SSR ZBB'd; stays 0) |
| AIPM timer registers | RC idle detection timer configuration | Not applicable (SSR ZBB'd) |
| AMBA LPI P-channel | SSR entry/exit protocol between RC and MC | HW present; SSR flow not activated |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| SSR_RESIDENCY PMON counter | HW counter | PythonSV namednodes | SSR gating time (stays 0 on NWP) |
| MR4 register | DRAM register | MC read via LPDDR6 mode register | Thermal status (active on NWP) |
| PActive state | Signal | Logic analyzer / VISA | MC→DRAM active indicator (never de-asserts for SR on NWP) |
| AIPM SSR timer | Config register | PythonSV namednodes | Idle threshold for SSR entry (not configured on NWP) |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs Affected |
|---|---|---|
| NWP (single-die, LPDDR6) | SSR ZBB'd by MC team; all SSR TCs rejected | All 5 TCDs |
| DMR (reference, DDR5/MCR) | SSR enabled; full entry/exit/residency path | N/A (different program) |
| NWP PkgC6 ZBB | Compounding: even if SSR were enabled, PkgC6 path is closed | Cross Products TCD (22022421230) |

---

## Section 3: Validation Strategy

**All tiers inactive for this TPF** — SSR is ZBB'd on NWP. No validation is required or possible for MC SSR features.

The only MC PM function that remains active on NWP from the AIPM scope is **CLTT via MR4** (thermal throttling), which is validated under a separate TPF (not under this MC SSR TPF).

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies that all layers are unclaimed because the feature is ZBB'd. All unclaimed layers are documented as accepted gaps in §5 Accepted Coverage Limitations.

### Why No Validation Is Needed

1. **SSR entry never occurs**: MC team disabled SSR at the architecture level (NWP Memory Feature Set Delta)
2. **PkgC6 also ZBB'd**: The deepest MC idle state requiring SSR is not available
3. **PHY constraints**: LPDDR6 WCK always-on eliminates clock stop and PHY power-down scenarios
4. **Co-design confirmed**: Three independent co-design MCP sources confirmed the ZBB (2026-06-22)

---

## Section 4: Tier Coverage

**All tiers: N/A** — feature ZBB'd on NWP. No bug coverage matrix applicable.

### Bug Coverage Matrix (Reference — If Feature Were Enabled)

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| SSR entry/exit timing | ⚠️ | ❌ | ✅ | ✅ | indirect |
| PActive signaling | ⚠️ | ❌ | ✅ | ✅ | ❌ |
| SSR residency counter | ❌ | ❌ | ✅ | ✅ | indirect |
| CLTT interaction during SSR | ❌ | ❌ | ✅ | ✅ | ❌ |
| PHY power-down (N/A LPDDR6) | ❌ | ❌ | ❌ | ❌ | ❌ |
| SSR x PkgC6 cross-product | ❌ | ❌ | ✅ | ✅ | ❌ |
| SSR x ADR cross-product | ❌ | ❌ | ✅ | ✅ | ❌ |
| BIOS SSR knob configuration | ✅ safe | ❌ | ❌ | ✅ | ❌ |

> **Note**: This matrix is retained for reference only. On NWP, all rows are N/A because SSR is ZBB'd.

---

## Section 5: Risks & Dependencies

### Active Risks

- **Risk: HAS vs MC team ZBB conflict** — NWP HAS feature table lists "SREF No Clock Stop = Yes" as spec compliance, while MC team has ZBB'd SSR. Treat as ZBB per TPF review and co-design confirmation. If HAS is updated to clarify, no TC changes needed.
- **Risk: Future stepping re-enablement** — If SSR is re-enabled on a future NWP stepping, all 5 TCDs (14 TCs) would need to be un-ZBB'd and validated. Architecture reference material preserved in §2 for this contingency.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | MC SSR entry/exit validation | None (ZBB) | SSR entry never occurs on NWP; MC team architecture decision confirmed by co-design MCP 2026-06-22 |
| **G-2** | SSR_RESIDENCY perfmon counter | None (ZBB) | Counter stays 0; SSR never entered; no observable state to validate |
| **G-3** | SSR x PkgC6 cross-product | None (ZBB) | Double ZBB: both SSR and PkgC6 are disabled on NWP |
| **G-4** | PHY power-down during SSR | None (N/A) | LPDDR6 PHY does not support clock stop or power-down (WCK always-on) |
| **G-5** | SSR BIOS knob validation | None (ZBB) | SSR knobs have no effect; MC SSR not enabled |

---

## Section 6: DFX Considerations

- **VISA/ITH T2**: MC SSR entry/exit signals are available via VISA for debug on platforms where SSR is enabled. Not applicable on NWP (SSR ZBB'd).
- **SSR_RESIDENCY PMON**: Debug counter for SSR gating time. Stays at 0 on NWP — can serve as a negative confirmation that SSR is properly disabled.
- **MR4 thermal polling**: CLTT via MR4 is the only active MC PM DFx observable on NWP within this feature scope.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior (NWP) |
|---|---|---|
| HAS says "SREF No Clock Stop = Yes" but MC team ZBB'd SSR | All 5 TCDs | Treat as ZBB per co-design confirmation; HAS entry is spec compliance, not enablement |
| CLTT thermal event during idle | TCD 22022421220 (Actions) | CLTT via MR4 is active but SSR is not entered; no SSR exit to trigger |
| SSR x ADR — ADR during self-refresh | TCD 22022421230 (Cross Products) | ADR never interrupts SSR because SSR never occurs |
| PHY power-down attempt | TCD 22022421220 (Actions) | LPDDR6 PHY always-on; clock stop HW not present; no recovery scenario |
| PkgC6 dependency on SSR | TCD 22022421230 (Cross Products) | PkgC6 also ZBB'd on NWP; double ZBB eliminates the entire MC idle→PkgC6 path |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| [22022421220](https://hsdes.intel.com/appstore/article-one/#/22022421220) | MC Shallow Self Refresh Actions | rejected (ZBB) | 3 |
| [22022421222](https://hsdes.intel.com/appstore/article-one/#/22022421222) | MC Shallow Self Refresh BIOS knobs | rejected (ZBB) | 1 |
| [22022421228](https://hsdes.intel.com/appstore/article-one/#/22022421228) | MC Shallow Self Refresh Boot Time Setup | rejected (ZBB) | 5 |
| [22022421230](https://hsdes.intel.com/appstore/article-one/#/22022421230) | MC Shallow Self Refresh Cross Products | rejected (ZBB) | 4 |
| [22022421233](https://hsdes.intel.com/appstore/article-one/#/22022421233) | MC Shallow Self Refresh Entry / Residency | rejected (ZBB) | 1 |

**Total**: 5 TCDs, 14 TCs — all rejected (ZBB)

### ZBB Evidence Chain

| Source | Date | Statement |
|---|---|---|
| NWP Memory Feature Set Delta | 2026 | APD/PPD, LPM1/2/3, SSR, SR: not enabled |
| Co-design MCP (MAS) | 2026-06-22 | "Memory Power Management: No Shallow Self-Refresh (SSR)" |
| Co-design MCP (PkgC6) | 2026-06-22 | "PkgC6 is not supported on NWP. Therefore, there will not be any SR, nor any SSR flows" |
| Co-design MCP (MC team) | 2026-06-22 | "MC team ZBBed shallow self-refresh (SSR)" |
| LPDDR6 HAS | 2026 | WCK always-on; no clock stop; no PHY power-down |

### References

- [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/overview/nwp_has.html) — NWP Memory PM feature delta; SREF spec compliance table
- [LPDDR6 HAS](https://docs.intel.com/documents/iparch/mc/has/gen6/releases/lpddr6/lpddr6.html) — Self-Refresh=Yes; Clock Stop=No; PHY Power Down=No; WCK Always-On=Yes
- [NWP HAS Comments](https://docs.intel.com/documents/custom-xeon/newport-docs/has/comments.html) — MC team ZBB statement
- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — SSR ZBB confirmation; TPF TC review 2026-06-01; all 14 MC SSR TCs ZBB'd
- [NWP iMH MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/) — SSR entry/exit architecture; P-channel protocol; MEM_ISA timer
- [Parent TP — 16030762529 AIPM](https://hsdes.intel.com/appstore/article-one/#/16030762529) — Autonomous Idle PM parent test plan

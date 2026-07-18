# TPF 15019477657 — [NWP PM] RACL

| Field | Value |
|-------|-------|
| **TPF ID** | [15019477657](https://hsdes.intel.com/appstore/article-one/#/15019477657) |
| **Title** | [NWP PM] RACL |
| **Parent TP** | [15019477771 — [NWP PM] RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477771) |
| **Status** | rejected (ZBB) |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**RACL (Running Average Current Limit)** is a per-VR **Thermal Design Current (TDC)** limiter designed for **dual-VCCIN** server platforms. It regulates each VCCIN voltage regulator to its TDC specification by computing a running average current limit (using RMS-based EWMA) and dynamically adjusting the CPU frequency ceiling — analogous to RAPL but for current instead of power.

**Classification**: Firmware-heavy feature with silicon enforcement. Each iMH PrimeCode instance runs its own RACL PID loop; hardware provides SVID IMON telemetry and frequency ceiling enforcement via CBB PCode.

**Gating mechanism**: `FUSE_TDC_LIMIT` (10-bit, 1A units, per-die). When `FUSE_TDC_LIMIT = 0`, RACL is entirely disabled — PrimeCode skips PID initialization and does not generate RACL frequency limits.

**NWP Status: REJECTED — ZBB.** NWP uses a **single VCCIN rail** (single NIO die topology), identical to GNR and DMR-SP. With one VR supplying the entire socket, TDP enforcement via Socket RAPL implicitly manages TDC — there is no per-VR current imbalance to protect against. `FUSE_TDC_LIMIT` is expected to be 0 on all NWP SKUs, suppressing RACL entirely. All 5 child TCDs are rejected.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| RACL applicability on NWP | **Disabled** (single VCCIN) | DMR SoC PM HAS, EEPAS |
| FUSE_TDC_LIMIT (NWP expected) | 0 (RACL disabled) | RACL VR TDC HAS |
| FUSE_TDC_LIMIT (DMR dual-VCCIN) | Non-zero (per-die, 1A units) | RACL VR TDC HAS |
| FUSE_TIME_WINDOW | 16-bit, 1 ms units, range 1–5000 ms | RACL VR TDC HAS |
| RACL control loop | RMS-based EWMA → PID → frequency ratio | RACL VR TDC HAS |
| RACL scope | Per-iMH (local), not global | DMR PM HAS |
| CBB frequency resolution | min(RAPL global ceiling, RACL local limit) | HPM spec |
| CHARGE_STATUS format | 18.14 Coulomb, monotonic | RACL VR TDC HAS |
| RACL debug disable | IO_PCODE_SYSTEM_MODES_CONTROL2[9] | DMR PM HAS |
| PEM event ID | 22 (RACL) | PEM telemetry spec |
| PLR bit | 54 (RACL, fine grain) | DMR PLR HAS |
| Security | Same SCA mitigation as RAPL (DRNG fuzzing, 5% error band) | RACL VR TDC HAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram (DMR Reference — Not Active on NWP)

> **Note:** This diagram shows the RACL architecture as implemented on DMR dual-VCCIN platforms. On NWP (single VCCIN), all layers are inactive because `FUSE_TDC_LIMIT = 0`.

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: OOB Observability (BMC / NM / PMT)</strong><br/>
    <small>CHARGE_STATUS via PMT · RACL_PERF_STATUS via PMT · No customer controllability</small><br/>
    <small style="color:#ffd700">⚠️ NWP: counters expected = 0 (RACL disabled)</small>
  </div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PrimeCode RACL PID Control (per-iMH)</strong><br/>
    <small>EWMA filter · RMS² error computation · PID → freq ratio output · HPM 0x14 packing</small><br/>
    <small style="color:#ffd700">⚠️ NWP: PID not initialized (FUSE_TDC_LIMIT = 0)</small>
  </div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: CBB PCode Enforcement</strong><br/>
    <small>RACL_PID_FREQ_OUTPUT → per-CCP freq ceiling · LEAF_PERF_STATUS.RACL_PERF_STATUS counter</small><br/>
    <small style="color:#ffd700">⚠️ NWP: RACL_PID_FREQ_OUTPUT = 0xFF (no limit)</small>
  </div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / HW Telemetry</strong><br/>
    <small>SVID IMON current measurement (shared with RAPL) · FUSE_TDC_LIMIT · FUSE_TIME_WINDOW</small><br/>
    <small style="color:#ffd700">⚠️ NWP: FUSE_TDC_LIMIT = 0 → RACL suppressed at fuse level</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L4: OOB Observability | ❌ | ❌ | ❌ | ❌ | ❌ | RACL disabled on NWP — counters = 0. No validation needed |
| L3: PrimeCode RACL PID | ❌ | ❌ | ❌ | ❌ | ❌ | PID not initialized — fuse-gated suppression. No validation needed |
| L2: CBB PCode Enforcement | ❌ | ❌ | ❌ | ❌ | ❌ | RACL_PID_FREQ_OUTPUT = 0xFF. No enforcement. No validation needed |
| L1: Silicon / HW Telemetry | ❌ | ❌ | ❌ | ✅ | ❌ | **Fuse verification only**: confirm FUSE_TDC_LIMIT = 0 on NWP silicon |

> **Single active validation point:** FV fuse read to confirm RACL is properly disabled. All other layers are inactive by design.

### RACL Architecture (DMR Dual-VCCIN Reference)

```
                    DMR Dual-VCCIN Topology (RACL Active)
                    ════════════════════════════════════

  North iMH (Root)                     South iMH (Leaf)
  ├── VCCIN_0 VR                       ├── VCCIN_1 VR
  │   └── SVID IMON ─┐                │   └── SVID IMON ─┐
  │                   ▼                │                   ▼
  │   RACL PID (local)                 │   RACL PID (local)
  │   ├── TDC² - IMON² → EWMA         │   ├── TDC² - IMON² → EWMA
  │   └── PID → freq ratio            │   └── PID → freq ratio
  │                   │                │                   │
  │   min(RAPL, RACL) │                │   min(RAPL, RACL) │
  │                   ▼                │                   ▼
  ├── CBB0 ← RAPL_PERF_LIMIT HPM      ├── CBB2 ← local limit
  └── CBB1 ← (RACL_PID_FREQ_OUTPUT)   └── CBB3 ← (RACL_PID_FREQ_OUTPUT)


                    NWP Single-VCCIN Topology (RACL Disabled)
                    ═════════════════════════════════════════

  NIO Root Die (single VCCIN)
  ├── VCCIN VR (single rail)
  │   └── SVID IMON → used by Socket RAPL only
  │
  │   FUSE_TDC_LIMIT = 0 → RACL PID NOT INITIALIZED
  │   RACL_PID_FREQ_OUTPUT = 0xFF (no limit)
  │
  ├── CBB0 ← Socket RAPL only (CLOS_LIMITS)
  └── CBB1 ← Socket RAPL only (CLOS_LIMITS)
```

### RACL Control Loop (DMR Reference)

```
VCCIN_VR_IMON (from SVID) → (IMON)² → [TDC² - IMON²] → EWMA filter → PID Controller → Frequency Ratio Output
                                                              ↑
                                                    FUSE_TDC_LIMIT² (target)

On NWP: FUSE_TDC_LIMIT = 0 → entire pipeline is skipped
```

### Interface & Register Matrix

| Register / Parameter | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | HPM | NWP State |
|---|---|---|---|---|---|---|---|
| FUSE_TDC_LIMIT | — | — | — | — | RO (per-die) | — | **= 0** (disabled) |
| FUSE_TIME_WINDOW | — | — | — | — | RO (per-die) | — | N/A (unused) |
| CHARGE_STATUS | — | — | PMT (RO_V) | — | — | — | = 0 (no RACL accounting) |
| RACL_PERF_STATUS | — | — | PMT (RO_V) | — | — | — | = 0 (no throttling) |
| PLR bit 54 (RACL) | — | RW0C | RW0C | — | — | PLR_MAILBOX | = 0 (never asserted) |
| PEM event 22 (RACL) | — | — | PMT | — | — | — | Not fired |
| RACL_PID_FREQ_OUTPUT | — | — | — | — | — | HPM 0x14 | = 0xFF (no limit) |
| RAPL_PERF_LIMIT HPM | — | — | — | — | — | HPM 0x14 | RACL field transparent |
| LEAF_PERF_STATUS.RACL | — | — | — | — | — | HPM 0x16 | = 0 (no modules limited) |
| IO_PCODE_SYSTEM_MODES_CONTROL2[9] | — | — | — | RW | — | — | N/A (debug disable moot) |

### Observability

| Observable | Type | Tool / Command | What it shows | NWP Expected |
|---|---|---|---|---|
| FUSE_TDC_LIMIT | Fuse | PythonSV fuse read | TDC limit per iMH (1A units) | **0** (disabled) |
| CHARGE_STATUS | PMT counter | OOB-MSM / PMT read | Accumulated charge (18.14 Coulomb) | 0 |
| RACL_PERF_STATUS | PMT counter | OOB-MSM / PMT read | Accumulated RACL throttle time | 0 |
| PLR bit 54 | TPMI | PythonSV PLR read | RACL limiting active | 0 |
| PEM event 22 | Telemetry | PEM trace | RACL throttle event | Not fired |
| HPM RACL_PID_FREQ_OUTPUT | HPM message | HPM trace / PrimeCode trace | RACL PID frequency limit | 0xFF |

### SKU / Config Distinctions

| SKU / Config | RACL Behavior | Reason |
|---|---|---|
| DMR-AP (dual VCCIN) | **Active** — per-iMH RACL PID runs, TDC enforced | Two independent VRs with independent TDC limits |
| DMR-SP (single VCCIN) | **Disabled** — FUSE_TDC_LIMIT = 0 | Single VR, same as NWP |
| NWP (single VCCIN, single NIO) | **Disabled** — FUSE_TDC_LIMIT = 0 | Single VR, single die — RAPL manages TDC implicitly |
| GNR (single VCCIN) | **Disabled** — no RACL feature | Pre-RACL generation |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| PrimeCode RACL PID | `src/flow/racl/v1_0/racl.cpp` / `racl.hpp` |
| PrimeCode HPM root packing | `src/flow/rapl/rapl_messaging/rapl_hpm_root/v2_0/rapl_hpm_root.cpp` |
| PrimeCode RAPL bridge (perf status) | `src/flow/rapl/rapl_bridge/v2_0/rapl_bridge_common.cpp` |
| CBB PCode RACL enforcement | `source/pcode/flows/slow_limits/rapl/rapl.cpp` |
| CBB PCode CFC (mesh limiting) | `src/ip/cfc/v2_0/cfc.cpp` |
| Fuse definitions | `src/flow/racl/v1_0/fuses_racl.xml` |
| HPM mailbox definitions | `src/flow/hpm/hpm_common/v2_0/hpm_mailbox.xml` |

---

## Section 3: Validation Strategy

**NWP RACL is rejected (ZBB)** — all five child TCDs are rejected because RACL is architecturally inapplicable on NWP's single-VCCIN topology.

The **sole remaining validation obligation** is fuse verification: confirming that `FUSE_TDC_LIMIT = 0` on NWP silicon to prove RACL is properly suppressed. This is covered by the Socket RAPL TPF's fuse-verification TCD, not by a dedicated RACL TCD.

> Layer coverage is mapped in §2 — the Validation-Tier Layer Claim table shows all layers except L1 (fuse verification) are unclaimed, which is correct because the feature is architecturally disabled.

### Tier Definitions

| Tier | Environment | Interface | RACL Relevance on NWP |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → model | N/A — RACL model would show disabled state only |
| PSS — HSLE | Single-die RTL | PythonSV → RTL | N/A — RACL fuse = 0 in RTL |
| PSS — XOS | Both-die RTL | PythonSV → full RTL | N/A — no dual-VCCIN to exercise |
| FV | Post-silicon NWP | PythonSV → namednodes | **Fuse verification only**: confirm FUSE_TDC_LIMIT = 0 |
| PV | Post-silicon NWP + Ubuntu | OS tools | N/A — no RACL observability exposed to OS |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | NWP Applicability |
|---|---|---|---|---|---|---|
| RACL PID algorithm bug | ❌ | ❌ | ❌ | ❌ | ❌ | N/A — PID not initialized |
| RACL fuse not properly suppressed | ❌ | ❌ | ❌ | ✅ | ❌ | **Only applicable bug class** |
| RACL cross-product with Socket RAPL | ❌ | ❌ | ❌ | ❌ | ❌ | N/A — RACL transparent (0xFF) |
| RACL security/fuzzing leak | ❌ | ❌ | ❌ | ❌ | ❌ | N/A — no RACL counters active |
| RACL HPM message error | ❌ | ❌ | ❌ | ❌ | ❌ | N/A — RACL field = 0xFF passthrough |
| Per-VR current imbalance | ❌ | ❌ | ❌ | ❌ | ❌ | N/A — single VCCIN, no imbalance possible |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| FUSE_TDC_LIMIT = 0 verification | ❌ | ✅ | ❌ | Confirms RACL fuse-level suppression on real silicon |
| RACL observability counters = 0 | ❌ | ✅ | ❌ | Confirms no spurious RACL activity |
| Socket RAPL operates as sole limiter | ✅ | ✅ | ✅ | Covered by Socket RAPL TPF — not RACL TPF scope |

---

## Section 5: Risks & Dependencies

### Active Risks

- **Risk: FUSE_TDC_LIMIT non-zero on NWP SKU** — If a manufacturing or fuse-programming error sets FUSE_TDC_LIMIT to a non-zero value on NWP, RACL PID would initialize unexpectedly and could throttle frequency without a valid TDC reference. **Mitigation:** FV fuse verification (covered by Socket RAPL TPF fuse TCD).

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | RACL PID algorithm correctness on NWP | None (feature disabled) | RACL PID requires dual VCCIN + non-zero TDC fuse. NWP has single VCCIN — algorithm cannot be exercised. Covered on DMR dual-VCCIN platforms |
| **G-2** | RACL cross-product with Socket RAPL on NWP | None (RACL transparent) | RACL_PID_FREQ_OUTPUT = 0xFF means CBB PCode only sees RAPL ceiling. Cross-product is architecturally moot |
| **G-3** | RACL security/fuzzing on NWP | None (no counters active) | DRNG fuzzing only applies to non-zero CHARGE_STATUS. With RACL disabled, counters = 0 — no SCA surface |
| **G-4** | RACL HPM message integrity on NWP | None (field = 0xFF) | RACL_PID_FREQ_OUTPUT is a passthrough value. HPM message integrity is validated by Socket RAPL HPM TCD |
| **G-5** | Per-VR asymmetric load testing | None (single VR) | NWP has one VCCIN — asymmetric loading across VRs is physically impossible |

---

## Section 6: DFX Considerations

- **RACL debug disable (IO_PCODE_SYSTEM_MODES_CONTROL2[9])**: Not applicable on NWP — RACL is already fuse-disabled. The debug disable bit is only relevant on DMR dual-VCCIN platforms where RACL is active.
- **PrimeCode trace**: RACL flow trace points exist in PrimeCode but will show "RACL disabled" path on NWP. No DFx action needed.
- **PMT counters**: CHARGE_STATUS and RACL_PERF_STATUS are architecturally present but read as 0. No special DFx handling required.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior on NWP |
|---|---|---|
| FUSE_TDC_LIMIT = 0 (nominal NWP) | All 5 TCDs (rejected) | RACL PID not initialized, all counters = 0, 0xFF in HPM |
| FUSE_TDC_LIMIT accidentally non-zero | All 5 TCDs | RACL PID would initialize with invalid TDC reference — potential spurious throttling. This is a fuse-programming defect, not a RACL bug |
| PBM disabled + RACL | N/A | On DMR: RACL continues even with PBM off. On NWP: moot (RACL disabled) |
| Socket RAPL throttling without RACL | Socket RAPL TCDs | RAPL operates normally as sole package-level limiter. RACL_PID_FREQ_OUTPUT = 0xFF is transparent to RAPL resolution |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | Owner | Segment |
|---|---|---|---|---|
| [22022420737](https://hsdes.intel.com/appstore/article-one/#/22022420737) | RACL Counters Verification | rejected (ZBB) | mps | FV |
| [22022420741](https://hsdes.intel.com/appstore/article-one/#/22022420741) | RACL Cross Product | rejected (ZBB) | mps | FV |
| [22022420746](https://hsdes.intel.com/appstore/article-one/#/22022420746) | RACL Fuses Verification | rejected (ZBB) | mps | FV |
| [22022420749](https://hsdes.intel.com/appstore/article-one/#/22022420749) | RACL HPM Verification | rejected (ZBB) | mps | FV |
| [22022420753](https://hsdes.intel.com/appstore/article-one/#/22022420753) | RACL Security | rejected (ZBB) | mps | FV |

### References

| Type | Link | Notes |
|------|------|-------|
| RACL HAS | [RACL VR TDC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html) | Primary spec — dual VCCIN, control loop, fuses, observability |
| RACL Data | [RACL_sheets.xlsx](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/embeddings/RACL_sheets.xlsx) | Fuse definitions, register tables |
| HPM Spec | [RAPL_PERF_LIMIT HPM](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#RAPL_PERF_LIMIT) | RACL_PID_FREQ_OUTPUT field |
| DMR SoC PM HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | Single-VCCIN impact table — RACL suppression |
| EEPAS | [EEPAS](https://docs.intel.com/documents/server-platform-arch/Power%20Management/EEPAS.html) | Single VCCIN → RACL not required |
| Primecode RACL FHAS | [RACL FHAS](https://docs.intel.com/documents/primecode/fhas/DMR/RACL/SERVERPMFW-154.html) | Primecode RACL fuse/flow spec |
| Fabric DVFS | [RACL/RAPL Limits for Fabric](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Fabric_DVFS.html#raplracl-limits-for-imh-memory-io-fabric-frequencies) | RACL → fabric freq reduction (DMR only) |
| PLR HAS | [DMR PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) | PLR bit 54 = RACL |
| KB Feature Article | [racl.md](../../pm_features/power_rapl/racl.md) | Full RACL KB with NWP delta |
| Socket RAPL KB | [socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) | RAPL is global; RACL is local per-iMH |
| Parent TPF (Socket RAPL) | [TPF 15019477653](https://hsdes.intel.com/appstore/article-one/#/15019477653) | Active TPF — RAPL is the sole NWP package limiter |

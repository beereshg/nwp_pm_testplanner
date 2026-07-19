# TPF 15019477948 — [NWP PM] SIMPL / DFC (Dynamic Frequency Control)

| Field | Value |
|-------|-------|
| **TPF ID** | [15019477948](https://hsdes.intel.com/appstore/article-one/#/15019477948) |
| **Title** | [NWP PM] SIMPL / DFC (Dynamic Frequency Control) |
| **Parent TP** | [15019477845 — [NWP PM] Power Control (SIMPL/PMAX/SVID)](https://hsdes.intel.com/appstore/article-one/#/15019477845) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**SIMPL (Simple IccMax/Power Limit)** is a **firmware-heavy feature with fuse-backed hardware support**. SIMPL is a SoC-wide proactive IccMax and frequency management scheme that extends DFC (Dynamic Frequency Control) to multiple domains (core, ring, memory, IO). DFC dynamically trades off maximum allowed core frequency versus ring/CFC frequency to stay within a given IccMax budget — when CCF demand is high, DFC allows higher ring frequency by reducing core frequency, and vice versa.

**Feature gating:** SIMPL policies are fuse-programmed (up to 4 SKU-dependent policies). DFC is enabled per CBB die via `SIMPL_CBB_DFC_EN` fuse. BIOS can override policy selection and force DFC mode via `SIMPL_DFC_CONTROL` register.

**NWP delta from DMR:** NWP inherits the DMR SIMPL/DFC architecture with Newport-specific fuse maps. No PQC payloads in NWP mailbox protocol (reserved fields). `SIMPL_CBB_DFC_EN` fuse and DFC offset bins are implemented per CBB die.

### Feature-Specific Constants

| Parameter | Value | Source |
|-----------|-------|--------|
| Max SIMPL policies | 4 (SKU-dependent) | NWP PM HAS |
| DFC modes | 4: Disabled, CFC Clipped, Core Clipped, Dynamic | NWP PM HAS |
| Domains managed | Core, Ring/CFC | NWP PM HAS |
| Control register | SIMPL_DFC_CONTROL (64b, RW via TPMI) | NWP PM HAS |
| Status register | SIMPL_DFC_STATUS (64b, RO via TPMI) | NWP PM HAS |
| DFC offset bin granularity | Frequency bins (per policy, per domain) | NWP PM HAS |
| CBB dies with DFC | cbb0, cbb1 | NWP topology |
| PQC payloads | Not supported on NWP (reserved) | NWP PM HAS |
| Register root | TPMI-accessible via PythonSV | NWP register map |

---

## Section 2: Design Details

### SIMPL/DFC — Full Stack (Policy Selection to Frequency Enforcement)

<!-- raw-html -->
<div style="max-width:680px;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;margin:16px 0;">

  <!-- OS / Tool Layer -->
  <div style="background:#e8f4fd;border:2px solid #2196f3;border-radius:8px 8px 0 0;padding:12px 18px;">
    <div style="font-weight:700;color:#1565c0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 5: OS / Tool</div>
    <div style="color:#1a237e;line-height:1.7;font-size:11.5px;">
      <code style="background:#fff;border:1px solid #90caf9;border-radius:3px;padding:1px 5px;">intel-speed-select</code> &nbsp;·&nbsp;
      <code style="background:#fff;border:1px solid #90caf9;border-radius:3px;padding:1px 5px;">cpufreq / scaling_max_freq</code> &nbsp;·&nbsp;
      TPMI sysfs interface for SIMPL status readback
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- BIOS Configuration Layer -->
  <div style="background:#fce4ec;border:2px solid #e91e63;padding:12px 18px;">
    <div style="font-weight:700;color:#880e4f;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 4: BIOS Configuration</div>
    <div style="color:#880e4f;line-height:1.8;font-size:11.5px;">
      Policy override knobs: min/max policy override &nbsp;·&nbsp;
      DFC mode force: disabled / CFC clipped / core clipped / dynamic &nbsp;·&nbsp;
      Can disable SIMPL entirely by setting min=max policy override
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Firmware Policy Layer -->
  <div style="background:#fff3e0;border:2px solid #ff9800;padding:12px 18px;">
    <div style="font-weight:700;color:#e65100;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 3: Firmware Policy &nbsp;<span style="font-weight:400;font-size:10px;color:#bf360c;">(PCode / PrimeCode)</span></div>
    <div style="color:#bf360c;line-height:1.8;font-size:11.5px;">
      PCode reads SIMPL policy + DFC mode from fuses and <code style="background:#fff;border:1px solid #ffcc80;border-radius:3px;padding:1px 5px;">SIMPL_DFC_CONTROL</code><br>
      Based on workload telemetry (core/ring utilization, Cdyn) → decides which domain to prioritize<br>
      Sets frequency ceilings → communicates to FIVR and local DVFS via mailbox + internal paths
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- FIVR / DVFS Layer -->
  <div style="background:#f3e5f5;border:2px solid #9c27b0;padding:12px 18px;">
    <div style="font-weight:700;color:#6a1b9a;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 2: FIVR / DVFS Enforcement</div>
    <div style="color:#4a148c;line-height:1.8;font-size:11.5px;">
      Receives frequency requests from PCode based on SIMPL/DFC policy &nbsp;·&nbsp;
      Sets voltage and frequency for each domain (core, ring) per clipped limits &nbsp;·&nbsp;
      DFC active → reduced freq request for clipped domain
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Silicon / Fuse Layer -->
  <div style="background:#e8f5e9;border:2px solid #4caf50;border-radius:0 0 8px 8px;padding:12px 18px;">
    <div style="font-weight:700;color:#2e7d32;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 1: Silicon / Fuse</div>
    <div style="color:#1b5e20;line-height:1.8;font-size:11.5px;">
      Fuses program: policy count, max freq per domain/Cdyn level, DFC enable, offset bins, min active cores &nbsp;·&nbsp;
      <code style="background:#fff;border:1px solid #a5d6a7;border-radius:3px;padding:1px 5px;">SIMPL_CBB_DFC_EN</code> fuse per CBB die
    </div>
  </div>

</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | FV | PV | Notes |
|---|---|---|---|---|---|
| OS / Tool | ❌ | ❌ | ❌ | ✅ | Requires booted OS + isst tooling |
| BIOS Configuration | ✅ | ❌ | ✅ | ✅ | VP safe for BIOS override testing |
| Firmware Policy | ✅ | ✅ | ✅ | indirect | All tiers validate PCode logic |
| FIVR / DVFS Enforcement | ❌ | ⚠️ | ✅ | indirect | HSLE partial (RTL DVFS model) |
| Silicon / Fuse | ❌ | ❌ | ✅ | ❌ | Real fuses required |

### DFC Mode Decision Flow

```
PCode boot:
    Read SIMPL_CBB_DFC_EN fuse per CBB
    Read policy count from fuses → populate SIMPL_DFC_STATUS.NUM_POLICIES
    Read SIMPL_DFC_CONTROL for BIOS overrides
    │
    ├── DFC mode = Disabled (00)
    │      └── Both core and ring run at max allowed frequency per SIMPL policy
    │
    ├── DFC mode = CFC Clipped (01)
    │      └── Ring/CFC frequency always clipped by DFC offset bins
    │      └── Core frequency allowed full P0n
    │
    ├── DFC mode = Core Clipped (10)
    │      └── Core frequency always clipped by DFC offset bins
    │      └── Ring frequency allowed full P0n
    │
    └── DFC mode = Dynamic (11)
           └── PCode monitors core C0 residency + ring bandwidth
           └── Dynamically switches which domain is clipped
           └── High ring demand → clip core, allow higher ring
           └── High core demand → clip ring, allow higher core
```

### NWP vs DMR SIMPL/DFC Differences

| Aspect | NWP Newport | DMR |
|--------|-------------|-----|
| SIMPL architecture | Inherited from DMR | Baseline |
| PQC payloads | Not supported (reserved) | Supported |
| DFC fuse (SIMPL_CBB_DFC_EN) | Per CBB die (cbb0, cbb1) | Per CBB die |
| Default policy/fuse values | NWP-specific SKU values | DMR-specific SKU values |
| Policy count | Up to 4 (SKU-dependent) | Up to 4 (SKU-dependent) |

### Interface & Register Matrix

| Register / MSR | Field | Width | Default | Feature effect | Tier validated |
|---|---|---|---|---|---|
| SIMPL_DFC_CONTROL | SIMPL_MAX_POLICY_OVRD | [3:0] | 0 | Maximum policy override | FV, PSS |
| SIMPL_DFC_CONTROL | SIMPL_MIN_POLICY_OVRD | [11:8] | 0 | Minimum policy override | FV, PSS |
| SIMPL_DFC_CONTROL | SIMPL_CBB_DFC_Mode | [17:16] | 00 | DFC mode: 00=disabled, 01=CFC clip, 10=core clip, 11=dynamic | FV, PSS |
| SIMPL_DFC_STATUS | SIMPL_NUM_POLICIES | [3:0] | Fuse | Number of available policies | FV |
| SIMPL_DFC_STATUS | SIMPL_CURRENT_POLICY | [11:8] | 0 | Currently active policy index | FV |
| SIMPL_DFC_STATUS | SIMPL_CBB_DFC_STATUS | [16] | 0 | Resolved DFC enable (fuse + override) | FV |
| Per-policy fuse | max_freq_core[policy][cdyn] | — | Fuse | Core freq limit per policy per Cdyn level | FV |
| Per-policy fuse | max_freq_ring[policy][cdyn] | — | Fuse | Ring freq limit per policy per Cdyn level | FV |
| Per-policy fuse | dfc_offset_bins | — | Fuse | Frequency bins to reduce when other domain prioritized | FV |
| SIMPL_CBB_DFC_EN fuse | enable | 1b | Fuse | Per-CBB DFC enable | FV |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| SIMPL_DFC_STATUS | Register | PythonSV TPMI read | Current policy, DFC enable, policy count |
| SIMPL_DFC_CONTROL | Register | PythonSV TPMI read | Active overrides and DFC mode |
| Core resolved frequency | Telemetry | PythonSV: `sv.socket0.cbb0.compute0.module0.resolved_freq.read()` | Actual core frequency (verify clipping) |
| Ring resolved frequency | Telemetry | PythonSV: ring freq telemetry register | Actual ring/CFC frequency |
| PCode DVFS/FIVR requests | Firmware trace | fw_runtime_tracker log | Frequency request flow from PCode |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| High core-count SKU | More policies available; DFC more impactful | All SIMPL/DFC TCDs |
| DFC fuse disabled | SIMPL runs without DFC tradeoff; ring/core independent | DFC-specific TCDs |
| BIOS min=max policy override | Effectively disables SIMPL | SIMPL policy TCDs |
| Single-CBB config | DFC per-CBB; behavior may differ from 2-CBB | Cross-CBB coordination TCD |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| BIOS configuration | BIOS knobs: policy override, DFC mode force |
| PCode / PrimeCode | `src/flow/simpl/` — SIMPL policy engine, DFC decision logic |
| FIVR / DVFS | Internal DVFS/FIVR paths — frequency enforcement |
| Fuse infrastructure | SIMPL policy fuses, SIMPL_CBB_DFC_EN per CBB |

---

## Section 3: Validation Strategy

Three-tier validation is required because SIMPL/DFC spans firmware policy (modelable in PSS), FIVR frequency enforcement (partially modelable), and fuse-backed silicon configuration (real silicon required).

> **Layer coverage:** See §2 — Validation-Tier Layer Claim table for which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | Firmware policy logic, BIOS override handling, DFC mode switching |
| PSS — HSLE | Single-die RTL (CBB) | PythonSV → DVFS RTL | DVFS frequency clipping response to PCode requests |
| FV | Post-silicon NWP | PythonSV → namednodes | Real fuse-backed policy, real FIVR/DVFS, real frequency tradeoff |
| PV | Post-silicon NWP + OS | intel-speed-select, cpufreq | OS-visible frequency behavior, isst tool integration |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | FV | PV |
|---|---|---|---|---|
| Firmware policy selection error | ✅ | ⚠️ | ✅ | indirect |
| DFC mode switching logic bug | ✅ | ⚠️ | ✅ | indirect |
| BIOS override out-of-range (min > max) | ✅ safe | ❌ | ✅ | ❌ |
| Fuse mismatch (policy count vs actual) | ❌ | ❌ | ✅ | indirect |
| DFC heuristic misprediction | ❌ | ❌ | ✅ | ✅ |
| FIVR frequency enforcement error | ❌ | ⚠️ | ✅ | indirect |
| Ring/core frequency inversion | ❌ | ❌ | ✅ | ✅ |
| OS/driver policy readback error | ❌ | ❌ | ❌ | ✅ |
| DFC toggle jitter (rapid enable/disable) | ❌ | ❌ | ✅ | ❌ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| Policy selection and override | ✅ | ✅ | ❌ | Firmware config validation |
| DFC mode force (all 4 modes) | ✅ | ✅ | ❌ | Verify each mode behavior |
| Dynamic DFC core↔ring switching | ❌ | ✅ | ✅ | Real workload variation |
| SIMPL disable (min=max override) | ✅ | ✅ | ❌ | Verify SIMPL bypass |
| Fuse readback and policy count | ❌ | ❌ | ✅ | Real fuse validation |
| DFC offset bin frequency reduction | ❌ | ✅ | ❌ | Verify exact frequency clip |
| Cross-CBB DFC coordination | ❌ | ✅ | ❌ | Multi-die coordination |
| OS isst tool SIMPL status readback | ❌ | ❌ | ✅ | E2E tool integration |

---

## Section 5: Risks & Dependencies

### Active Risks

- **DFC heuristic accuracy:** Dynamic mode relies on workload heuristics (core C0 residency, ring bandwidth) — misprediction causes suboptimal performance. Requires characterization across workloads.
- **Policy override boundary:** If BIOS sets min > max policy override, SIMPL is disabled — must be handled gracefully by PCode. Risk of silent feature disablement.
- **DFC toggling jitter:** Rapid active core count changes near the DFC enable threshold can cause frequent mode switching and performance instability.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Real workload heuristic convergence | FV + PV | Requires sustained varied workloads; PSS models approximate at best |
| **G-2** | Fuse-backed policy content validation | FV only | Real fuses required; cannot model fuse content pre-Si |
| **G-3** | OS isst tool integration | PV only | Requires booted Linux + driver stack |

---

## Section 6: DFX Considerations

- **SIMPL_DFC_STATUS register:** Read-only register provides current policy, DFC enable status, and policy count for debug and validation.
- **DFC mode observable:** SIMPL_CBB_DFC_Mode field readable to verify BIOS override took effect.
- **Frequency telemetry:** Core and ring resolved frequencies observable via PythonSV for verifying DFC clipping.
- **PCode firmware trace:** fw_runtime_tracker log captures SIMPL policy decisions and DFC mode transitions for post-mortem analysis.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| BIOS min > max policy override | SIMPL policy TCD | SIMPL disabled; PCode defaults to no clipping |
| DFC mode forced to Dynamic with single active core | DFC mode TCD | DFC should not activate (below min active core threshold) |
| Policy count fuse = 0 | SIMPL policy TCD | Feature disabled; PCode uses default freq limits |
| DFC enable fuse = 0 on one CBB, = 1 on other | Cross-CBB TCD | Asymmetric behavior: one CBB has DFC, other does not |
| Rapid workload transition (core → ring bound) | DFC dynamic TCD | DFC switches clipping domain; verify no freq discontinuity |
| All cores in C1/C6 (zero active cores) | DFC idle TCD | DFC should be inactive; no clipping applied |
| SIMPL policy switch during active RAPL PID loop | RAPL interaction TCD | SIMPL policy and RAPL must converge without oscillation |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

*No TCDs currently defined under this TPF. TCD creation is pending.*

### References

- [NWP PM HAS — SIMPL / DFC section](https://hsdes.intel.com/appstore/article-one/#/15019477948) — feature specification
- [NWP PM MAS — Power Control chapter](https://hsdes.intel.com/appstore/article-one/#/15019477845) — parent TP
- [DMR PM HAS — SIMPL (baseline reference)](https://hsdes.intel.com/appstore/article-one/#/) — DMR baseline for SIMPL/DFC

# TPF 15019477947 — [NWP PM] PMAX (Maximum Power Protection)

| Field | Value |
|-------|-------|
| **TPF ID** | [15019477947](https://hsdes.intel.com/appstore/article-one/#/15019477947) |
| **Title** | [NWP PM] PMAX (Maximum Power Protection) |
| **Parent TP** | [15019477845 — [NWP PM] Power Control (SIMPL/PMAX/SVID)](https://hsdes.intel.com/appstore/article-one/#/15019477845) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**PMAX (Maximum Power Protection)** is a **silicon-heavy feature with firmware coordination**. Multi-Threshold PMax (MT-PMax) is an on-die analog overcurrent/overvoltage protection circuit that senses FIVR input VccIN voltage and triggers immediate frequency throttle before hardware damage occurs. PCode/PrimeCode configures thresholds and handles masking during deep C-states; hardware enforces the throttle response autonomously at sub-microsecond timescales.

**Feature gating:** PMAX is always enabled on NWP production parts (fuse-controlled thresholds). BIOS can adjust the hard-throttle trip threshold or disable PMAX for overclocking platforms. GPIO PMAX_TRIGGER_IO mode is BIOS-configurable (RX/TX/disabled).

**NWP delta from DMR:** Single VCCIN domain on NIO (imh0) — DMR-AP has dual VCCIN domains with PMAX detectors on both IMH dies. NWP drives D2D fast-throttle wire from imh0 to both cbb0 and cbb1; no cross-die HPM messaging needed.

### Feature-Specific Constants

| Parameter | Value | Source |
|-----------|-------|--------|
| VCCIN domains | 1 (imh0 / NIO die) | NWP HAS |
| PMAX detector location | imh0 only | NWP HAS |
| CBBs receiving throttle | 2 (cbb0 + cbb1) | NWP topology |
| Throttle levels | 4: Vtrip0 (soft), Vtrip1 (soft), Vtrip2 (hard), Vtrip3/FDP | NWP PM HAS |
| Hard throttle target | Psafe frequency | NWP PM HAS |
| Hard throttle response | <50 ns power reduction via D2D wire | NWP PM HAS |
| Trip encoding granularity | 1 code = 2 mV VccIN | NWP PM HAS |
| Valid trip encodings | 001, 011, 111 only | NWP PM HAS |
| D2D fast-throttle wires | YY_FAST_THROTTLE_IN_0 (hard), YY_FAST_THROTTLE_IN_1 (PWM/soft) | NWP PM HAS |
| Register root | sv.socket0.nio.punit.* | NWP register map |

---

## Section 2: Design Details

### PMAX Protection — Full Stack (Detection to Throttle Enforcement)

<!-- raw-html -->
<div style="max-width:680px;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;margin:16px 0;">

  <!-- Platform / VR Layer -->
  <div style="background:#e8f4fd;border:2px solid #2196f3;border-radius:8px 8px 0 0;padding:12px 18px;">
    <div style="font-weight:700;color:#1565c0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 5: Platform / VR</div>
    <div style="color:#1a237e;line-height:1.7;font-size:11.5px;">
      MBVR (motherboard voltage regulator) delivers VCCIN &nbsp;·&nbsp;
      Platform loadline determines IccIN↔VccIN mapping &nbsp;·&nbsp;
      GPIO <code style="background:#fff;border:1px solid #90caf9;border-radius:3px;padding:1px 5px;">PMAX_TRIGGER_IO</code> (external observe/inject)
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Firmware Policy Layer -->
  <div style="background:#fff3e0;border:2px solid #ff9800;padding:12px 18px;">
    <div style="font-weight:700;color:#e65100;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 4: Firmware Policy &nbsp;<span style="font-weight:400;font-size:10px;color:#bf360c;">(PCode / PrimeCode)</span></div>
    <div style="color:#bf360c;line-height:1.8;font-size:11.5px;">
      PCode configures trip thresholds via <code style="background:#fff;border:1px solid #ffcc80;border-radius:3px;padding:1px 5px;">PMAX_CONTROL</code> &nbsp;·&nbsp;
      Masks PMAX during PkgC6 entry &nbsp;·&nbsp;
      Dynamic IccMax adjustment via <code style="background:#fff;border:1px solid #ffcc80;border-radius:3px;padding:1px 5px;">ICCMAX_CONFIG</code> &nbsp;·&nbsp;
      Clears/resets throttle events
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Detection Layer -->
  <div style="background:#f3e5f5;border:2px solid #9c27b0;padding:12px 18px;">
    <div style="font-weight:700;color:#6a1b9a;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 3: Analog Detection &nbsp;<span style="font-weight:400;font-size:10px;color:#4a148c;">(imh0 PMAX IP)</span></div>
    <div style="color:#4a148c;line-height:1.8;font-size:11.5px;">
      On-die analog detector senses VccIN &nbsp;·&nbsp;
      Compares against 3 fuse-programmable thresholds (Vtrip0/1/2) + FDP (Vtrip3)<br>
      Vtrip0/1 → soft/proportional throttle &nbsp;·&nbsp; Vtrip2 → hard throttle &nbsp;·&nbsp; Vtrip3 → fast droop protection
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- D2D Signaling Layer -->
  <div style="background:#e8f5e9;border:2px solid #4caf50;padding:12px 18px;">
    <div style="font-weight:700;color:#2e7d32;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 2: D2D Throttle Signaling &nbsp;<span style="font-weight:400;font-size:10px;color:#1b5e20;">(imh0 → cbb0/cbb1)</span></div>
    <div style="color:#1b5e20;line-height:1.8;font-size:11.5px;">
      <code style="background:#fff;border:1px solid #a5d6a7;border-radius:3px;padding:1px 5px;">YY_FAST_THROTTLE_IN_0</code> — hard throttle wire (~50 ns) &nbsp;·&nbsp;
      <code style="background:#fff;border:1px solid #a5d6a7;border-radius:3px;padding:1px 5px;">YY_FAST_THROTTLE_IN_1</code> — PWM proportional throttle
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Core Throttle Enforcement Layer -->
  <div style="background:#ffebee;border:2px solid #f44336;border-radius:0 0 8px 8px;padding:12px 18px;">
    <div style="font-weight:700;color:#c62828;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 1: Core Throttle Enforcement &nbsp;<span style="font-weight:400;font-size:10px;color:#b71c1c;">(CBB Acode / DVFS)</span></div>
    <div style="color:#b71c1c;line-height:1.8;font-size:11.5px;">
      Hard throttle → immediate frequency drop to Psafe &nbsp;·&nbsp;
      Soft throttle → PWM proportional frequency reduction &nbsp;·&nbsp;
      FDP → fast-path frequency clamp within first droop time constant
    </div>
  </div>

</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | FV | PV | Notes |
|---|---|---|---|---|---|
| Platform / VR | ❌ | ❌ | ✅ | ✅ | Requires real VR and loadline |
| Firmware Policy | ✅ | ✅ | ✅ | ❌ | PCode threshold config validated all tiers |
| Analog Detection | ❌ | ⚠️ | ✅ | ❌ | RTL model partial; real silicon required |
| D2D Throttle Signaling | ❌ | ❌ | ✅ | ❌ | Real D2D wire required |
| Core Throttle Enforcement | ⚠️ | ✅ | ✅ | indirect | HSLE validates Acode response; PV observes freq |

### PMAX Event Flow (Detection to Recovery)

```
VccIN droops below Vtrip threshold
    │
    ├── Vtrip0/1: soft throttle path
    │      └── PWM signal via YY_FAST_THROTTLE_IN_1 → proportional freq reduction
    │
    ├── Vtrip2: hard throttle path
    │      └── D2D wire YY_FAST_THROTTLE_IN_0 asserted (~50 ns)
    │      └── cbb0/cbb1 Acode → immediate drop to Psafe frequency
    │
    └── Vtrip3/FDP: fast droop protection
           └── Direct signal to core throttle logic
           └── Frequency clamp within first droop time constant (ns)

Recovery:
    VccIN recovers above threshold
    └── PCode clears throttle event status
    └── Frequency ramps back up per DVFS policy
```

### NWP vs DMR PMAX Topology

| Aspect | NWP Newport (NIO) | DMR-AP |
|--------|-------------------|--------|
| VCCIN domains | Single (imh0) | Dual (IMH0, IMH1) |
| PMAX detector | imh0 only | Both IMH dies |
| D2D throttle signaling | imh0 → cbb0 + cbb1 | Each IMH → local CBBs |
| Cross-die coordination | Not needed | HPM messaging between IMH0/IMH1 |
| Trip levels | 3 soft + 1 FDP | 3 soft + 1 FDP |
| GPIO observability | PMAX_TRIGGER_IO (bi-dir, BIOS) | PMAX_TRIGGER_IO |

### Interface & Register Matrix

| Register / MSR | Field | Default | Feature effect | Tier validated |
|---|---|---|---|---|
| PMAX_CONTROL (imh0) | trip_threshold[2:0] | Fuse | Programs Vtrip0/1/2 thresholds | FV, PSS |
| PMAX_CONTROL (imh0) | pmax_enable | 1 | Master enable for PMAX detection | FV, PSS |
| PMAX_CONTROL (imh0) | mask_output | 0 | Masks PMAX output (used during PkgC6) | FV, PSS |
| ICCMAX_CONFIG | iccmax_reduction | 0 | Dynamic IccMax adjustment changes effective trip | FV |
| PMAX_TRIGGER_IO GPIO | mode[1:0] | RX | RX=platform-driven, TX=DFX observe, 00=disabled | FV, PV |
| PMAX_STATUS | hard_throttle_event | 0 | Sticky bit: hard throttle occurred | FV |
| PMAX_STATUS | soft_throttle_event | 0 | Sticky bit: soft throttle occurred | FV |
| FDP event counters | fdp_trigger_count | 0 | Count of FDP triggers for validation | FV |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| PMAX_STATUS register | Register | PythonSV: `sv.socket0.nio.punit.pmax_status.show()` | Hard/soft throttle event sticky bits |
| FDP trigger count | Register | PythonSV: `sv.socket0.nio.punit.fdp_trigger_count.read()` | Number of FDP events |
| PMAX_TRIGGER_IO GPIO (TX mode) | GPIO pin | Scope / logic analyzer on platform connector | Live PMAX event waveform |
| Core frequency (post-throttle) | Telemetry | PythonSV: `sv.socket0.cbb0.compute0.module0.resolved_freq.read()` | Verify Psafe enforcement |
| ICCMAX_CONFIG | Register | PythonSV: `sv.socket0.nio.punit.iccmax_config.show()` | Current IccMax reduction code |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| Overclocking platforms | PMAX may be disabled for higher performance | All PMAX TCDs |
| Server (locked) | PMAX always enabled; BIOS cannot disable | All PMAX TCDs |
| PMAX_TRIGGER_IO = TX mode | Validation-only: enables external observation | DFX TCD |
| PkgC6 active | PMAX masked during entry/exit to prevent false triggers | PkgC6 interaction TCD |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| BIOS configuration | BIOS knob: PMAX_TRIGGER_IO mode, trip threshold adjust |
| PCode / PrimeCode | `src/ip/pmax/` — threshold programming, PkgC6 masking, event handling |
| PMAX detection HW | imh0 PMAX IP — analog detector, fuse-programmable thresholds |
| D2D signaling HW | YY_FAST_THROTTLE_IN_0/1 wires — imh0 → cbb0/cbb1 |
| Core throttle HW | CBB Acode DVFS — Psafe frequency enforcement |

---

## Section 3: Validation Strategy

Three-tier validation is required because PMAX spans analog detection (silicon-only), D2D wire signaling (real hardware), and firmware policy configuration (modelable in PSS).

> **Layer coverage:** See §2 — Validation-Tier Layer Claim table for which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → PMAX model | Firmware threshold configuration, PkgC6 masking logic |
| PSS — HSLE | Single-die RTL (imh0) | PythonSV → PMAX RTL | Analog detector behavior in RTL, threshold comparison |
| FV | Post-silicon NWP | PythonSV → namednodes | Real analog detection, D2D wire timing, end-to-end throttle |
| PV | Post-silicon NWP + OS | Platform tools, scope | Platform-level VccIN behavior, GPIO observability |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | FV | PV |
|---|---|---|---|---|
| Firmware threshold misconfiguration | ✅ | ✅ | ✅ | indirect |
| PkgC6 masking logic error | ✅ | ⚠️ | ✅ | indirect |
| Analog detector trip point inaccuracy | ❌ | ⚠️ | ✅ | indirect |
| D2D fast-throttle wire failure | ❌ | ❌ | ✅ | indirect |
| Hard throttle response timing violation | ❌ | ❌ | ✅ | ❌ |
| FDP response too slow | ❌ | ❌ | ✅ | ❌ |
| GPIO PMAX_TRIGGER_IO misconfiguration | ✅ | ❌ | ✅ | ✅ |
| Illegal trip encoding (010/110/100) | ✅ | ✅ | ✅ | ❌ |
| ICCMAX_CONFIG dynamic adjustment error | ✅ | ✅ | ✅ | indirect |
| Platform loadline / VR interaction | ❌ | ❌ | ❌ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| Threshold programming and readback | ✅ | ✅ | ❌ | Firmware config validation |
| Hard throttle event injection and frequency verify | ❌ | ✅ | ❌ | Real D2D wire + analog |
| Soft throttle PWM proportional response | ❌ | ✅ | ❌ | Real D2D + DVFS |
| FDP droop injection and recovery | ❌ | ✅ | ❌ | Real analog droop |
| PkgC6 entry/exit masking | ✅ | ✅ | ❌ | C-state interaction |
| GPIO TX mode external observation | ❌ | ❌ | ✅ | Platform-level signal |
| Cross-platform VR + loadline variation | ❌ | ❌ | ✅ | Real platform variation |

---

## Section 5: Risks & Dependencies

### Active Risks

- **Analog detector accuracy:** Trip threshold accuracy depends on on-die process variation — validate across multiple parts and steppings.
- **D2D wire timing:** Hard throttle <50 ns response is silicon-dependent; PSS cannot validate timing.
- **Platform loadline sensitivity:** IccMax-to-trip-code mapping is sensitive to VR loadline; platform-specific calibration needed.
- **PkgC6 false trigger:** If PMAX mask is applied late during PkgC6 entry, false throttle events may occur.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Real analog droop detection accuracy | FV only | Silicon-level analog behavior cannot be modeled pre-Si |
| **G-2** | D2D wire propagation delay measurement | FV only | Requires real chiplet interconnect |
| **G-3** | Platform VR + loadline interaction | PV only | Requires real platform with production VR |

---

## Section 6: DFX Considerations

- **PMAX_TRIGGER_IO GPIO (TX mode):** Allows external scope/SMB observation of live PMAX events. Must be BIOS-configured to TX; default is RX (platform-driven injection).
- **Event counters:** PMAX_STATUS and FDP event counters provide validation hooks for automated checking.
- **VISA/ITH traces:** PMAX throttle events should be visible in VISA domain if configured; verify with ITH T2 enabling status.
- **PkgC6 mask verification:** DFX registers allow verifying PMAX mask is applied during deep C-state transitions.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| Illegal trip encoding (010, 110, 100) programmed | Threshold config TCD | HW behavior undefined — firmware must prevent programming |
| PMAX event during PkgC6 exit (race condition) | PkgC6 interaction TCD | Event should be masked; verify no false throttle |
| Rapid Vtrip0→Vtrip2 progression (skip soft throttle) | Hard throttle TCD | Hard throttle must still engage within 50 ns |
| PMAX_TRIGGER_IO left in TX mode on production | DFX TCD | Should not affect functional behavior; may leak debug info |
| IccMax reduction to 0 (no headroom) | Dynamic IccMax TCD | Continuous throttle expected; verify graceful degradation |
| External event injection via PMAX_TRIGGER_IO (RX mode) | Platform event TCD | Platform can drive intentional throttle — verify firmware handles |
| Multiple consecutive FDP events | FDP stress TCD | Counter increments correctly; no event loss |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

*No TCDs currently defined under this TPF. TCD creation is pending.*

### References

- [NWP PM HAS — PMAX / MT-PMax section](https://hsdes.intel.com/appstore/article-one/#/15019477947) — feature specification
- [NWP PM MAS — Power Protection chapter](https://hsdes.intel.com/appstore/article-one/#/15019477845) — parent TP
- [DMR PM HAS — PMAX (baseline reference)](https://hsdes.intel.com/appstore/article-one/#/) — DMR baseline for MT-PMax

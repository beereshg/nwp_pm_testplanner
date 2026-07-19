# TPF 22022420507 — CBB CCF Active States

| Field | Value |
|-------|-------|
| **TPF ID** | [22022420507](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Title** | CBB CCF Active States |
| **Parent TP** | [22022420505 — [NWP PM] CBB CCF PM](https://hsdes.intel.com/appstore/article-one/#/22022420505) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**CBB CCF Active States** covers the CCF (Converged Coherent Fabric) ring power management in the active (C0) and idle (C3) states within each CBB die. The CCF PMA (Power Management Agent) is the central hardware agent that executes GV (working-point) transitions for frequency/voltage changes, manages Fast Ring C3 and Ring C3 idle states, and handles save/restore across C-state transitions — all orchestrated by CBB PCode via PMSB messaging.

**Classification:** Silicon-heavy + Firmware-heavy hybrid. The GVFSM hardware (PLL/FLL, CCF FIVRs) is silicon; the GV control policy (workpoint calculation, VF curve interpolation, ELC) is CBB PCode firmware. Cross-die coordination (HPM 0x1b Uniform Fabric Freq) is IMH/NIO Primecode firmware.

**Gating mechanism:**
- **Fuses:** VF curve points (Pm..P0), max/min ratio caps define the GV operating envelope
- **BIOS knobs:** `UncoreFreqCtrlCbb` programs UFS_CONTROL fields via TPMI during TPMI_INIT PH1.x
- **Runtime TPMI:** OS/PythonSV can modify UFS_CONTROL at runtime (subject to BIOS lock)
- **MSR POWER_CTL (0x1FC) bit[25]:** `disable_ring_ee` — must be 0 for ring scalability distress source (affects Active States indirectly)

**NWP delta from DMR:** No architectural changes in CCF PMA, GVFSM, or register interface. NWP disables PkgC6 (and thus full Ring C3) for customer silicon — only Fast Ring C3 is POR on silicon. TPMI replaces legacy MSR interface for all CCF PM control/status.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBBs per socket | 2 (cbb0, cbb1) | NWP SOC topology |
| Cores per CBB | 48 (PantherCove) | NWP SOC topology |
| CCF ring max frequency (P0) | ~2.2 GHz (ratio 0x16) | Fuse-defined |
| CCF ring min frequency (Pm) | ~800 MHz (ratio 0x08) | Fuse-defined |
| CCF FIVRs per CBB | 8 | NWP VF architecture |
| VF curve points | Up to 8 per FIVR | NWP HAS |
| GV mode at boot | NonAutoGV (POR default) | NWP HAS |
| Fast Ring C3 | POR on silicon | NWP HAS |
| Ring C3 (full) | HSLE/Simics only (PkgC6 fused off) | NWP HAS |

---

## Section 2: Design Details

### CCF Active States Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">CBB CCF Active States — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / Tool</strong><br/>
    <small>turbostat · PythonSV namednodes · TPMI sysfs · UFS_STATUS readback</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: BIOS / UEFI Configuration</strong><br/>
    <small>UncoreFreqCtrlCbb BIOS knob → TPMI UFS_CONTROL init · VF curve fuse readout</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: CBB PCode (GV Policy)</strong><br/>
    <small>GVFSM: V-first/F-first sequencing · VF curve interpolation · ELC modes · NonAutoGV/Fast GV mode selection</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: CCF PMA (Power Management Agent)</strong><br/>
    <small>CCF_WP workpoint execution · Fast Ring C3 / Ring C3 entry/exit · PLL/FLL control · Save/Restore FSM · Abort handling</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / HW</strong><br/>
    <small>8× CCF FIVRs · PLL/FLL · Q-channels · Ring fabric · VCCRING rail · D2D UCIe link · TPMI decoder</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| OS / Tool | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS + tool stack |
| BIOS / UEFI Configuration | ✅ safe | ❌ | ❌ | ✅ | ❌ | VP safe for negative BIOS testing |
| CBB PCode (GV Policy) | ✅ | ✅ | ✅ | ✅ | indirect | All tiers validate firmware logic |
| CCF PMA (Power Mgmt Agent) | ⚠️ model | ✅ | ✅ | ✅ | indirect | HSLE validates PMA FSM directly |
| Silicon / HW | ❌ | ❌ | ❌ | ✅ | indirect | Real silicon only |

### GV Transition Sequencing (GVFSM)

```
Frequency UP (V-first):
  PCode calculates target ratio + voltage from VF curve
  → CCF PMA raises FIVR voltage (all 8 CCF FIVRs)
  → Wait FIVR stable
  → PLL/FLL crawl to new frequency (Fast GV: no UCLK stop)
  → UFS_STATUS.CURRENT_RATIO updates to new ratio
  → GVFSM done

Frequency DOWN (F-first):
  PCode calculates target ratio + voltage
  → PLL/FLL crawl to new frequency first
  → Wait PLL locked
  → CCF PMA lowers FIVR voltage
  → UFS_STATUS.CURRENT_RATIO updates
  → GVFSM done
```

### Fast Ring C3 vs Ring C3

| Attribute | Fast Ring C3 | Ring C3 (Full) |
|---|---|---|
| Trigger | PkgC0, PMA-autonomous (MC6) | PkgC6 prerequisite |
| Ring PLL | **ON** | **OFF** |
| UCLK | Gated | Gated |
| Q-channels | Deasserted | Deasserted |
| VCCRING | Retained | Gated |
| D2D UCIe link | L0 | **L1** |
| Save/Restore | Not needed | S/R FSM saves PMA state |
| NWP silicon | ✅ Supported | ❌ HSLE/Simics only |

### CCF PMA Save/Restore

- **C6 entry:** CCF PMA saves internal state to S/R SRAM (unless `RESET_BYPASS_CFG.SKIP_SAVE_RESTORE` set)
- **C6 exit:** CCF PMA restores state, reinitializes PLL, UCLK, Q-channels
- **SKIP_SAVE_RESTORE:** When set, PCode handles save/restore instead of hardware FSM

### NonAutoGV / Fast GV / Drainless GV

| Mode | PLL Mode | UCLK Stop | Description |
|---|---|---|---|
| NonAutoGV (POR default) | FLL | No | CCF changes workpoint only when commanded |
| Fast GV | FLL | No | PLL crawls to new frequency; no clock halt |
| Drainless GV | PLL | No | Legacy/survivability; atomic PLL set |

Registers: `pll_mode`, `pll_mode_ovrden` (fuse-set or override)

### ELC (Efficient Latency Control) Modes

- **Purpose:** Floor ring frequency at low utilization to reduce power without latency penalty
- **Fields in UFS_CONTROL:** ELC_LOW_RATIO [28:22], ELC_LOW_THRESHOLD [38:32], ELC_HIGH_THRESHOLD_ENABLE [39], ELC_HIGH_THRESHOLD [46:40], ELC_MID_RATIO [63:57]
- **Modes:** ELC_LOW (floor freq), ELC_MID (mid freq), ELC_HIGH (boost freq)
- **Thresholds:** Programmable via BIOS/TPMI; C0-utilization driven

### Interface & Register Matrix

| Register | Offset / Access | Key Fields | Purpose |
|---|---|---|---|
| CCF_WP[0-7] | 0x1100+ (PMSB CR) | TARGET_VID[10:0], TARGET_C_STATE[14:11], TARGET_MAX_RATIO[24:16], RST_TYPE[28:25], TARGET_PS[31:29] | GV workpoint + C-state target |
| UFS_CONTROL | TPMI cluster 0x01 | MAX_RATIO[14:8], MIN_RATIO[21:15], ELC fields, UNIFORM_CBB_FABRIC_FREQ_MODE[30], THROTTLE_MODE[1:0] | OS/BIOS control interface |
| UFS_STATUS | TPMI cluster 0x00 | CURRENT_RATIO[6:0], CURRENT_VOLTAGE[22:7], THROTTLE_COUNTER[63:32] | Current state readback |
| RESET_BYPASS_CFG | 0x1200 | SKIP_BIST[0], SKIP_PLL_RESET[1], SKIP_SAVE_RESTORE[2], SKIP_FAST_INIT_ON_CST_EXIT[3], SKIP_STALL_PBIST_POST_TEST[5:4], SET_BREAKPOINT_POST_RINGRESET[6], SKIP_GPSB_VOLUNTARY_MSGS_BLOCK[7] | Debug/survivability bypass |
| CCF_PMA_COMMAND | 0x1244 | BLOCK_REQ[0], MONITOR_COPY[1] | PMA command interface |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| UFS_STATUS.CURRENT_RATIO | TPMI | PythonSV `cbb.tpmi.ufs_status.current_ratio` | Live CCF ring ratio |
| UFS_STATUS.CURRENT_VOLTAGE | TPMI | PythonSV readback | Current ring voltage |
| CCF_WP[0].TARGET_MAX_RATIO | PMSB CR | PythonSV `cbb.base.ccf_pma.ccf_pmc_regs.ccf_wp[0]` | Active workpoint |
| pll_mode / pll_mode_ovrden | CR | PythonSV readback | FLL vs PLL mode |
| fast_c3_residency.counter | CR | PythonSV `cbb.base.ccf_pma.ccf_pmc_regs.fast_c3_residency.counter` | Fast Ring C3 residency |
| PEGA injection | Debug | `pega.uncoreRatioSingleShot(skt, cbb, ratio)` | Force CCF ring ratio |
| RESET_BYPASS_CFG | CR | PythonSV readback | Debug bypass bits |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| PkgC6 fuse-disabled (NWP customer) | Full Ring C3 not available; only Fast Ring C3 | TCD 16031169647 (Ring C3 — HSLE/Simics only) |
| NonAutoGV vs AutoGV boot mode | Determines whether CCF autonomously scales or waits for commands | TCD 22022421183 (NonAutoGV) |
| VF curve fuse variation | Different stepping/SKU may have different VF points | TCD 22022421168 (VF Curves) |

---

## Section 3: Validation Strategy

Three-tier rationale: PSS validates firmware logic and C-state FSM in models; FV validates real silicon GV transitions, VF curves, and PMA behavior; PV validates OS-visible UFS_STATUS readback.

Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | Firmware logic, BIOS flows, safe negative testing |
| PSS — HSLE | Single-die CBB RTL | PythonSV → TPMI RTL | PMA FSM, GVFSM, Fast Ring C3, save/restore |
| PSS — XOS | Both-die RTL (IMH+CBB) | PythonSV → full RTL | Cross-die HPM 0x1b coordination |
| FV | Post-silicon NWP | PythonSV → namednodes | Real silicon GV, VF curves, FIVR, Fast Ring C3 |
| PV | Post-silicon NWP + Ubuntu | turbostat / sysfs | OS-visible UFS_STATUS, TPMI readback |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| PCode GV policy bug (wrong VF curve interpolation) | ✅ | ⚠️ | ✅ | ✅ | indirect |
| CCF PMA FSM bug (wrong state transition) | ⚠️ model | ✅ | ✅ | ✅ | indirect |
| GVFSM V-first/F-first ordering bug | ❌ | ✅ | ✅ | ✅ | indirect |
| Fast Ring C3 entry/exit bug | ❌ | ✅ | ✅ | ✅ | indirect |
| Ring C3 PLL-off / VCCRING gating bug | ❌ | ✅ | ✅ | ❌ NWP | ❌ |
| Cross-die HPM 0x1b coordination bug | ❌ | ❌ | ✅ | ✅ | indirect |
| Silicon HW bug (FIVR, PLL, TPMI decoder) | ❌ | ❌ | ❌ | ✅ | indirect |
| BIOS negative validation (invalid UFS_CONTROL) | ✅ safe | ❌ | ❌ | ❌ risky | ❌ |
| OS/driver readback bug (turbostat, sysfs) | ❌ | ❌ | ❌ | ❌ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| GV transition full [Pm..P0] sweep | ✅ | ✅ | ❌ | FV validates real VF curve |
| Fast Ring C3 entry/exit | ✅ HSLE | ✅ | ❌ | FV validates real PLL behavior |
| Ring C3 full (PLL off, VCCRING gated) | ✅ HSLE | ❌ NWP | ❌ | HSLE only on NWP |
| NonAutoGV mode verification | ✅ | ✅ | ❌ | FV validates real pll_mode |
| BIOS knob → UFS_CONTROL propagation | ✅ safe | ✅ | ❌ | VP safe for negative cases |
| TPMI per-die scoping | ✅ | ✅ | ❌ | FV validates real per-die isolation |
| ELC threshold-driven freq floor | ✅ | ✅ | ❌ | FV validates real ELC response |
| Cross-die Uniform Fabric Freq (HPM 0x1b) | ✅ XOS | ✅ | ❌ | XOS validates cross-die protocol |

---

## Section 5: Risks & Dependencies

### Active Risks

- **Ring C3 untestable on NWP silicon:** Full Ring C3 requires PkgC6, which is fused off on NWP customer silicon. Mitigation: validate on HSLE/Simics only.
- **ELC mode validation gap:** No TCD or TC exists for ELC modes. Mitigation: create new TCD (identified in T1 gap audit).
- **Cross-die HPM coordination gap:** No TCD covers HPM 0x1b end-to-end flow. Mitigation: create new TCD (identified in T1 gap audit).

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|---|---|---|---|
| G-1 | Ring C3 (full, PLL off) not testable on NWP silicon | HSLE/Simics only | PkgC6 fused off on customer silicon; HSLE RTL validates PMA FSM directly |
| G-2 | OS/tool layer (PV) for CCF Active States | No PV TCs | CCF ring freq is not directly user-facing; FV validates all functional behavior |

---

## Section 6: DFX Considerations

- **RESET_BYPASS_CFG:** 8-bit debug/survivability register allows skipping PLL reset, save/restore, LLC BIST, and GPSB message blocking during C-state flows. Critical for silicon debug when PMA hangs during entry/exit.
- **SET_BREAKPOINT_POST_RINGRESET:** Allows debug halt after ring reset for trace capture.
- **PEGA injection:** Enables forced CCF ring ratio for targeted GV validation without OS workload dependency.
- **CCF_PMA_COMMAND.MONITOR_COPY:** Copies PMA internal state for debug observation.
- **fast_c3_residency.counter:** Hardware residency counter for Fast Ring C3 — key observability for idle state validation.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| GV transition at Pm (minimum ratio boundary) | TCD 22022421168 | CCF clamps at Pm; no underflow; UFS_STATUS reflects Pm |
| GV transition at P0 (maximum ratio boundary) | TCD 22022421168 | CCF clamps at P0; no overshoot; VF curve voltage correct |
| Fast Ring C3 entry during active GV transition | TCD 16031169646 | PMA completes GV first, then enters Fast C3; no abort |
| Ring C3 exit with corrupted S/R SRAM | TCD 16031169647 | PMA detects and resets; RESET_BYPASS_CFG.SKIP_SAVE_RESTORE fallback |
| TPMI write during GV transition | TCD 22022421168 | PCode serializes TPMI writes with GVFSM; no race |
| All cores in C6 + Fast Ring C3 + wake event | TCD 16031169646 | PMA exits Fast C3, restores ring, core exits C6 |
| NonAutoGV mode with PEGA injection | TCD 22022421183 | PEGA overrides NonAutoGV workpoint; UFS_STATUS tracks |
| ELC threshold crossing during idle→active | *(no TCD)* | PCode should ramp freq to ELC floor within 1 slow loop |
| Cross-die HPM 0x1b with asymmetric CBB load | *(no TCD)* | IMH resolves max across CBBs; each CBB enforces max(local, global_min) |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | TC Count | Segment |
|---|---|---|---|---|
| [22022421168](https://hsdes.intel.com/appstore/article-one/#/22022421168) | CBB CCF PM GV Control Interface | open | 4 (BIOS Config, PEGA, TPMI, VF Curves) | FV |
| [16031169646](https://hsdes.intel.com/appstore/article-one/#/16031169646) | CBB CCF Fast Ring C3 | open | 1 | FV |
| [16031169647](https://hsdes.intel.com/appstore/article-one/#/16031169647) | CBB CCF Ring C3 | open | 1 | FV |
| [22022421183](https://hsdes.intel.com/appstore/article-one/#/22022421183) | CBB CCF NonAutoGV Mode | open | 1 | FV |
| [22022421179](https://hsdes.intel.com/appstore/article-one/#/22022421179) | [SPLIT] CBB CCF Idle states | deprecated | 0 | — |

### References

| Type | Link | Scope |
|------|------|-------|
| HAS | [DMR CBB CCF PM HAS v1.0](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html) | CCF PMA architecture, C-state entry/exit, GV, S/R |
| HAS | [NWP CBB CCF HAS](https://docs.intel.com/documents/clientsilicon/dmr_cbb/global/ccf/nwp_ccf.html) | NWP-specific CCF deltas |
| HAS | [DMR CBB Address Map](https://docs.intel.com/documents/ClientSilicon/DMR_CBB/global/NCU/CBBAddressMap.html) | CBB register address map |
| HAS | [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR_PM_Features/DMR_Fabric_DVFS.html) | UFS_CONTROL/STATUS, ELC, Uniform Fabric Freq |
| HAS | [CBB PEGA](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA injection for debug/validation |
| HAS | [CBB TPMI](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) | TPMI register interface |
# TPF 22022420514 — CBB CCF Ring Scalability

| Field | Value |
|-------|-------|
| **TPF ID** | [22022420514](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Title** | CBB CCF Ring Scalability |
| **Parent TP** | [22022420505 — [NWP PM] CBB CCF PM](https://hsdes.intel.com/appstore/article-one/#/22022420505) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**CBB CCF Ring Scalability** is the ring-frequency scaling subsystem within each CBB die. It drives CCF ring GV (Gear Voltage) transitions using two complementary telemetry inputs — CBO bandwidth and SBO snoop distress — processed entirely by CBB-local PCode through a slow-loop heuristic (~1 ms) and fast-path triggers (200 µs DistressCycleUpdate). The feature ensures the CCF ring frequency ramps up under fabric congestion or high bandwidth demand, and ramps down during idle or low-demand periods, minimizing power without sacrificing latency.

**Classification:** Silicon-heavy + Firmware-heavy hybrid. The GVFSM hardware (PLL/FLL, 8x CCF FIVRs) is silicon; the frequency policy algorithm (BW threshold LUT walk, distress-to-ia_ring_factor conversion, workpoint clamping) is CBB PCode firmware. Cross-die coordination via HPM 0x1b is IMH/NIO Primecode firmware.

**Gating mechanism:**
- **MSR POWER_CTL (0x1FC) bit[25] disable_ring_ee:** Must be 0 (enabled) on all cores for ring scalability / distress source to function
- **Fuses:** VF curve points (Pm..P0), max/min ratio caps define the GV operating envelope
- **BIOS knobs:** UFS_CONTROL fields (MAX_RATIO, MIN_RATIO, ELC thresholds, THROTTLE_MODE) programmed via TPMI during TPMI_INIT PH1.x
- **Runtime TPMI:** OS/PythonSV can modify UFS_CONTROL at runtime (subject to BIOS lock)

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBBs per socket | 2 (cbb0, cbb1) | NWP SOC topology |
| Cores per CBB | 48 (PantherCove) | NWP SOC topology |
| CCF ring max frequency (P0) | 2.2 GHz (ratio 0x16) | Fuse-defined |
| CCF ring min frequency (Pm) | 800 MHz (ratio 0x08) | Fuse-defined |
| CCF FIVRs per CBB | 8 | NWP VF architecture |
| VF curve points | 6-point curve per FIVR | NWP HAS |
| GVFSM slow-loop period | ~1 ms | PCode design |
| DistressCycleUpdate (fast-path) | 200 µs | PCode design |
| RSE (Ring Scalability Event) period | ~2k uclk cycles | NWP CCF spec |
| GV mode at boot | NonAutoGV (POR default) | NWP HAS |
| D2D roundtrip latency at 2 GHz | ~72 cycles | NWP D2D spec |

### Generational Lineage (Co-Design T6 — ingested 2026-07-18)

> **Provenance:** Each row cites the spec document verbatim. Rows marked `no spec access` are honest gaps — not inferred. Full source list in §8 References.

| Generation | Change (interface/behavior/scope) | Interface impact | Spec ref (doc + clause, verbatim) | Source collection | Validation impact |
|---|---|---|---|---|---|
| pre-ICL | Ring frequency decision was PCode-only slow-loop (~1 ms) based on CCF telemetry; no HW ring-scalability mechanism | Tests target slow-loop PCode behavior only; later HW distress / fast-response tests do not apply | "Until ICL, the decision on changing ring frequency was done by PCode once every 'slow loop' based on telemetry received from CCF." | External Industry Specs | invalidates |
| ICL | HW-based ring scalability introduced: CBO monitors LLC accesses/hit/TOR occupancy; SBO accumulates distress; PUnit responds faster to raise uclk | Adapt from pure slow-loop to HW telemetry counters + SBO→PUnit distress | "In ICL HW-based ring scalability mechanism introduced. Each CBO will have counters which will monitor LLC accesses, LLC hit, TOR occupancy… The SBO accumulating the distress indication from all the CBOs." | External Industry Specs | adapt |
| ADL | Telemetry bucket thresholds changed; configurable RSE event length added; ring scalability used only for GT scenarios on ADL-P | Threshold/period assumptions not portable; tests adapt to new buckets, RSE config, GT-only scope | "ADL changes: LLC HR buckets move from limits at 12.5%, 25%, 50% to 25%, 50%, 75%. Adding an option to adjust RSE… for ADL, ring scalability is used only for GT scenarios." | External Industry Specs | adapt |
| LNL | Ring scalability reframed as efficiency optimization using scalability predictor from CCF and Amdahl's law | Adapt from simple distress/no-distress to predictor-based efficiency/performance tradeoff | "Ring scalability is a feature that allows reduce ring frequency in order to improve efficiency of IA/Ring domain. This is done by consuming scalability predictor from CCF and evaluation of power/performance impact using Amdahl's law." | [ring_scalability.html](https://docs.intel.com/documents/pm_doc/src/lnl/features/ring%20scalability/ring_scalability.html) | adapt |
| LNL | Distress reporting uses discrete decoded levels via `RING_DISTRESS_STATUS[IA_LEVEL]` (0x0–0x5+), not binary | Binary / low-high distress tests need adaptation to discrete-level validation | "CCF reports the scalability (p) via the RING_DISTRESS_STATUS[IA_LEVEL]. The values are discreet values decoded as follows: 0x0 - 0.01 0x1 - 0.10 0x2 - 0.32 0x3 - 0.40 0x4 - 0.60 0x5 and above - 0.85" | [ring_scalability.html](https://docs.intel.com/documents/pm_doc/src/lnl/features/ring%20scalability/ring_scalability.html) | adapt |
| LNL | CCF GV default is NonAutoGV; AutoGV transition exists via SB message `AUTO_GV_CTRL_REQ`; `CCF_WP` writable only in NonAuto mode | NonAuto-only tests partly valid; must adapt to cover AutoGV capability if POR | "In LNL we are going to have only NonAutoGV mode (AutoGV is not POR)… CCF can be transitioned into AutoGV Mode if SB MSG: AUTO_GV_CTRL_REQ received with auto_gv_en set." | [lnl_ccf_pm.html](https://docs.intel.com/documents/pm_doc/src/lnl/ip%20integration/ccf/lnl_ccf_pm.html) | adapt |
| DMR (CBB feature list) | Server-side Ring GV becomes named DMR CBB PM feature: "Fast & Independent Per-die Ring GV", "Ring Rocket (fast up / distress / scalability)", "Ring with 2-slope RAPL support" | Client-era tests must adapt to server per-die / fast-up / RAPL-coupled scope | "Ring GV [Fast & Independent Per-die Ring GV]… Ring Rocket (fast up / ring distress / ring scalability)… Ring with 2-slope RAPL support" | [dmr_cbb_power_management.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb%20overview/dmr_cbb_power_management.html) | adapt |
| DMR (CBB GV mode) | CBB GV is NonAutoGV only; AutoGV is not POR | LNL-style AutoGV validation invalidated for DMR POR | "In CBB we are going to have only NonAutoGV mode (AutoGV is not POR)" | [cbb_ccf_pm.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/ip%20integration/ccf/cbb_ccf_pm.html) | invalidates |
| DMR (CBB GV mode) | NonAutoGV remains reset default; `CCF_WP` update only legal in NonAuto mode | Existing NonAuto reset/default tests valid; AutoGV transition tests do not apply | "This is the reset default state. Upon cold boot exit or C-State exit, CCF will start in NonAuto Mode. CCF_WP can only be updated when CCF is in NonAuto Mode." | [cbb_ccf_pm.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/ip%20integration/ccf/cbb_ccf_pm.html) | unchanged |
| DMR (ring scalability) | Telemetry explicitly dual-path: CBO pipe traffic + central SBO data, accumulated per RSE and sent to PCode through SB | Earlier single-source telemetry assumptions must adapt to combined CBO + SBO model | "The system collects traffic data from each cbo pipe and from the central SBO, and performs calculations on it. Once per RSE… it accumulates the adjusted traffic grade from all cbos… The calculated result is being sent to Pcode through SB." | [cbb_ccf_pm.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/ip%20integration/ccf/cbb_ccf_pm.html) | adapt |
| DMR (ring scalability MAS) | MAS describes cluster-local CBO + SBO telemetry, SBO-generated grade, CCF PMA collection, distress message to Punit; SBO includes "Linear regression block and PMON logic" | Adapt to graded/processed telemetry path; regression/PMON logic changes observability | "The feature analyzes ring traffic telemetries implemented inside each of the cluster's CBOs and their corresponding SBO… SBO then outputs a 'Grade'… CCF PMA collects the grades… constructs and sends a 'Distress' message to Punit" | [ring_scalability_mas.html](https://docs.intel.com/documents/ccfdoc/src/cbb/ring_scalability/ring_scalability_mas.html) | adapt |
| DMR (server scope) | Telemetry narrowed to IA-core traffic only ("GT is not under CCF anymore") | Client/GT-oriented ring-scalability tests invalidated for server CBB | "For LNL we will measure IA cores traffic only (GT is not under CCF anymore)" | [cbb_ccf_pm.html](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/ip%20integration/ccf/cbb_ccf_pm.html) | invalidates |
| NWP | no spec access | no spec access | no spec access | no spec access | adapt (assume DMR baseline) |

**NWP-relevant tail:** Feature introduced at ICL (HW ring scalability); strongest lineage break is LNL→DMR — LNL documents an AutoGV transition path, while DMR server CBB explicitly says NonAutoGV only (AutoGV not POR). DMR server narrows telemetry scope to IA-only (no GT) and adds dual-path CBO BW + SBO distress with linear regression grading. NWP inherits DMR server CBB behavior unless NWP-specific CBB delta HAS says otherwise; the NWP row remains `no spec access` — an honest gap, not inferred.

---

## Section 2: Design Details

### Ring Scalability Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">CBB CCF Ring Scalability — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 5: OS / Tool</strong> — intel_pstate driver, PythonSV/PEGA injection, MSR 0x1FC ring_ee enable check</div>
  <div style="background:#2F5496;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: BIOS / Firmware Init</strong> — TPMI_INIT PH1.x: UFS_CONTROL programming (MAX/MIN ratio envelope, ELC thresholds, THROTTLE_MODE), VF curve fuse→TPMI propagation</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: CBB PCode (Local Policy)</strong> — BW threshold LUT walk, distress→ia_ring_factor→ia_promote_ring, GVFSM workpoint computation, slow-loop (~1 ms) + fast-path (200 µs)</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: IMH/NIO Primecode (Cross-Die Coord.)</strong> — HPM 0x1b aggregation (max of all CBB desired ratios → DOWNSTREAM_RESOLVED_MIN_RATIO), Uniform Fabric Frequency enforcement</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Silicon HW</strong> — GVFSM (V-first/PLL-first state machine), Ring PLL/FLL, 8x CCF FIVRs, CBO/SBO telemetry counters, CCF PMA ring-scalability logic, distress threshold comparators</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 5: OS / Tool | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS + intel_pstate; MSR 0x1FC readback |
| Layer 4: BIOS / Firmware Init | ✅ | ❌ | ❌ | ✅ | ✅ | VP validates TPMI_INIT; FV validates post-boot UFS_CONTROL state |
| Layer 3: CBB PCode (Local Policy) | ✅ | ✅ | ✅ | ✅ | indirect | VP: BW heuristic logic; HSLE: single-die PCode; XOS: cross-die |
| Layer 2: IMH/NIO Primecode (Cross-Die) | ❌ | ❌ | ✅ | ✅ | indirect | XOS: both dies present; FV: real silicon HPM transport |
| Layer 1: Silicon HW | ❌ | ✅ | ✅ | ✅ | indirect | HSLE: RTL-level GVFSM/PLL/distress comparators; FV: real silicon |

### Ring Scalability — Dual-Path Architecture (BW + Distress)

<!-- raw-html -->
<div style="margin:16px 0;border:2px solid #1e3a5f;border-radius:10px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;max-width:780px;">

  <div style="background:#0f4c81;color:#fff;padding:10px 18px;font-weight:700;font-size:13px;letter-spacing:.3px;">
    CBB Die — Ring Scalability Dual-Path Architecture <span style="font-weight:400;opacity:.7;font-size:11px;">(all GV decisions CBB-local)</span>
  </div>

  <div style="padding:18px 20px;background:#f8fafc;">

    <!-- ROW 1: Telemetry Inputs -->
    <div style="display:flex;gap:16px;margin-bottom:4px;">
      <div style="flex:1;background:#e3f2fd;border:2px solid #1565c0;border-radius:8px;padding:12px;">
        <div style="font-weight:700;color:#1565c0;font-size:12px;margin-bottom:6px;">Path A: CBO Bandwidth</div>
        <div style="font-size:10px;color:#333;line-height:1.7;">
          <strong>48 CBO mesh</strong> — RD/WR transaction counters<br>
          accumulate per-cycle; sampled per RSE (~2k uclk)
        </div>
      </div>
      <div style="flex:1;background:#fce4ec;border:2px solid #c62828;border-radius:8px;padding:12px;">
        <div style="font-weight:700;color:#c62828;font-size:12px;margin-bottom:6px;">Path B: SBO Distress</div>
        <div style="font-size:10px;color:#333;line-height:1.7;">
          <strong>SBO snoop back-pressure</strong> — TOR occupancy + WCil<br>
          counters exceed HIGH threshold → assert distress
        </div>
      </div>
      <div style="flex:1;background:#fff8e1;border:2px solid #f9a825;border-radius:8px;padding:12px;">
        <div style="font-weight:700;color:#e65100;font-size:12px;margin-bottom:6px;">Path C: External Requests</div>
        <div style="font-size:10px;color:#333;line-height:1.7;">
          <strong>BIOS</strong> — UFS_CONTROL (boot)<br>
          <strong>PEGA</strong> — B2P mailbox (injection)<br>
          <strong>TPMI</strong> — runtime ratio lock
        </div>
      </div>
    </div>

    <!-- Arrows row 1-2 -->
    <div style="display:flex;gap:16px;margin-bottom:4px;">
      <div style="flex:1;text-align:center;color:#1565c0;font-size:16px;">&#9660; <span style="font-size:9px;">BW telemetry per RSE</span></div>
      <div style="flex:1;text-align:center;color:#c62828;font-size:16px;">&#9660; <span style="font-size:9px;">distress assertion</span></div>
      <div style="flex:1;text-align:center;color:#e65100;font-size:16px;">&#9660; <span style="font-size:9px;">ratio request</span></div>
    </div>

    <!-- ROW 2: Processing Logic -->
    <div style="display:flex;gap:16px;margin-bottom:4px;">
      <div style="flex:1;background:#e8eaf6;border:2px solid #3949ab;border-radius:8px;padding:10px;text-align:center;">
        <div style="font-weight:700;color:#3949ab;font-size:11px;">BW Threshold LUT Walk</div>
        <div style="font-size:9px;color:#555;margin-top:4px;">
          BW &gt; HIGH_THRESH for N loops → boost<br>
          BW &lt; LOW_THRESH for M loops → reduce
        </div>
      </div>
      <div style="flex:1;background:#fce4ec;border:2px solid #c62828;border-radius:8px;padding:10px;text-align:center;">
        <div style="font-weight:700;color:#c62828;font-size:11px;">Distress Grade Computation</div>
        <div style="font-size:9px;color:#555;margin-top:4px;">
          TOR occ + WCil &gt; HIGH → assert ia_distress[3:0]<br>
          7-threshold logistic regression → grade 0-15<br>
          hysteresis: de-assert after N_OFF below LOW
        </div>
      </div>
      <div style="flex:1;background:#fff8e1;border:2px solid #f9a825;border-radius:8px;padding:10px;text-align:center;">
        <div style="font-weight:700;color:#e65100;font-size:11px;">TPMI UFS_CONTROL</div>
        <div style="font-size:9px;color:#555;margin-top:4px;">
          MAX_RATIO [14:8] · MIN_RATIO [21:15]<br>
          ELC thresholds · THROTTLE_MODE
        </div>
      </div>
    </div>

    <!-- Arrows row 2-3 -->
    <div style="display:flex;gap:16px;margin-bottom:4px;">
      <div style="flex:1;text-align:center;color:#3949ab;font-size:16px;">&#9660; <span style="font-size:9px;">GV target</span></div>
      <div style="flex:1;text-align:center;color:#c62828;font-size:16px;">&#9660; <span style="font-size:9px;">ia_distress[3:0] via CR_WR 0x1C8</span></div>
      <div style="flex:1;text-align:center;color:#e65100;font-size:16px;">&#9660; <span style="font-size:9px;">~1 ms slow-loop read</span></div>
    </div>

    <!-- ROW 3: CBB PCode Decision Engine -->
    <div style="background:#1a237e;color:#fff;border-radius:8px;padding:14px 18px;margin-bottom:4px;">
      <div style="font-weight:700;font-size:12px;margin-bottom:8px;">CBB PCode — Workpoint Decision Engine <span style="font-weight:400;opacity:.7;font-size:10px;">(per-CBB, slow-loop ~1 ms + fast-path 200 µs)</span></div>
      <div style="display:flex;gap:20px;font-size:10px;">
        <div style="flex:1;background:rgba(255,255,255,.12);border-radius:6px;padding:8px;">
          <strong>1.</strong> Read [MIN_RATIO, MAX_RATIO] from UFS_CONTROL<br>
          <strong>2.</strong> Read BW telemetry (CBO counters per RSE)<br>
          <strong>3.</strong> Read PEGA B2P request (overrides BW heuristic)
        </div>
        <div style="flex:1;background:rgba(255,255,255,.12);border-radius:6px;padding:8px;">
          <strong>4.</strong> Compute distress workpoint:<br>
          &nbsp;&nbsp;<code style="color:#90caf9;">distress_ccf_freq = max_ccp_req × ring_distress_table[level][epb]</code><br>
          &nbsp;&nbsp;<code style="color:#90caf9;">snoop_floor = snoop_distress_table[snoop_level][epb]</code><br>
          &nbsp;&nbsp;<code style="color:#90caf9;">ufs_ratio = max(distress_ccf_freq, snoop_floor)</code><br>
          &nbsp;&nbsp;<code style="color:#90caf9;">final = min(ufs_ratio, rapl_ccf_freq, limits)</code><br>
          <strong>5.</strong> Clamp to [MIN, MAX] — silent enforcement
        </div>
      </div>
    </div>

    <!-- Arrow row 3-4 -->
    <div style="text-align:center;color:#1a237e;font-size:18px;margin-bottom:4px;">&#9660; <span style="font-size:9px;color:#555;">resolved GV target ratio</span></div>

    <!-- ROW 4: GVFSM Execution -->
    <div style="background:#fff;border:2px solid #1a237e;border-radius:8px;padding:14px 18px;margin-bottom:4px;">
      <div style="font-weight:700;color:#1a237e;font-size:12px;margin-bottom:8px;">GVFSM — NonAutoGV Execution (POR Mode)</div>
      <div style="display:flex;gap:16px;">
        <div style="flex:1;background:#e8f5e9;border:2px solid #2e7d32;border-radius:6px;padding:8px;text-align:center;">
          <div style="font-weight:700;color:#2e7d32;font-size:10px;">Freq UP (V-first)</div>
          <div style="font-size:9px;color:#333;margin-top:3px;">FIVR voltage ramp (8 FIVRs)<br>→ wait settle → PLL ratio change</div>
        </div>
        <div style="flex:1;background:#fce4ec;border:2px solid #c62828;border-radius:6px;padding:8px;text-align:center;">
          <div style="font-weight:700;color:#c62828;font-size:10px;">Freq DOWN (PLL-first)</div>
          <div style="font-size:9px;color:#333;margin-top:3px;">PLL ratio step down<br>→ FIVR voltage reduce (8 FIVRs)</div>
        </div>
        <div style="flex:1;background:#f3e5f5;border:2px solid #7b1fa2;border-radius:6px;padding:8px;text-align:center;">
          <div style="font-weight:700;color:#7b1fa2;font-size:10px;">FSM States</div>
          <div style="font-size:9px;color:#333;margin-top:3px;">IDLE → BLOCK → INC_GB<br>→ DEC_DB → RESUME → BLK_INTF</div>
        </div>
      </div>
    </div>

    <!-- Arrow row 4-5 -->
    <div style="text-align:center;color:#1a237e;font-size:18px;margin-bottom:4px;">&#9660; <span style="font-size:9px;color:#555;">settled frequency / voltage</span></div>

    <!-- ROW 5: Outputs -->
    <div style="display:flex;gap:12px;">
      <div style="flex:1;background:#e8f5e9;border:2px solid #2e7d32;border-radius:8px;padding:10px;text-align:center;">
        <div style="font-weight:700;color:#2e7d32;font-size:11px;">UFS_STATUS</div>
        <div style="font-size:9px;color:#333;margin-top:4px;">CURRENT_RATIO [6:0] — live PLL ratio<br>CURRENT_VOLTAGE [22:7] — max(8 FIVRs)<br>THROTTLE_COUNTER — 1/ms on violation</div>
      </div>
      <div style="flex:1;background:#e3f2fd;border:2px solid #1565c0;border-radius:8px;padding:10px;text-align:center;">
        <div style="font-weight:700;color:#1565c0;font-size:11px;">HPM 0x1b → IMH/NIO</div>
        <div style="font-size:9px;color:#333;margin-top:4px;">UPSTREAM_CCF_DESIRED_RATIO<br>freq intent → Primecode Fabric DVFS</div>
      </div>
      <div style="flex:1;background:#fff3e0;border:2px solid #e65100;border-radius:8px;padding:10px;text-align:center;">
        <div style="font-weight:700;color:#e65100;font-size:11px;">PLR_DIE_LEVEL</div>
        <div style="font-size:9px;color:#333;margin-top:4px;">Perf Limit Reason<br>0x0 = no throttle (clean run)</div>
      </div>
    </div>

  </div>
</div>
<!-- /raw-html -->

### Distress Signal Flow — CBO/SBO to PCode

`
CBO Bandwidth Path:
  48 CBO mesh counters accumulate RD/WR per cycle
    → CBB PCode slow-loop reads CBO counters each ~1 ms
    → BW threshold LUT walk: compare current BW to HIGH/LOW thresholds
    → BW > HIGH_THRESHOLD for N loops → GVFSM boosts CCF ring ratio
    → BW < LOW_THRESHOLD for M loops → GVFSM reduces CCF ring ratio

SBO Distress Path:
  SBO snoop back-pressure: TOR occupancy + WCil counters
    → Both exceed HIGH threshold → CCF PMA asserts IA_DISTRESS
    → PMSB CR_WR 0x1C8 delivers ia_distress[3:0] (0-15 grade)
    → CBB PCode: ia_distress → ring_distress_table[level][epb] → ia_ring_factor
    → ia_promote_ring = max_ccp_req × ia_ring_factor
    → snoop_floor = snoop_distress_table[snoop_level][epb]
    → final_ratio = min(max(distress_freq, snoop_floor), rapl_limit, global_limits)
    → CBB GVFSM executes GV transition
    → Congestion relieves → IA_DISTRESS de-asserts after N_OFF below LOW threshold

Fast-path triggers (bypass slow-loop):
  - Distress state change (assertion/de-assertion)
  - DistressCycleUpdate every 200 µs
  - Upon distress assertion: Santa issues 3 consecutive throttle messages to cNCU
  - Upon de-assertion: 3 consecutive de-throttle messages
`

### NonAutoGV Execution Mechanism

NonAutoGV is the **only POR mode** for CBB ring GV. The CCF does NOT autonomously select V/F — it executes GV transitions exclusively in response to explicit workpoint commands written to CCF_WP by PCode.

**Clocking modes:**
- pll_mode=0 (POR): Fast GV — no clock stop during transition; PLL re-locks while frequency changes
- pll_mode=1 (Survivability): PLL Crawling (FLL) — frequency steps ≤ req_crawl_delta_f fuse; requires pll_mode_ovrden=1

### Idle Exit GV Recovery

When CCF is in Active Idle (Fast Ring C3 / ELC Low at CFC_MIN_RATIO), incoming C-state wake events trigger the GVFSM to execute a V-first GV ramp-up:

`
CCF Active Idle (CFC_MIN_RATIO, e.g. 800 MHz)
  └── Wake event arrives (core C-state exit / BW request / HPM 0x1b update)
      └── CBB PCode detects wake → issues GVFSM GV step
          └── V-first: FIVR ramp → PLL ratio change
              └── UFS_STATUS.CURRENT_RATIO reaches target
                  └── Fabric active, traffic serviced
`

### GV Control Interface — Three Input Paths

| Path | When | Register | Mechanism |
|---|---|---|---|
| **BIOS Config** | Boot (TPMI_INIT PH1.x) | UFS_CONTROL: MAX_RATIO, MIN_RATIO, ELC thresholds | Sets operating envelope; PCode reads per slow-loop |
| **PEGA Injection** | Any time (Ring 0) | B2P Mailbox: pega.pegaPstate(skt, cbb, clrgv=ratio) | Overrides BW heuristic; direct ratio control |
| **TPMI Runtime** | Any time (OS/PySV) | 	pmi.ufs_control.max_ratio = min_ratio = N | Ratio lock (MAX=MIN) or restore autonomous |

### Interface & Register Matrix

| Register / MSR | Field | Default | Feature Effect | Tier Validated |
|---|---|---|---|---|
| MSR POWER_CTL (0x1FC) | bit[25] disable_ring_ee | 0 (enabled) | Ring scalability / distress source enable | FV, PSS |
| TPMI UFS_CONTROL | MAX_RATIO [14:8] | P0 fuse | Upper bound for GV transitions | FV, PSS |
| TPMI UFS_CONTROL | MIN_RATIO [21:15] | Pm fuse | Lower bound for GV transitions | FV, PSS |
| TPMI UFS_CONTROL | THROTTLE_MODE [1:0] | 0 | Throttle enforcement mode | FV |
| TPMI UFS_STATUS | CURRENT_RATIO [6:0] | — | Live PLL ratio after GV completion | FV, PSS |
| TPMI UFS_STATUS | CURRENT_VOLTAGE [22:7] | — | Max of 8 CCF FIVRs (U3.13 format) | FV |
| PUNIT_CR_RING_DISTRESS_STATUS (0x1C8) | ia_distress [3:0] | 0 | IA main distress grade (0-15) | FV |
| PUNIT_CR_RING_DISTRESS_STATUS (0x1C8) | snoop_level [11:8] | 0 | Snoop distress grade (0-15) | FV |
| PUNIT_CR_RING_DISTRESS_STATUS (0x1C8) | ia_distress_invalid [4] | 0 | Validity flag (0 = valid) | FV |
| PUNIT_CR_RING_DISTRESS_STATUS (0x1C8) | snoop_level_invalid [12] | 0 | Validity flag (0 = valid) | FV |
| CCF_WP[0] | target_max_ratio | — | PCode-written GV workpoint target | FV, PSS |
| Ring PLL mode | pll_mode (fusecr_ovrd_0) | 0 (PLL) | 0=Fast GV (POR), 1=PLL Crawling | FV |
| pcode.vars.ring | resolved_ratios.{max,guaranteed,min} | — | PCode algorithm internal state | FV |
| pcode.vars.ring | ia_distress, ia_ring_factor | — | Distress grade and ring factor | FV |
| HPM 0x1b | UPSTREAM_CCF_DESIRED_RATIO | — | CCF freq intent → Primecode | FV, PSS (XOS) |
| HPM 0x1b | DOWNSTREAM_CCF_RESOLVED_MIN_RATIO | — | Min-ratio floor from Primecode | FV, PSS (XOS) |
| CSR CBB_RING_FASTC3_RESIDENCY | — | 0 | Cycle count in Fast Ring C3 | FV |
| CSR CCF_PMA pm_state | — | — | CCF PM FSM state | FV |
| CSR Crs_ring_inject_starvation_thresholds | — | — | CBO ring inject starvation thresholds | FV |
| CSR Crs_agt_ring_inject_starvation_thresholds | — | — | Agent ring inject starvation thresholds | FV |

### Observability

| Observable | Type | Tool / Command | What It Shows |
|---|---|---|---|
| UFS_STATUS.CURRENT_RATIO | TPMI | sv.sockets.sktN.cbbs.cbbX.base.tpmi.ufs.ufs_status | Live CCF ring ratio |
| ring_distress_status | CSR | sv.sockets.sktN.cbbs.cbbX.base.punit_regs.punit_pmsb.pmsb_pcu.ring_distress_status | ia_distress, snoop_level, invalid flags |
| pcode.vars.ring | PCode vars | sv.sockets.sktN.cbbs.cbbX.base.pcode.vars.ring.* | Algorithm internals: resolved ratios, ia_ring_factor |
| CCF_WP status | CSR | sv.sockets.sktN.cbbs.cbbX.base.punit_regs.punit_pmsb.pmsb_pcu.ccf_wp_status | Current resolved workpoint |
| PMON CLR counters | CSR | sv.sockets.sktN.cbbs.cbbX.base.i_ccf_envs[k].egresss[j].pmoncounter[N] | Ring scalability events |
| PLR_DIE_LEVEL | TPMI | sv.sockets.sktN.cbbs.cbbX.base.tpmi.plr_die_level | Performance Limit Reason |
| Fast C3 residency | CSR | sv.sockets.sktN.cbbs.cbbX.base.ccf_pma.ring_fastc3_residency | Cycles in Fast Ring C3 |
| CCF PM FSM | CSR | sv.sockets.sktN.cbbs.cbbX.base.ccf_pma.pm_state | Current PM state |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs Affected |
|---|---|---|
| `disable_ring_ee=1` (MSR 0x1FC bit[25]) | Ring scalability disabled — no distress signal generated | 22022421197 (no distress), 22022421207 (Uniform mode interaction) |
| `pll_mode=1` (PLL Crawling / FLL) | Survivability mode — limited step size, longer transitions | 22022421183 (NonAutoGV clocking) |
| UFS_CONTROL MAX_RATIO = MIN_RATIO | Ratio lock — GV disabled, ring runs at fixed frequency | All TCDs (GV transitions suppressed) |
| Uniform CBB Fabric Freq Mode = 1 | Cross-CBB coordination via HPM 0x1b; both CBBs run at max(desired) | 22022421207 (Fast Ring C3) |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| CBB PCode — ring scalability algorithm | PCode CBB source: ring frequency slow-loop, distress handler, BW threshold LUT |
| CBB PCode — GVFSM control | PCode CBB source: ccf_wp write logic, GV state machine interface |
| IMH/NIO Primecode — HPM 0x1b | Primecode source: HPM message aggregation, Fabric DVFS, Uniform mode enforcement |
| CCF PMA — distress generation | RTL: CCF PMA ring-scalability logic, SBO occupancy threshold comparators |
| CCF PMA — CBO counters | RTL: CBO mesh counter accumulator, ingress lookup counter infrastructure |
| BIOS — TPMI_INIT | BIOS source: TpmiSetUfsControl() in TPMI_INIT PH1.x |

---

## Section 3: Validation Strategy

Ring Scalability validation requires a **three-tier** approach because the feature spans firmware algorithm, silicon execution hardware, and cross-die coordination:

- **PSS (VP / HSLE / XOS):** Validates PCode algorithm correctness — BW threshold LUT walk, distress-to-ia_ring_factor conversion, workpoint clamping — in a safe model environment. VP covers firmware logic; HSLE validates single-die GVFSM execution at RTL level; XOS (both dies) is mandatory for HPM 0x1b cross-die protocol and Uniform mode.
- **FV (Post-silicon NWP):** Validates real silicon behavior — actual GVFSM V/F transitions, distress signal latency, PMON counter accuracy, idle exit GV recovery timing, and multi-CBB independence.
- **PV (Post-silicon + OS):** Validates OS-visible frequency behavior under real workloads — intel_pstate driver interaction, sysfs frequency readback, E2E user-visible ring frequency scaling.

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| PCode BW heuristic algorithm bug (wrong threshold, wrong loop count) | ✅ | ⚠️ | ✅ | ✅ | indirect |
| PCode distress-to-ia_ring_factor conversion error | ✅ | ⚠️ | ✅ | ✅ | indirect |
| GVFSM state machine hang or wrong sequence | ❌ | ✅ | ✅ | ✅ | indirect |
| Distress threshold comparator silicon bug | ❌ | ✅ | ✅ | ✅ | indirect |
| CBO/SBO telemetry counter stuck or zero | ❌ | ✅ | ✅ | ✅ | indirect |
| PMON CLR ring_scale_events miscounting | ❌ | ✅ | ✅ | ✅ | indirect |
| HPM 0x1b message lost or wrong value | ❌ | ❌ | ✅ | ✅ | indirect |
| Uniform mode cross-CBB frequency mismatch | ❌ | ❌ | ✅ | ✅ | indirect |
| NonAutoGV PLL/FLL mode transition failure | ❌ | ✅ | ✅ | ✅ | indirect |
| Idle exit GV recovery — wake event lost | ❌ | ✅ | ✅ | ✅ | indirect | *(TCD 22022421209 reparented to TPF 22022420507 — scenario coverage gap under this TPF)* |
| BIOS UFS_CONTROL mis-programming | ✅ (VP safe) | ❌ | ❌ | ✅ | ✅ |
| OS/driver ring frequency visibility | ❌ | ❌ | ❌ | ❌ | ✅ |
| Real-power / TDP convergence impact | ❌ | ❌ | ❌ | ✅ | ✅ |
| BIOS negative validation (invalid UFS_CONTROL) | ✅ safe | ❌ | ❌ | ❌ risky | ❌ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique Value |
|---|---|---|---|---|
| Distress signal path (ia_distress delivery) | ✅ | ✅ | — | FV: real latency; PSS: algorithm correctness |
| BW-driven ring GV sweep (P0..Pm) | ✅ | ✅ | — | FV: real VF curve; PSS: boundary compliance |
| PCode algorithm internals (ia_ring_factor, resolved_ratios) | ✅ | ✅ | — | PSS: inspect PCode vars safely |
| NonAutoGV Fast GV (POR pll_mode=0) | ✅ | ✅ | — | FV: real PLL behavior |
| NonAutoGV PLL Crawling (pll_mode=1) | ✅ | ✅ | — | FV: real FLL step-size behavior |
| Idle exit GV recovery (Active Idle → active) | ✅ | ✅ | — | *(TCD 22022421209 reparented to TPF 22022420507 — scenario no longer under this TPF)* |
| Uniform Fabric Mode across Fast Ring C3 | — | ✅ | — | FV: cross-CBB frequency lock during idle — **⚠️ TCD 22022421207 title says Uniform mode but content/TCs are telemetry counters** |
| CBO/SBO telemetry counter correctness | — | ✅ | — | FV: real counter increment validation |
| PMON CLR ring_scale_events | — | ✅ | — | FV: PMON infrastructure validation |
| OS ring frequency scaling (intel_pstate) | — | — | ✅ | PV: E2E OS-visible frequency |

---

## Section 5: Risks & Dependencies

### Active Risks

- **SBO distress bit-width discrepancy:** Co-Design spec describes ia_distress as 2-bit IA (weak/strong) + 1-bit GT = 3 bits. TCD KB describes ia_distress[3:0] (4-bit, grade 0-15 via 7-threshold logistic regression). **Action:** Verify actual bit-width from RTL or PCode source — spec may be stale or NWP may differ from DMR.
- **PMON CLR ring_scale_events reliability:** PMON counter infrastructure depends on correct CLR event selection (v_sel=0x24). If event encoding changed between DMR→NWP, counters may silently miscount.
- **D2D latency impact on distress response:** NWP D2D PHY upgrade (16→32 GT/s) adds 72-cycle roundtrip latency at 2 GHz. HPM 0x1b cross-die coordination messages may arrive later than expected, affecting Uniform mode response time.
- **Ring C3 exit (PkgC6) is ZBB on NWP:** Full Ring C3 PLL restart not validated. PkgC6→active ring GV recovery requires additional TCD post-ZBB.
- **TCD 22022421209 reparented:** Idle Exit GV Recovery (now "CBB CCF PM x CState") moved to TPF 22022420507 (CCF Active States). Wake event / idle exit coverage is no longer under this TPF.
- **TCD 22022421207 dissolved (T2 ingest 2026-07-19):** Title/content mismatch resolved by dissolution. Telemetry counter content was already reparented; Uniform Fabric Mode coverage requires a separate TCD with spec-cited bar (Co-Design did not provide one — deferred).

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|---|---|---|---|
| **G-1** | OS/driver ring frequency visibility | PV only | Requires booted OS + intel_pstate + intel-speed-select — cannot be tested pre-silicon |
| **G-2** | Real-power / TDP convergence impact of ring scaling | FV + PV only | Model-level power accuracy insufficient; FV power measurement is the isolation environment |
| **G-3** | AutoGV mode (not POR for CBB) | Not tested | AutoGV is disabled in NWP CBB; NonAutoGV is the only POR mode |

---

## Section 6: DFX Considerations

- **PMON CLR counters:** Programmable to count ring-scalability events (RING_SCALE_EVENTS, v_sel=0x24), providing debug visibility into distress and BW heuristic decisions
- **PCode vars (pcode.vars.ring.*):** Ring algorithm internals observable via PythonSV — 
esolved_ratios, ia_distress, ia_ring_factor — critical for root-causing incorrect frequency decisions
- **ring_distress_status CSR:** Direct read of distress grade and validity flags via PMSB — first debug checkpoint when ring frequency not scaling
- **UFS_STATUS / PLR_DIE_LEVEL TPMI:** Live ratio + perf limit reason — identifies whether ring is throttled and why
- **CCF PMA pm_state CSR:** Direct FSM state read — identifies whether CCF is stuck in idle/transition
- **VISA / ITH T2:** CCF PMA distress assertion can be captured via VISA subsystem for timing analysis

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| Both CBBs at max distress simultaneously | NEW-TELEM, 22022421168 | Each CBB independently boosts to P0; Uniform mode enforces max(cbb0, cbb1) |
| Distress oscillation (rapid assert/de-assert) | NEW-TELEM, NEW-PCODE | Hysteresis window (N_OFF loops below LOW threshold) prevents frequency oscillation |
| PEGA injection during active distress | NEW-PCODE, 22022421168 | PEGA overrides BW heuristic but distress workpoint may override PEGA if higher |
| Wake event during GVFSM mid-transition | *(22022421209 — reparented to TPF 22022420507)* | GVFSM must complete current step before processing wake; event must not be lost |
| UFS_CONTROL ratio lock (MAX=MIN) during distress | NEW-PCODE, 22022421168 | GV transitions suppressed; distress grade still generated but ratio clamped |
| Concurrent C-state wake events (core exit + BW request) | *(22022421209 — reparented to TPF 22022420507)* | Highest-priority event wins; lower-priority absorbed or queued |
| PLL Crawling mode idle exit | 22022421183 | FLL step-size limit increases GV recovery time; ratio change must complete correctly |
| CBO counter wrap-around | NEW-TELEM | Counter reset per RSE prevents wrap; verify no stale data after RSE boundary |
| SBO counter disabled + distress expected | NEW-TELEM | No distress generated when SBO counters disabled — expected behavior |
| Uniform mode with one CBB in Fast Ring C3 | *(deferred — Uniform Fabric Mode TCD pending)* | Awake CBB's desired ratio propagated via HPM 0x1b; sleeping CBB receives DOWNSTREAM_RESOLVED_MIN_RATIO on wake |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Segment | TC Count | Notes |
|---|---|---|---|---|
| [22022421168](https://hsdes.intel.com/appstore/article-one/#/22022421168) | CBB CCF GV Control Requests | FV | 3 | ✓ retitled 2026-07-19 (was "PM GV Control Interface"); TC 22022422863 reparented to TCD 22022421174 |
| [22022421183](https://hsdes.intel.com/appstore/article-one/#/22022421183) | CBB CCF[00] NonAutoGV Mode | FV | 2 | ✓ aligned — keep |
| NEW-TELEM | CBB CCF Ring Scalability Telemetry & Distress Generation | FV | 2 | ✓ split from 22022421197; TCs 22022422894, 22022422895 — HSD creation pending |
| NEW-PCODE | CBB PCode Ring-Distress Consumption Algorithm | FV | 1 | ✓ split from 22022421197; TC 22022422905 — HSD creation pending |

> **Dissolved (T2 ingest 2026-07-19):**
> - TCD [22022421197](https://hsdes.intel.com/appstore/article-one/#/22022421197) — [SPLIT] into NEW-TELEM + NEW-PCODE (HW/FW boundary split)
> - TCD [22022421207](https://hsdes.intel.com/appstore/article-one/#/22022421207) — [DISSOLVE] — title/content mismatch, 0 TCs, no bar
> - TC 22022422863 — reparented to existing [TCD 22022421174 (CBB CCF VF Curves)](https://hsdes.intel.com/appstore/article-one/#/22022421174) under TPF 22022420512

> **Reparented:** TCD [22022421209](https://hsdes.intel.com/appstore/article-one/#/22022421209) (now "CBB CCF PM x CState") moved to TPF [22022420507 — CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507). Idle exit GV recovery + C-state wake event coverage is now under that TPF.

### References

- [CBB CCF Power Management HAS — Ring Scalability](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB CCF PM Architecture](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-pm-architecture)
- [Parent TP: CBB CCF PM (22022420505)](https://hsdes.intel.com/appstore/article-one/#/22022420505)
- [TPF 22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514)
- **Lineage sources (T6, ingested 2026-07-18):**
  - [LNL Ring Scalability HAS](https://docs.intel.com/documents/pm_doc/src/lnl/features/ring%20scalability/ring_scalability.html)
  - [LNL CCF PM HAS](https://docs.intel.com/documents/pm_doc/src/lnl/ip%20integration/ccf/lnl_ccf_pm.html)
  - [DMR CBB Power Management Overview](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb%20overview/dmr_cbb_power_management.html)
  - [DMR CBB CCF PM HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/ip%20integration/ccf/cbb_ccf_pm.html)
  - [DMR CBB CCF PM HAS v0.5](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.0.5.html)
  - [DMR CBB CCF PM HAS v1.0](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html)
  - [Ring Scalability MAS (CCF doc)](https://docs.intel.com/documents/ccfdoc/src/cbb/ring_scalability/ring_scalability_mas.html)
  - [LNL CCF IP Spec](https://docs.intel.com/documents/clientsilicon/nvl/ip/ccf/ccf.html)

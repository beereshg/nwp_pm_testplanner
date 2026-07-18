# TCD 22022421004 -- HWP Native Mode

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421004](https://hsdes.intel.com/appstore/article-one/#/22022421004) |
| **Title** | HWP Native Mode |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [22022420483 -- Pstate-HWP](https://hsdes.intel.com/appstore/article-one/#/22022420483) |
| **Child TCs** | [22022422298](https://hsdes.intel.com/appstore/article-one/#/22022422298) -- HWP Autonomous P-state Selection (APS)<br>[22022422301](https://hsdes.intel.com/appstore/article-one/#/22022422301) -- HWP BIOS configuration<br>[22022422303](https://hsdes.intel.com/appstore/article-one/#/22022422303) -- HWP EPP resolution<br>[22022422305](https://hsdes.intel.com/appstore/article-one/#/22022422305) -- HWP Functionality with OS Optin<br>[22022422309](https://hsdes.intel.com/appstore/article-one/#/22022422309) -- HWP Fuse Checks<br>[22022422311](https://hsdes.intel.com/appstore/article-one/#/22022422311) -- HWP Interruptions<br>[22022422312](https://hsdes.intel.com/appstore/article-one/#/22022422312) -- HWP Package/Core level cross-product<br>[22022422317](https://hsdes.intel.com/appstore/article-one/#/22022422317) -- [Solar] P-States-HWP-P0_PN_random |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**HWP (Hardware P-states)** is the modern OS–hardware P-state interface, first introduced in SKX and supported on all server products since. The OS specifies a performance envelope (Min/Max/Desired ratio + EPP) via MSR 0x774 (`IA32_HWP_REQUEST`); the **APS (Autonomous P-state Selection)** algorithm running in **Acode slowloop** (core firmware) selects the optimal frequency within that range. **HWP Native mode** = OS writes MSR 0x774 directly (Linux `intel_pstate` driver).

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.3px;">HWP Native Mode -- End-to-End Data Flow</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <div style="display:flex;gap:0;align-items:flex-start;margin-bottom:12px;flex-wrap:wrap;">
      <div style="background:#e8eaf6;border:2px solid #3949ab;border-radius:6px;padding:8px 12px;min-width:110px;text-align:center;">
        <div style="font-weight:700;color:#3949ab;font-size:11px;">BIOS (CPL3)</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">PM_ENABLE[0]=1<br>Default HWP_REQUEST<br>Native mode select</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">boot</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e8f5e9;border:2px solid #2e7d32;border-radius:6px;padding:8px 12px;min-width:110px;text-align:center;">
        <div style="font-weight:700;color:#2e7d32;font-size:11px;">OS intel_pstate</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">MSR 0x774 writes<br>Min/Max/Desired<br>EPP (0-255)</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">MSR</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;min-width:130px;text-align:center;">
        <div style="font-weight:700;color:#e65100;font-size:11px;">Acode APS/UBPS</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;"><b>Core ACP slowloop</b><br>gain_term = ubps_gain × util<br>+ EET local constraint<br>clips to WP limits ↓</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">~1ms</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#fce4ec;border:2px solid #c62828;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;">
        <div style="font-weight:700;color:#c62828;font-size:11px;">PCode (PUnit)</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">Global constraints:<br>ICCP · PL1/PL2 · Thermal<br>Guardrail (Pn)<br>→ WP registers</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">WP</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e1f5fe;border:2px solid #0277bd;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;">
        <div style="font-weight:700;color:#0277bd;font-size:11px;">Core FIVR+PLL</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">GV transition<br>~few μS<br>PERF_STATUS</div>
      </div>
    </div>
    <div style="background:#e3f2fd;border:1px solid #64b5f6;border-radius:5px;padding:8px 12px;font-size:11px;margin-bottom:8px;">
      <strong>APS Algorithm (UBPS):</strong> Runs per-thread in <b>Acode slowloop</b> (core firmware). Computes target ratio from utilization + EPP, applies EET locally, then clips to WP ceilings/floors provided by <b>PCode</b>. PCode resolves global constraints (ICCP, PL1/PL2, thermal, guardrails) and writes limits to WP registers.
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Validation targets:</strong> (1) HWP_REQUEST envelope honored &nbsp;&#8212;&nbsp; (2) EPP affects frequency response &nbsp;&#8212;&nbsp; (3) Pn guardrail enforced &nbsp;&#8212;&nbsp; (4) HWP_CAPABILITIES matches fuses
    </div>
  </div>
</div>
<!-- /raw-html -->

### Key Concepts

| Concept | Description |
|---------|-------------|
| **HWP** | Hardware P-states — modern OS-to-PCode P-state interface replacing legacy PERF_CTL. First introduced in SKX. |
| **Native mode** | OS directly writes MSR 0x774; Linux `intel_pstate` driver takes control. |
| **OOB mode** | BMC writes TPMI HWP registers; overrides OS MSR 0x774 (tested under separate TCD). |
| **APS** | Autonomous P-state Selection — the algorithm that selects optimal P-state. Runs in **Acode** slowloop (core firmware) per-thread. |
| **UBPS** | Utilization Based P-state Selection — the closed-loop algorithm used by APS. Uses gain/decay terms based on workload utilization. |
| **EPP** | Energy Performance Preference — 8-bit hint (0=max perf, 255=max efficiency). Controls ubps_gain and ratio_decay parameters. |
| **P0n** | Highest_Performance from HWP_CAPABILITIES — max turbo ratio (all-core). |
| **P1** | Guaranteed_Performance — base frequency ratio at TDP. |
| **Pn** | Lowest_Performance (LFM) — minimum efficiency ratio; HW guardrail enforced via GUARDRAIL_CLKI. |
| **ICCP** | Instruction Class Current Profile — dynamic current license based on workload type. |
| **EET** | Energy Efficient Turbo — workload-sensitive turbo attenuation. |
| **PEGA** | Power Event Generation Architecture — PCode firmware feature for injecting C/P-state events via mailboxes (Ucode/TAP). Used for stress testing, not the HWP selection algorithm. |

### APS Algorithm Details (from Core P-state HAS)

The APS algorithm is a **closed-loop UBPS (Utilization Based P-state Selection)** algorithm:

```
// Executed every hcpm_timer expiry (slowloop, ~1 ms)
gain_term = ubps_gain × avg_util
decay_term = ratio_decay × current_core_ratio

if (workload_increasing):
    gain_term dominates → frequency ramps UP
else:
    decay_term dominates → frequency ramps DOWN
```

**EPP Resolution**: EPP can come from multiple sources (OS HWP_REQUEST, OOB override, fuse default). Resolved EPP controls:
- `ubps_gain` — how fast frequency ramps up with utilization
- `ratio_decay` — how fast frequency ramps down when idle
- `rocket_threshold` — threshold for aggressive frequency boost
- `default_activity_window` — observation window for utilization measurement

### NWP-Specific Deltas

- **Same HWP algorithm** — APS/UBPS algorithm unchanged from GNR/DMR; runs in Acode slowloop (core firmware).
- **Pn guardrail** — Minimum ratio enforced via `GUARDRAIL_CLKI.MIN_RATIO` = Pn (typically 8 for 800 MHz).
- **2 CBBs** — fewer cores but same per-core HWP behavior; `range(2)` for CBB iteration.
- **SST-PP removed** — no SST-PP level HWP cross-products; HWP capabilities static after boot.
- **Single NIO** — simplified HWP coordination vs IMH-P root on DMR.
- **Same MSR interfaces** — IA32_PM_ENABLE, IA32_HWP_CAPABILITIES, IA32_HWP_REQUEST unchanged.
- **PantherCove BigCore** — same core architecture as DMR-AP.

### HWP Operating Range (NWP — SKU-dependent typical values)

| Point | Description | Typical Ratio | Typical Frequency |
|-------|-------------|---------------|-------------------|
| **P0n** | Max Turbo (all-core) | 27 | 2.7 GHz |
| **P1** | Guaranteed (base TDP) | 20 | 2.0 GHz |
| **Pn** | LFM (minimum, guardrail) | 8 | 800 MHz |

> **Note:** Actual values are SKU/fuse-dependent. Read from `IA32_HWP_CAPABILITIES` (MSR 0x771) or via mailbox `GET_FREQUENCIES`.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422298 — HWP Autonomous P-state Selection (APS)](https://hsdes.intel.com/appstore/article-one/#/22022422298) | PEGA autonomous selection | Verify PEGA selects frequency within HWP_REQUEST envelope; workload-responsive |
| [22022422301 — HWP BIOS configuration](https://hsdes.intel.com/appstore/article-one/#/22022422301) | Boot-time setup | Verify BIOS enables HWP (PM_ENABLE), sets default HWP_REQUEST, Native mode active |
| [22022422303 — HWP EPP resolution](https://hsdes.intel.com/appstore/article-one/#/22022422303) | EPP effect on frequency | Verify EPP 0→255 range affects PEGA target selection; lower EPP = higher frequency |
| [22022422305 — HWP Functionality with OS Optin](https://hsdes.intel.com/appstore/article-one/#/22022422305) | Native mode operation | Verify OS writes to MSR 0x774 are honored; intel_pstate driver interop |
| [22022422309 — HWP Fuse Checks](https://hsdes.intel.com/appstore/article-one/#/22022422309) | Fuse propagation | Verify HWP_CAPABILITIES reflects fused ratios (P0n, P1, Pn) correctly |
| [22022422311 — HWP Interruptions](https://hsdes.intel.com/appstore/article-one/#/22022422311) | HWP change notification | Verify LVT thermal interrupt on PEGA-selected ratio change; HWP_STATUS flags |
| [22022422312 — HWP Package/Core level cross-product](https://hsdes.intel.com/appstore/article-one/#/22022422312) | Package vs core HWP_REQUEST | Verify HWP_REQUEST_PKG (0x772) vs per-core 0x774 priority/interaction |
| [22022422317 — [Solar] P-States-HWP-P0_PN_random](https://hsdes.intel.com/appstore/article-one/#/22022422317) | Full range stress | Stress test HWP across P0n to Pn range with random workloads |
| **⚠ MISSING — HWP Desired Performance (explicit hint)** | **Desired≠0 targeting** | **Write specific Desired ratio in MSR 0x774[23:16]; verify APS targets exact ratio; EPP informational only; boundary clipping at Min/Max** |
| **⚠ MISSING — HWP Desired mode switching** | **Desired=0 ↔ nonzero transition** | **Toggle Desired between autonomous (0) and explicit at runtime; verify APS mode switch within 1 slowloop** |

---

## Section 2: Interfaces and Protocols

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS (CPL3) | Read CPUID.06H:EAX[7] to verify HWP supported | CPUID |
| 2 | BIOS (CPL3) | Write IA32_PM_ENABLE[0]=1 to enable HWP (write-once per boot) | MSR 0x770 |
| 3 | BIOS (CPL3) | Write default HWP_REQUEST_PKG with min/max/epp values | MSR 0x772 |
| 4 | BIOS (CPL3) | Configure Native vs OOB mode via BIOS knob | BIOS Setup |
| 5 | OS intel_pstate | Verify HWP enabled, read HWP_CAPABILITIES for P0n/P1/Pn | MSR 0x771 |
| 6 | OS intel_pstate | Write IA32_HWP_REQUEST per-core: Min/Max/Desired/EPP | MSR 0x774 |
| 7 | PCode (PUnit) | Resolve global constraints: ICCP license, PL1/PL2, thermal | Slowloop |
| 8 | PCode (PUnit) | Enforce Pn guardrail via GUARDRAIL_CLKI.MIN_RATIO | HW Register |
| 9 | PCode (PUnit) | Write constraint limits to WP registers (Fceil, WP4) | WP Registers |
| 10 | Acode Slowloop | Read HWP_REQUEST fields every ~1ms (hcpm_timer expiry) | Internal |
| 11 | Acode APS/UBPS | Compute gain_term = ubps_gain × avg_util | Algorithm |
| 12 | Acode APS/UBPS | Compute decay_term = ratio_decay × current_ratio | Algorithm |
| 13 | Acode APS/UBPS | Select target_ratio based on gain/decay dominance | Algorithm |
| 14 | Acode | Apply EET attenuation (local constraint) | Algorithm |
| 15 | Acode | Clip target_ratio to PCode-provided WP limits (Fceil, WP4) | Internal |
| 16 | Acode | Issue working point (WP) command to core FIVR controller | Core Mailbox |
| 17 | Core FIVR+PLL | Execute GV transition to new frequency/voltage in ~μS | Hardware |
| 18 | Core | Update IA32_PERF_STATUS with new operating ratio | MSR 0x198 |
| 19 | OS | Read PERF_STATUS to confirm frequency change | MSR 0x198 |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | OS | Core MSR | WRMSR IA32_HWP_REQUEST (0x774) | MSR |
| 2 | Core | Acode | HWP request latched (shadow register) | Internal |
| 3 | PCode | WP Regs | Update Fceil, WP4 with global constraint limits | WP |
| 4 | Acode Timer | APS | hcpm_timer expiry (~1ms) triggers UBPS evaluation | Internal |
| 5 | APS | Thread | Read avg_util from utilization counter | HW Counter |
| 6 | APS | EPP LUT | Lookup ubps_gain, ratio_decay from resolved EPP | Table |
| 7 | APS | Algorithm | Compute gain_term, decay_term | Internal |
| 8 | APS | Algorithm | Select target_ratio = constrain(ubps_result, HWP_MIN, HWP_MAX) | Internal |
| 9 | Acode | EET | Apply EET attenuation (local constraint) | Internal |
| 10 | Acode | WP Regs | Read PCode-provided Fceil/WP4 limits | WP |
| 11 | Acode | Algorithm | Clip target_ratio to Fceil/WP4 limits | Internal |
| 12 | Acode | Core | Issue WP command (ratio, voltage) | Mailbox |
| 13 | Core FIVR | PLL | Configure VID and frequency divider | Hardware |
| 14 | PLL | Core | Clock frequency transition complete | Hardware |
| 15 | Core | MSR | Update IA32_PERF_STATUS with new ratio | Register |

### Interface Table

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| MSR | IA32_PM_ENABLE (0x770) | RW | [0] HWP enable — write 1 once per boot; cannot disable without reboot |
| MSR | IA32_HWP_CAPABILITIES (0x771) | RO | [7:0] Highest (P0n); [15:8] Guaranteed (P1); [23:16] Most Efficient (Pn); [31:24] Lowest |
| MSR | IA32_HWP_REQUEST_PKG (0x772) | RW | Package-level HWP request — applies to all cores unless overridden per-core |
| MSR | IA32_HWP_INTERRUPT (0x773) | RW | [0] CHANGE_NOTIFICATION_EN; [1] ENERGY_PERF_PREFERENCE_CHANGE_EN |
| MSR | IA32_HWP_REQUEST (0x774) | RW | [7:0] Min_Perf (≥Pn); [15:8] Max_Perf; [23:16] Desired (0=auto); [31:24] EPP |
| MSR | IA32_HWP_STATUS (0x777) | RO/RWC | HWP state change flag; cleared by SW |
| MSR | IA32_PERF_STATUS (0x198) | RO | Current operating ratio |
| TPMI | HWP registers | RW (BMC) | OOB HWP request — same fields as MSR 0x774; overrides OS in OOB mode |
| PythonSV | sv.socket0.cbb0.compute0.module0.hwp_request | RW | Per-module HWP request (if exposed) |
| PythonSV | sv.socket0.cbb0.compute0.module0.hwp_capabilities | RO | Per-module HWP capabilities |

---

## Section 3: Reset / Power / Clocking

- **BIOS CPL3**: BIOS enables HWP via `IA32_PM_ENABLE[0] = 1` (write-once per boot). Programs default `HWP_REQUEST` values. Selects Native vs OOB mode via BIOS knob.
- **OS boot**: Linux `intel_pstate` driver detects HWP capability (CPUID.06H:EAX[7]), verifies PM_ENABLE set, takes control of HWP_REQUEST per-core.
- **Acode slowloop**: Acode APS evaluates HWP_REQUEST every ~1 ms (hcpm_timer); uses UBPS algorithm to compute target ratio based on utilization and EPP.
- **PCode constraints**: PCode (PUnit) resolves global constraints (ICCP license, PL1/PL2, thermal, Pn guardrail) and writes limits to WP registers (Fceil, WP4).
- **Acode clipping**: Acode applies local EET constraint, then clips its target ratio to PCode-provided WP limits before issuing GV command.
- **GV transition**: Core FIVR + PLL transition to WP frequency/voltage in ~few μS. `IA32_PERF_STATUS` reflects new ratio.
- **C-state cycle**: HWP_REQUEST persists across C-states; APS re-evaluates on C-state exit if workload changed.
- **Pn guardrail**: Hardware enforces `MIN_RATIO ≥ Pn` via `GUARDRAIL_CLKI.MIN_RATIO` regardless of OS request.

---

## Section 4: Programming Model

HWP Native mode programming follows a sequence from BIOS enable through OS runtime control.

### Stage 1: BIOS Enable (CPL3)

BIOS enables HWP capability and programs initial state:

```
Read CPUID.06H:EAX[7] — verify HWP supported
Write IA32_PM_ENABLE[0] = 1  — enable HWP (write-once)
Write IA32_HWP_REQUEST_PKG = default_min | default_max | 0 | default_epp
Configure BIOS knob: Native mode (OS controls) vs OOB mode (BMC controls)
```

**Constraints:**
- `IA32_PM_ENABLE[0]` is write-once — cannot be cleared without reboot.
- Default HWP_REQUEST values affect boot-time frequency until OS overrides.

### Stage 2: OS Driver Initialization

Linux `intel_pstate` driver takes control:

```
Verify CPUID.06H:EAX[7] = 1 — HWP present
Verify IA32_PM_ENABLE[0] = 1 — HWP enabled
Read IA32_HWP_CAPABILITIES — get P0n, P1, Pn bounds
Write IA32_HWP_REQUEST per-core:
    MIN_PERF = policy_min (≥ Pn)
    MAX_PERF = policy_max (≤ P0n)
    DESIRED = 0 (autonomous) or specific ratio
    EPP = 128 (balanced) or governor-specific
```

### Stage 3: Runtime Operation

OS dynamically adjusts HWP_REQUEST based on cpufreq governor:

| Governor | MIN_PERF | MAX_PERF | DESIRED | EPP |
|----------|----------|----------|---------|-----|
| performance | P0n | P0n | P0n | 0 |
| powersave | Pn | Pn | Pn | 255 |
| schedutil | varies | P0n | 0 (auto) | varies |

### Stage 4: APS Resolution (UBPS Algorithm)

**PCode (PUnit)** resolves global constraints and provides limits to Acode:

```
// PCode slowloop - resolves global constraints:
Fceil = min(ICCP_license_cap, thermal_limit, power_limit)
WP4_min = max(Pn, GUARDRAIL_CLKI.MIN_RATIO)
// Writes Fceil, WP4 to WP registers for Acode to read
```

**Acode (Core)** runs APS/UBPS and clips to PCode limits:

```
// Acode slowloop - every hcpm_timer (~1 ms):
gain_term = ubps_gain[epp] × avg_util
decay_term = ratio_decay[epp] × current_core_ratio

if (gain_term > decay_term):
    ubps_target = ramp_up(current_ratio)
else:
    ubps_target = ramp_down(current_ratio)

// Apply local constraint (EET):
eet_target = apply_eet_attenuation(ubps_target)

// Clip to HWP_REQUEST bounds:
bounded_target = clamp(eet_target, HWP_REQUEST.MIN_PERF, HWP_REQUEST.MAX_PERF)

// Clip to PCode-provided WP limits:
final_ratio = clamp(bounded_target, WP4_min, Fceil)

// Issue working point to core FIVR:
Apply GV transition to final_ratio
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Cold boot (HWP enabled) | PM_ENABLE[0]=1; HWP_CAPABILITIES populated from fuses; APS active from CPL3 |
| OS writes HWP_REQUEST | New envelope takes effect within ~1 ms (slowloop); APS re-evaluates target |
| EPP = 0 (max perf) | APS uses higher ubps_gain → favors higher frequency; faster ramp-up on load |
| EPP = 255 (max efficiency) | APS uses lower ubps_gain → favors lower frequency; slower ramp-up on load |
| **Desired = 0 (autonomous)** | **APS selects frequency autonomously within Min/Max range based on utilization + EPP. This is the default mode (intel_pstate writes Desired=0).** |
| **Desired = nonzero (explicit hint)** | **APS targets the exact Desired ratio (clipped to [Min_Perf, Max_Perf]). EPP becomes informational only — frequency converges to Desired, not utilization-derived.** |
| **Desired > Max_Perf** | **PCode/APS clips Desired to Max_Perf ceiling. No frequency exceedance.** |
| **Desired < Min_Perf** | **PCode/APS raises effective target to Min_Perf floor. HW guardrail enforced.** |
| **Desired transition 0→nonzero→0** | **APS switches between autonomous and explicit targeting within ~1 slowloop. No transient overshoot.** |
| MIN_PERF < Pn requested | HW guardrail clamps to Pn via GUARDRAIL_CLKI.MIN_RATIO |
| HWP change notification enabled | LVT thermal interrupt fires when APS-selected ratio changes |
| Package vs core HWP conflict | Per-core HWP_REQUEST overrides HWP_REQUEST_PKG for that core |
| Thermal throttle active | APS clamps resolved ratio ≤ thermal limit regardless of HWP_REQUEST |

---

## Section 6: Corner Cases & Error Handling

- **Pn clamp behavior**: Test OS requests MIN_PERF < Pn; verify HW guardrail clamps to Pn; no MCA or unexpected behavior.
- **EPP boundary values**: Test EPP = 0, 127, 128, 255; verify frequency response matches EPP expectation.
- **Write-once PM_ENABLE**: Verify second write to PM_ENABLE[0] after boot is ignored (no toggle possible).
- **HWP_CAPABILITIES consistency**: Verify HWP_CAPABILITIES matches fused ratios; no runtime changes.
- **Package vs core priority**: Verify per-core HWP_REQUEST overrides HWP_REQUEST_PKG; test mixed configurations.
- **HWP during C-state**: Verify HWP_REQUEST persists across C1/C1E; APS re-evaluates on exit.
- **HWP interrupt delivery**: Verify LVT thermal vector fires on APS ratio change when CHANGE_NOTIFICATION_EN set.
- **Thermal override**: Verify thermal limit overrides HWP_REQUEST.MAX_PERF; APS respects thermal cap.
- **⚠ GAP — Desired=0 autonomous mode**: No TC explicitly validates that Desired=0 triggers APS autonomous selection (all existing TCs implicitly use Desired=0 but don't verify the autonomous vs explicit mode switch).
- **⚠ GAP — Desired nonzero explicit hint**: No TC writes a specific Desired ratio and verifies PCode/APS targets that exact ratio (clipped to Min/Max). When Desired≠0, EPP should be informational only.
- **⚠ GAP — Desired boundary clipping**: No TC validates Desired > Max_Perf (clip to Max) or Desired < Min_Perf (raise to Min).
- **⚠ GAP — Desired mode transition**: No TC toggles Desired between 0 (autonomous) and nonzero (explicit) at runtime and verifies correct APS mode switching.
- **⚠ GAP — Desired + EPP interaction**: When Desired≠0, EPP should NOT derate frequency — the OS explicitly requested a target ratio. No TC validates this interaction.
- **⚠ GAP — Desired + ICCP**: When Desired=P0n but ICCP license limits to lower ratio, ICCP must win. No TC validates global constraint override of explicit Desired.

---

## Section 7: Security / Safety / Policy

- HWP MSRs are writable only at ring 0 — OS kernel controls HWP_REQUEST.
- Pn guardrail is hardware-enforced via GUARDRAIL_CLKI — OS cannot request frequency below LFM.
- OOB mode (BMC control) completely overrides OS HWP_REQUEST — security boundary at TPMI.
- HWP does not expose internal APS algorithm — only resolved ratio visible via PERF_STATUS.
- No HWP-specific security vulnerabilities documented for NWP.

---

## Section 8: References

- [Pstate-HWP Feature KB -- pstate_hwp.md](../../../pm_features/pstate_stack/pstate_hwp.md)
- [Core P-State HAS -- APS Algorithm §4.17](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html)
- [NWP PM MAS -- P-state range §3](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [PEGA HAS -- High Level Architecture](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
- [PM Debug Handbook -- HWP §3.3.2](https://docs.intel.com/documents/pm_doc/src/server/PM_Debug_Handbook.html)
- [Resource Adapter MAS -- GUARDRAIL_CLKI](https://docs.intel.com/documents/pm_doc/src/Resource_Adapter_MAS.html)
- [Intel SDM -- HWP MSRs](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [Parent TCD HSD 22022421004](https://hsdes.intel.com/appstore/article-one/#/22022421004)

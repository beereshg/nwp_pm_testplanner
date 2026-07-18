# TCD 22022420986 -- EPB and SAPM-DLL

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420986](https://hsdes.intel.com/appstore/article-one/#/22022420986) |
| **Title** | EPB and SAPM - DLL |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [22022420477 -- [NWP PM] P-State / HWP (PNC Core)](https://hsdes.intel.com/appstore/article-one/#/22022420477) |
| **Child TCs** | [22022422281](https://hsdes.intel.com/appstore/article-one/#/22022422281) -- EPB check<br>[22022422284](https://hsdes.intel.com/appstore/article-one/#/22022422284) -- SAPM-DLL check |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**EPB (Energy Performance Bias)** is a 4-bit OS power/performance hint (0–15) programmed via MSR 0x1B0 that influences PCode and system agent behavior. **SAPM-DLL (System Agent Power Management – Dynamic Load-Line)** runs in **CBB PCode** (`flows/sapm/sapm.cpp`) and dynamically switches the internal EPB to performance mode when high turbo residency is detected, optimizing for SPECpower scenarios.

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.3px;">EPB and SAPM-DLL -- End-to-End Data Flow</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <div style="display:flex;gap:0;align-items:flex-start;margin-bottom:12px;flex-wrap:wrap;">
      <div style="background:#e8eaf6;border:2px solid #3949ab;border-radius:6px;padding:8px 12px;min-width:110px;text-align:center;">
        <div style="font-weight:700;color:#3949ab;font-size:11px;">OS / BIOS</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">MSR 0x1B0<br>EPB = 0-15<br>(0=perf, 15=save)</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">write</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e8f5e9;border:2px solid #2e7d32;border-radius:6px;padding:8px 12px;min-width:130px;text-align:center;">
        <div style="font-weight:700;color:#2e7d32;font-size:11px;">EPB Resolution</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">Source select:<br>BIOS vs OS<br>(POWER_CTL[34])</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">4-bit</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;min-width:130px;text-align:center;">
        <div style="font-weight:700;color:#e65100;font-size:11px;">PCode SAPM-DLL</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;"><b>CBB PCode flow</b><br>sapm.cpp slow loop<br>Monitor C0P0/C0<br>EWMA + threshold<br>EPB → 0 (perf)</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">~1ms</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#fce4ec;border:2px solid #c62828;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;">
        <div style="font-weight:700;color:#c62828;font-size:11px;">PCode / Agents</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">Use resolved EPB<br>for PM decisions<br>(RAPL, throttle)</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">hint</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e1f5fe;border:2px solid #0277bd;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;">
        <div style="font-weight:700;color:#0277bd;font-size:11px;">HWP APS</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">EPP (if disabled)<br>derived from EPB<br>EPP = EPB << 4</div>
      </div>
    </div>
    <div style="background:#e3f2fd;border:1px solid #64b5f6;border-radius:5px;padding:8px 12px;font-size:11px;margin-bottom:8px;">
      <strong>SAPM-DLL Logic:</strong> Monitors turbo residency (C0P0_time / C0_time). If ratio exceeds <code>P0_TOTAL_TIME_THRESHOLD_HIGH</code>, EPB switches to 0 (performance). When ratio drops below <code>P0_TOTAL_TIME_THRESHOLD_LOW</code>, EPB reverts to programmed value.
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Validation targets:</strong> (1) EPB source resolution (BIOS vs OS) &nbsp;&#8212;&nbsp; (2) EPB value read-back correct &nbsp;&#8212;&nbsp; (3) SAPM-DLL dynamic switching works &nbsp;&#8212;&nbsp; (4) EPB→EPP derivation when EPP disabled
    </div>
  </div>
</div>
<!-- /raw-html -->

### EPB Value Mapping

| EPB Value | Mode | Description |
|-----------|------|-------------|
| 0–3 | Performance | Favor high frequency, less aggressive power saving |
| 4–7 | Balanced Performance | Slight performance bias |
| 8–11 | Balanced Power | Slight power saving bias |
| 12–15 | Power Saving | Favor energy efficiency |

> **Note:** Only the upper 2 bits of EPB are used internally, mapping 16 values to 4 effective modes.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **EPB** | Energy Performance Bias — 4-bit hint (0=perf, 15=save) in MSR 0x1B0 |
| **SAPM-DLL** | System Agent Power Management – Dynamic Load-Line — implemented in **CBB PCode** (`flows/sapm/sapm.cpp`); dynamically overrides EPB to performance under high turbo load |
| **C0P0 residency** | Fraction of time core requests turbo (P0) while active (C0) |
| **P0_THRESHOLD_HIGH** | SAPM-DLL threshold to switch EPB to performance (ratio > threshold) |
| **P0_THRESHOLD_LOW** | SAPM-DLL threshold to revert EPB to programmed value (ratio < threshold) |
| **EPB Source** | BIOS-controlled (POWER_CTL[34]=1) or OS-controlled (POWER_CTL[34]=0) |
| **EPP derivation** | If HWP EPP disabled, EPP = EPB << 4 (EPB 0-15 → EPP 0-240) |

### NWP-Specific Deltas

- **2 CBBs only** — SAPM-DLL iterates over 2 CCPs (cbb0, cbb1) instead of 4 on DMR.
- **NIO root die** — EPB config registers accessed via `sv.socket0.nio0.punit.*`, not `imh0`.
- **Same EPB mechanism** — MSR 0x1B0, same 4-bit encoding, same source resolution via POWER_CTL.
- **Same SAPM-DLL algorithm** — PCode `flows/sapm/sapm.cpp` identical flow (EWMA C0P0/C0, threshold-based EPB override, HPM `SAPM_OUTPUT_EPB` reporting).

### PCode Implementation Details

- **SAPM-DLL runs in CBB PCode** — `flows/sapm/sapm.cpp` registers as `FlowID::sapm`. Not in Acode.
- **PCode slow loop** — `accumulate_c0p0_tx()` runs on both fast path (preq shaping) and slow loop (~1ms).
- **Per-CCP EPB resolution** — `resolve_epb_tx(ccp_id)` computes EWMA of C0P0/C0 ratio per CCP; `get_epb(ccp_id)` returns resolved value.
- **EPB priority in `get_epb_value()`**: (1) BIOS (`PWR_PERF_TUNING_CFG_MODE=1` → `ALT_ENERGY_PERF_BIAS`), (2) PECI override (`bios_mbx_epb_peci_override_enable`), (3) OS (`CCP_P_REQ.ENERGY_EFFICIENCY_POLICY`).
- **P-alpha consumes resolved EPB** — `palpha.cpp` calls `sapm.get_epb(ccp_id)` for EET frequency deration.
- **HPM reporting** — `report_hpm_tx()` sends `SAPM_OUTPUT_EPB` message to IMH/NIO.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422281 — EPB check](https://hsdes.intel.com/appstore/article-one/#/22022422281) | EPB resolution | Verify EPB source resolution (BIOS vs OS), MSR 0x1B0 read/write, EPB value effect on PM |
| [22022422284 — SAPM-DLL check](https://hsdes.intel.com/appstore/article-one/#/22022422284) | SAPM-DLL switching | Verify SAPM-DLL dynamic EPB override under high turbo load; threshold behavior |

---

## Section 2: Interfaces and Protocols

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS (CPL3) | Configure EPB source via MSR_POWER_CTL[34] (0=OS, 1=BIOS) | MSR 0x1FC |
| 2 | BIOS (CPL3) | Write ALT_ENERGY_PERF_BIAS in ENERGY_PERF_BIAS_CONFIG if BIOS-controlled | MSR 0xA01 |
| 3 | BIOS (CPL3) | Enable SAPM-DLL via MSR_POWER_CTL[33]=1 | MSR 0x1FC |
| 4 | BIOS (CPL3) | Configure SAPM-DLL thresholds (HIGH/LOW) in ENERGY_PERF_BIAS_CONFIG | MSR 0xA01 |
| 5 | OS | Write IA32_ENERGY_PERF_BIAS[3:0] with desired EPB value (if OS-controlled) | MSR 0x1B0 |
| 6 | PCode | Read EPB from resolved source (OS MSR or BIOS config) | Internal |
| 7 | PCode SAPM-DLL | Monitor C0P0 / C0 turbo residency ratio (EWMA, `accumulate_c0p0_tx`) | HW Counter |
| 8 | PCode SAPM-DLL | If ratio > P0_THRESHOLD_HIGH, override EPB to 0 (performance) | `resolve_epb_tx` |
| 9 | PCode SAPM-DLL | If ratio < P0_THRESHOLD_LOW, revert EPB to programmed value | `resolve_epb_tx` |
| 10 | PCode SAPM-DLL | Report resolved EPB via HPM `SAPM_OUTPUT_EPB` to IMH/NIO | `report_hpm_tx` |
| 11 | PCode P-alpha | Consume `sapm.get_epb(ccp_id)` for EET frequency deration | `palpha.cpp` |
| 12 | PCode APS | If HWP EPP disabled, derive EPP = EPB << 4 | Internal |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | OS | Core MSR | WRMSR IA32_ENERGY_PERF_BIAS (0x1B0) | MSR |
| 2 | PCode | EPB Resolver | Read EPB from OS MSR or BIOS ALT_EPB (`get_epb_value()`) | Internal |
| 3 | PCode | SAPM-DLL | Read resolved EPB as baseline | `sapm.cpp` |
| 4 | SAPM-DLL | HW Counter | Sample PKG_IA_C0 per LP (`accumulate_c0p0_tx`) | Counter |
| 5 | SAPM-DLL | EWMA Filter | Compute `avg_c0p0_over_c0 = alpha*curr + (1-alpha)*prev` | `resolve_epb_tx` |
| 6 | SAPM-DLL | Threshold | Compare ratio vs HIGH/LOW thresholds (U0.6 format) | Internal |
| 7 | SAPM-DLL | EPB Override | If HIGH exceeded, set `resolved_epb = performance` | Internal |
| 8 | PCode | HPM | Send `SAPM_OUTPUT_EPB` to IMH/NIO | `report_hpm_tx` |
| 9 | P-alpha | SAPM-DLL | Read `sapm.get_epb(ccp_id)` for EET | `palpha.cpp` |
| 10 | APS | EPP LUT | If EPP disabled, derive EPP = EPB << 4 | Table |

### Interface Table

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| MSR | IA32_ENERGY_PERF_BIAS (0x1B0) | RW | [3:0] EPB value (0=perf, 15=save); thread scope |
| MSR | MSR_POWER_CTL (0x1FC) | RW | [18] PWR_PERF_PLTFRM_OVR; [33] SAPM-DLL enable; [34] EPB source select |
| MSR | ENERGY_PERF_BIAS_CONFIG (0xA01) | RW | [6:3] ALT_EPB (BIOS); [17:12] P0_HIGH; [23:18] P0_LOW; [31:24] AVG_WINDOW |
| HW | C0P0 counter | RO | Time spent in turbo (P0) while active (C0) |
| HW | C0 counter | RO | Total active time |
| Internal | Resolved EPB | — | 4-bit value computed by PCode SAPM-DLL (`resolve_epb_tx`), consumed by P-alpha and agents |

---

## Section 3: Reset / Power / Clocking

- **BIOS CPL3**: BIOS configures EPB source (POWER_CTL[34]), SAPM-DLL enable (POWER_CTL[33]), and thresholds (MSR 0xA01). Sets ALT_EPB if BIOS-controlled.
- **OS boot**: OS writes IA32_ENERGY_PERF_BIAS if OS-controlled (POWER_CTL[34]=0).
- **SAPM-DLL active**: PCode SAPM-DLL (`resolve_epb_tx`) monitors turbo residency and dynamically overrides EPB when thresholds crossed.
- **Reset behavior**: EPB and SAPM-DLL config persists across warm reset; cold reset restores BIOS defaults.
- **Power domain**: EPB is per-thread MSR; SAPM-DLL operates at per-CCP level in PCode slow loop (~1ms).

---

## Section 4: Programming Model

### Stage 1: BIOS Configuration

\\\
// Select EPB source:
Write MSR_POWER_CTL[34]:
  0 = OS controls EPB via MSR 0x1B0
  1 = BIOS controls EPB via ALT_ENERGY_PERF_BIAS

// If BIOS-controlled, set default EPB:
Write ENERGY_PERF_BIAS_CONFIG[6:3] = ALT_ENERGY_PERF_BIAS (0-15)

// Enable SAPM-DLL:
Write MSR_POWER_CTL[33] = 1

// Configure SAPM-DLL thresholds:
Write ENERGY_PERF_BIAS_CONFIG[17:12] = P0_TOTAL_TIME_THRESHOLD_HIGH
Write ENERGY_PERF_BIAS_CONFIG[23:18] = P0_TOTAL_TIME_THRESHOLD_LOW
Write ENERGY_PERF_BIAS_CONFIG[31:24] = AVG_TIME_WINDOW (decay constant)
\\\

### Stage 2: OS Runtime (if OS-controlled)

\\\
// Set EPB per-thread:
Write IA32_ENERGY_PERF_BIAS[3:0] = desired_epb (0=perf, 15=save)

// Typically set via:
//   Linux: /sys/devices/system/cpu/cpuX/power/energy_perf_bias
//   or: x86_energy_perf_policy tool
\\\

### Stage 3: SAPM-DLL Runtime (PCode `flows/sapm/sapm.cpp`)

```
// PCode slow loop — SAPM-DLL flow:
// accumulate_c0p0_tx: reads PKG_IA_C0 per LP; accumulates C0P0 if desired >= P1-offset
// update_configuration_tx: reads POWER_CTL.PWR_PERF_TUNING_ENABLE_DYN_SWITCHING,
//   ENERGY_PERF_BIAS_CONFIG thresholds (U0.6), computes EWMA alpha
// resolve_epb_tx(ccp_id):
ratio = max_c0p0 / max_c0  // clamped to [0,1]
avg = alpha * ratio + (1-alpha) * prev_avg   // EWMA

if (avg > P0_THRESHOLD_HIGH):
    resolved_epb = EnergyPerformanceBias::performance  // EPB = 0
elif (avg < P0_THRESHOLD_LOW):
    resolved_epb = get_input_epb(ccp_id)  // Revert to OS/BIOS/PECI value
else:
    // Hysteresis — maintain current state

// EPB priority in get_epb_value():
//   1. BIOS (PWR_PERF_TUNING_CFG_MODE=1) → ALT_ENERGY_PERF_BIAS
//   2. PECI override (bios_mbx_epb_peci_override_enable + valid HPM) → PECI_EPB
//   3. OS (default) → CCP_P_REQ.ENERGY_EFFICIENCY_POLICY
```
---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| OS writes EPB = 8 (balanced power) | If OS-controlled, PCode SAPM-DLL may override to 0 under high turbo load |
| High turbo workload | SAPM-DLL detects C0P0/C0 > HIGH threshold; EPB switches to 0 |
| Workload drops | SAPM-DLL detects C0P0/C0 < LOW threshold; EPB reverts to programmed |
| BIOS-controlled EPB | OS writes to MSR 0x1B0 ignored; BIOS ALT_EPB used |
| SAPM-DLL disabled | EPB never overridden; programmed value always used |
| HWP EPP enabled | EPP from HWP_REQUEST used; EPB is informational only |
| HWP EPP disabled | EPP derived from EPB: EPP = EPB << 4 |

---

## Section 6: Corner Cases & Error Handling

- **EPB source conflict**: Verify OS writes ignored when BIOS-controlled (POWER_CTL[34]=1).
- **SAPM-DLL threshold tuning**: Verify hysteresis between HIGH and LOW prevents oscillation.
- **SAPM-DLL + Turbo Disable**: Verify SAPM-DLL has no effect when turbo is disabled (no P0 residency).
- **EPB per-thread vs per-CCP**: Verify EPB is per-thread MSR but SAPM-DLL resolves per-CCP in PCode.
- **Reset persistence**: Verify EPB value survives warm reset; verify BIOS re-programs on cold reset.
- **EPB + HWP interaction**: Verify EPP derivation from EPB only when EPP explicitly disabled.

---

## Section 7: Security / Safety / Policy

- EPB is ring-0 writable — OS kernel controls power/performance policy.
- BIOS can lock out OS control via POWER_CTL[34]=1 — platform policy override.
- SAPM-DLL is transparent to OS — no security surface.
- EPB does not directly affect security features; impacts power/frequency only.

---

## Section 8: References

- [Pstate-EPB and SAPM-DLL Feature KB](../../../pm_features/pstate_stack/pstate_epb_and_sapm_dll.md)
- [Core P-State HAS — EPB and SAPM-DLL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html)
- [NWP PM MAS — EPB](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel SDM — IA32_ENERGY_PERF_BIAS MSR](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [Parent TCD HSD 22022420986](https://hsdes.intel.com/appstore/article-one/#/22022420986)

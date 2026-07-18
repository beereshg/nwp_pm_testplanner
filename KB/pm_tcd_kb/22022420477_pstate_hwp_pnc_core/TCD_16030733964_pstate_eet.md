# TCD 16030733964 -- Pstate - EET

| Field | Value |
|-------|-------|
| **TCD ID** | [16030733964](https://hsdes.intel.com/appstore/article-one/#/16030733964) |
| **Title** | Pstate - EET |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [22022420477 -- [NWP PM] P-State / HWP (PNC Core)](https://hsdes.intel.com/appstore/article-one/#/22022420477) |
| **Child TCs** | [16030734092](https://hsdes.intel.com/appstore/article-one/#/16030734092) -- Pstate - EET flow verification |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Energy Efficient Turbo (EET)** dynamically attenuates turbo frequency based on workload scalability. If the workload is memory-bound (low IPC, high cache miss), increasing frequency provides little performance benefit — EET derates the request to save power.

> **NWP uses the same CBB as DMR.** Per the authoritative [DMR CBB EET FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/EET/eet.html): *"This document describes the changes in the requirements and implementation of the 'Energy Efficient Turbo' (EET) algorithm in **DMR CBB PCode**..."*

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.3px;">EET — CBB PCode Architecture (NWP = DMR CBB)</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <!-- Row 1: EET in PCode -->
    <div style="margin-bottom:16px;">
      <div style="font-size:10px;color:#0f4c81;font-weight:700;margin-bottom:8px;border-bottom:1px dashed #90caf9;padding-bottom:4px;">EET Path (PCode — scalability + deration):</div>
      <table style="border-collapse:separate;border-spacing:8px 0;margin:0 auto;">
        <tr>
          <td style="background:#f3e5f5;border:2px solid #7b1fa2;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#7b1fa2;font-size:11px;">🔢 Core Telemetry</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;"><b>HW PMU</b><br>L1/L2/L3 stalls<br>SQ Occupancy<br>C0 residency</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#7b1fa2;font-size:10px;">→telem→</span></td>
          <td rowspan="1" style="background:#ede7f6;border:2px solid #5e35b1;border-radius:6px;padding:10px 14px;min-width:180px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#5e35b1;font-size:11px;">⚙️ PCode EET</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;"><b>CBB PUNIT Slowloop</b><br>Scalability LUT<br>EPB from SAPM</div>
            <div style="margin-top:8px;padding-top:8px;border-top:1px dashed #5e35b1;">
              <div style="font-weight:700;color:#c62828;font-size:10px;">📉 Output: derated_p_req</div>
              <div style="font-size:9px;color:#555;">Module-level → P-state stack</div>
            </div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#2e7d32;font-size:10px;">←EPB←</span></td>
          <td style="background:#e8f5e9;border:2px solid #2e7d32;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#2e7d32;font-size:11px;">📊 PCode SAPM</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;"><b>CBB PUNIT</b><br>Resolved EPB<br>(0-15)</div>
          </td>
        </tr>
      </table>
    </div>
    <!-- Row 2: P-State Stack -->
    <div style="margin-bottom:12px;">
      <div style="font-size:10px;color:#0f4c81;font-weight:700;margin-bottom:8px;border-bottom:1px dashed #90caf9;padding-bottom:4px;">P-State Stack (HWP_REQUEST → derated → final freq):</div>
      <table style="border-collapse:separate;border-spacing:8px 0;margin:0 auto;">
        <tr>
          <td style="background:#e8eaf6;border:2px solid #3949ab;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#3949ab;font-size:11px;">💻 OS</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">HWP_REQUEST<br>MSR per-thread<br>(EPP, min, max)</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#555;">→</span></td>
          <td style="background:#e1f5fe;border:2px solid #0277bd;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#0277bd;font-size:11px;">⚡ PCode APS</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;"><b>CBB PUNIT</b><br>P-state selection<br>→ EET derate</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#c62828;">↑derate↑</span></td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#555;">→</span></td>
          <td style="background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#e65100;font-size:11px;">🔒 PCode Limits</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;"><b>CBB PUNIT</b><br>WP, TRL, FACT<br>Thermal</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#555;">→Feff→</span></td>
          <td style="background:#e0f2f1;border:2px solid #00796b;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#00796b;font-size:11px;">🎯 Module Freq</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">Final granted<br>to core PLLs</div>
          </td>
        </tr>
      </table>
    </div>
    <div style="background:#e3f2fd;border:1px solid #64b5f6;border-radius:5px;padding:8px 12px;font-size:11px;margin-bottom:8px;">
      <strong>HAS Reference:</strong> <a href="https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/EET/eet.html">DMR CBB EET FAS</a> — EET implemented in <b>PCode</b> on CBB PUNIT. NWP uses same CBB.
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Scalability:</strong> Weighted sum of C0, L1/L2/L3 stalls, SQ occupancy → LUT → freq_scale_factor. Deration: <code>derated_p_req = ratio_in - freq_scale_factor × (ratio_in - floor_ratio)</code>
    </div>
  </div>
</div>
<!-- /raw-html -->
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Scalability:</strong> <code>(C0 - L2_stall - L3_stall - SQ_stall) / C0</code> → LUT → deration factor. APS applies: <code>Ft = Ft_base × (1 - freq_deration_factor[c])</code>
    </div>
  </div>
</div>
<!-- /raw-html -->

### CBB PCode — Algorithm Locations (NWP = DMR CBB)

| Algorithm | Location | Scope | Function | HAS Reference |
|-----------|----------|-------|----------|---------------|
| **EET** | **PCode (CBB PUNIT)** | Module | Process stall telemetry, compute scalability via 2D LUT, derate P-state request | [DMR CBB EET FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/EET/eet.html) |
| **SAPM** | **PCode (CBB PUNIT)** | Module | Compute EPI, resolve EPB, report to PrimeCode | [DMR P-State Stack HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |
| **APS** | **PCode (CBB PUNIT)** | Module | P-state selection, receives EET derated request | [DMR Firmware Arch](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) |
| **Global Limits** | **PCode (CBB PUNIT)** | Module/Package | WP, TRL, FACT, thermal constraints | DMR CBB HAS |

### EET Stall Counters (HW PMU → PCode)

| Counter | Description | Usage |
|---------|-------------|-------|
| **L1 Stall Cycles** | Cycles stalled on L1 cache | Low weight (fast cache) |
| **L2 Stall Cycles (MLC)** | Cycles stalled on L2 cache miss | Medium weight |
| **L3 Stall Cycles (LLC)** | Cycles stalled on L3 cache miss | High weight (memory-bound indicator) |
| **SQ Occupancy** | Store queue / outstanding memory transactions | Memory pressure indicator |
| **C0 Residency** | Active cycles | Denominator for scalability ratio |

### Scalability Calculation (PCode)

```
// PCode EET — from eet_and_scalability.cpp (PrimeCode firmware):

// Weighted stall formula:
weighted_stall_count = 
    A_c0_multiplier * C0_residency           // 1.0
  + B_l1_stall_multiplier * L1_stalls        // -2.55
  + C_l2_stall_multiplier * L2_stalls        // 1.15
  + D_l3_stall_multiplier * L3_stalls        // 0.0 (platform tunable)
  + E_sq_occupency_multiplier * SQ_OCCUPENCY // 0.0 (platform tunable)

module_scalability = weighted_stall_count / C0_residency
// Clamped to [0.0, 1.0]

// 2D LUT lookup: eet_freq_scale_factor[EPB][scalability_bin]
freq_scale_factor = eet_freq_scale_factor[output_epb][floor(scalability * 16)]

// Deration formula:
derated_p_req = ratio_in - floor(freq_scale_factor × (ratio_in - floor_ratio))
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **EET** | Energy Efficient Turbo — **runs in PCode (CBB PUNIT)**; derates turbo for memory-bound workloads |
| **Scalability** | Measure of useful work vs stall cycles (0-1); weighted sum formula |
| **freq_scale_factor** | 2D LUT indexed by [EPB][scalability_bin]; determines deration amount |
| **derated_p_req** | Module-level derated P-state request; output of EET algorithm |
| **APS** | Autonomous P-State Selection; runs in PCode; receives EET derated request |
| **SAPM** | Software Autonomous Power Management; runs in PCode; computes EPI, resolves EPB |

### NWP = DMR CBB (Same Architecture)

NWP is a **derivative of DMR** and uses the **same CBB**. Per the authoritative DMR CBB HAS:

| Algorithm | Execution Location | HAS Document |
|-----------|-------------------|--------------|
| **EET** | PCode (CBB PUNIT) | [DMR CBB EET FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/EET/eet.html) |
| **APS** | PCode (CBB PUNIT) | [DMR Firmware Arch](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) |
| **SAPM** | PCode (CBB PUNIT) | [DMR P-State Stack HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) |

**Note:** Since NWP uses the same CBB as DMR, the EET/APS/SAPM algorithms run in PCode for both platforms.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [16030734092 — Pstate - EET flow verification](https://hsdes.intel.com/appstore/article-one/#/16030734092) | EET flow | Verify EET scalability calculation, freq_deration_factor, APS integration |

---

## Section 2: Interfaces and Protocols

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Check CAPID4.EET_EN fuse; skip EET init if disabled | Fuse |
| 2 | BIOS | Configure EET scalability LUT parameters | MMIO |
| 3 | OS | Write HWP_REQUEST MSR per-thread (EPP, min, max, desired) | MSR |
| 4 | PCode EET | Read core telemetry: L1, L2/MLC, L3/LLC stalls, SQ Occupancy, C0 | HW Telem |
| 5 | PCode EET | Compute weighted scalability = f(C0, stalls) | Algorithm |
| 6 | PCode EET | 2D LUT lookup: eet_freq_scale_factor[EPB][scalability_bin] | LUT |
| 7 | PCode SAPM | Provide resolved EPB (0-15) | Internal |
| 8 | PCode EET | Compute derated_p_req = ratio_in - freq_scale_factor × (ratio_in - floor) | Algorithm |
| 9 | PCode APS | Receive derated_p_req from EET | Internal |
| 10 | PCode APS | Apply to P-state selection | Algorithm |
| 11 | PCode | Apply global limits (WP, TRL, FACT) | Internal |
| 12 | PCode | Grant final frequency to module PLLs | Internal |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | BIOS | Fuse | Read CAPID4.EET_EN | Fuse |
| 2 | BIOS | Acode | Configure EET LUT | MMIO |
| 3 | OS | MSR | Write HWP_REQUEST | MSR |
| 4 | Acode | Stall Counters | Read L1/L2/L3/SQ/C0 | Counter |
| 5 | Acode | EET | Compute raw scalability | Algorithm |
| 6 | Acode | LUT | Table lookup → scalability_factor | Table |
| 7 | Acode | SAPM-DLL | Get resolved EPB | Internal |
| 8 | Acode | EET | Compute freq_deration_factor[c] | Algorithm |
| 9 | EET | APS/UBPS | Pass freq_deration_factor[c] | Internal |
| 10 | Acode | APS | Compute Ft with deration | Algorithm |
| 11 | Acode | PCode | Write Ft | Shared Reg |
| 12 | PCode | Module | Grant frequency | Internal |

### Interface Table

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| Fuse | CAPID4.EET_EN | RO | EET feature enable fuse |
| HW Counter | L1_STALL_COUNT | RO | L1 cache stall cycles |
| HW Counter | STALL_COUNT0 / MISC_MOD_COUNT3 | RO | L2/MLC stall cycles |
| HW Counter | STALL_COUNT1 / MOD_THROT_COUNT0 | RO | L3/LLC stall cycles |
| HW Counter | MISC_MOD_COUNT1 | RO | SQ Occupancy |
| HW Counter | C0_RES_COUNT | RO | C0 residency (active cycles) |
| LUT | SCALABILITY_LUT | RO | Firmware scalability table |
| Internal | resolved_epb | — | 4-bit value from SAPM-DLL |
| Internal | freq_deration_factor[c] | — | Per-core deration; input to APS |
| MSR | HWP_REQUEST | RW | OS target frequency request |

---

## Section 3: Reset / Power / Clocking

- **BIOS CPL3**: BIOS checks CAPID4.EET_EN fuse and configures EET LUT parameters.
- **Warm reset**: EET config persists; stall counters reset.
- **Cold reset**: BIOS re-programs EET; counters reset.
- **Power domain**: EET runs per-core in Acode Slowloop.
- **Clock dependency**: EET sampling tied to Acode Slowloop period.

---

## Section 4: Programming Model

### Stage 1: BIOS Configuration

\\\
// Check EET fuse:
if (CAPID4.EET_EN == 0):
    // EET disabled by fuse — skip init
    return

// Configure EET scalability LUT (firmware table):
// LUT maps raw_scalability (0-100%) to deration factor
for i in range(NUM_BUCKETS):
    Write SCALABILITY_LUT[i] = platform_tuned_values[i]
\\\

### Stage 2: Acode EET (Per-Core — runs in Acode Slowloop)

\\\
// Acode Slowloop — EET moved here in ACP model:

// Sample stall counters:
l1_stall = read(L1_STALL_COUNT)
l2_stall = read(STALL_COUNT0)  // MLC
l3_stall = read(STALL_COUNT1)  // LLC
sq_occ = read(MISC_MOD_COUNT1)
c0_res = read(C0_RES_COUNT)

// Compute raw scalability:
total_stall = l2_stall + l3_stall + sq_occ  // L1 may be excluded or low-weighted
raw_scalability = (c0_res - total_stall) / c0_res  // 0 = all stalls, 1 = no stalls

// Table lookup:
scalability_index = quantize(raw_scalability, NUM_BUCKETS)
scalability_factor = SCALABILITY_LUT[scalability_index]

// Get resolved EPB from SAPM-DLL:
resolved_epb = get_sapm_dll_epb()  // 0=perf, 15=power_save

// Compute freq_deration_factor for this core:
// Higher EPB + lower scalability = more deration
freq_deration_factor[c] = compute_deration(scalability_factor, resolved_epb)

// Pass to APS/UBPS as input:
// freq_deration_factor[c] is used by Autonomous HWP
\\\

### Stage 3: Acode APS/UBPS (Per-Core — uses EET deration)

\\\
// Acode Slowloop — APS/UBPS receives EET deration:

// Read OS request:
hwp_req = read_msr(HWP_REQUEST)
epp = hwp_req.EPP
min_perf = hwp_req.MIN_PERF
max_perf = hwp_req.MAX_PERF

// Compute base target frequency:
Ft_base = aps_ubps_algorithm(epp, utilization, min_perf, max_perf)

// Apply EET deration:
Ft_derated = Ft_base * (1 - freq_deration_factor[c])

// Write to shared register for PCode:
write_shared(HWP_REQUEST_SUPPLEMENTAL, Ft_derated)
\\\

### Stage 4: PCode (Module — Global Limits Only)

\\\
// PCode — applies global constraints:

// Read derated Ft from Acode:
Ft = read_shared(HWP_REQUEST_SUPPLEMENTAL)

// Apply global limits:
Ft_final = min(Ft, WP_limit, TRL_limit, FACT_limit)

// Grant frequency:
grant_frequency(Ft_final)
\\\

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Compute-bound workload | Low stalls; scalability ≈ 1; minimal deration |
| Memory-bound workload | High L3/SQ stalls; scalability ≈ 0; aggressive deration |
| EPB = 0 (performance) | Less aggressive deration regardless of scalability |
| EPB = 15 (power save) | More aggressive deration when scalability low |
| CAPID4.EET_EN = 0 | EET disabled; freq_deration_factor = 0 always |
| Turbo disabled | No turbo to derate; EET has no effect |

---

## Section 6: Corner Cases & Error Handling

- **Zero C0 residency**: Verify EET handles divide-by-zero (idle cores).
- **Counter overflow**: Verify delta calculation handles counter wrap.
- **LUT boundary**: Verify scalability_index clamps to valid LUT range.
- **EET + thermal throttle**: Verify EET deration combines with thermal limits.
- **EET + RAPL**: Verify EET works in conjunction with power limits.
- **Per-core vs module**: Verify freq_deration_factor[c] correctly per-core.

---

## Section 7: Security / Safety / Policy

- EET is Acode-internal; no direct OS control surface.
- CAPID4.EET_EN fuse is read-only — manufacturing-set.
- Scalability LUT is firmware-defined; not OS-modifiable.
- EET does not affect security features; impacts power/frequency only.

---

## Section 8: References

- [Autonomous Core Perimeter PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/autonomous%20core%20perimeter/autonomous%20core%20perimeter%20pm%20has.html) — **EET moves to Acode Slowloop**
- [ACP-CCP Backward Compatibility](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/autonomous%20core%20perimeter/autonomous%20core%20perimeter%20pm%20has.html#acp-ccp-backward-compatibility) — EET in Acode, scalability LUT
- NWP HAS: Global IDs — CAPID4.EET_EN
- KB: [KB/pm_features/pstate_stack/pstate_stack_main.md](../../pm_features/pstate_stack/pstate_stack_main.md)

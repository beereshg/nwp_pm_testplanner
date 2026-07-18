# TCD 22022420993 -- Flex ratio configuration and functionality

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420993](https://hsdes.intel.com/appstore/article-one/#/22022420993) |
| **Title** | Flex ratio configuration and functionality |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [16030732015 -- Pstate Operating Range](https://hsdes.intel.com/appstore/article-one/#/16030732015) |
| **Child TCs** | 2 TCs (Flex Ratio base, Flex Ratio x SST cross-product) |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Flex Ratio** clips the guaranteed ratio (P1) to a BIOS-configured value via soft-strap delivered from PrimeCode to PCode at reset exit. This allows power management, binning, or SKU differentiation by limiting the maximum guaranteed frequency.

> **HAS Reference:** [DMR CBB P-State Stack HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) — Flex Ratio configuration, DISTRIBUTE_STRAPS_CBB delivery mechanism.

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.3px;">Flex Ratio — P1 Clipping Flow (PrimeCode → PCode)</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <div style="margin-bottom:16px;">
      <div style="font-size:10px;color:#0f4c81;font-weight:700;margin-bottom:8px;border-bottom:1px dashed #90caf9;padding-bottom:4px;">Soft-Strap Delivery at Reset Exit:</div>
      <table style="border-collapse:separate;border-spacing:8px 0;margin:0 auto;">
        <tr>
          <td style="background:#e8f5e9;border:2px solid #388e3c;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#388e3c;font-size:11px;">BIOS</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">Configures<br>FlexRatio<br>value</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#388e3c;font-size:10px;">→</span></td>
          <td style="background:#f3e5f5;border:2px solid #7b1fa2;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#7b1fa2;font-size:11px;">PrimeCode (iMH)</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">HPM message<br>DISTRIBUTE_STRAPS_CBB<br>DATA_OFFSET=1</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#5e35b1;font-size:10px;">→soft-strap→</span></td>
          <td style="background:#ede7f6;border:2px solid #5e35b1;border-radius:6px;padding:10px 14px;min-width:140px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#5e35b1;font-size:11px;">PCode (CBB PUNIT)</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">Programs<br>CORE_STRAPS<br>register</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#e65100;font-size:10px;">→</span></td>
          <td style="background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#e65100;font-size:11px;">Microcode</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">Enforces<br>clipped P1<br>ratio</div>
          </td>
        </tr>
      </table>
    </div>
    <div style="background:#e3f2fd;border:1px solid #64b5f6;border-radius:5px;padding:8px 12px;font-size:11px;margin-bottom:8px;">
      <strong>Formula:</strong> <code>Effective P1 = min(fused_P1, FlexRatio)</code>
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Fuse:</strong> <code>FLEX_RATIO_DISABLE</code> — if set, Flex Ratio feature is disabled and fused_P1 is used directly.
    </div>
  </div>
</div>
<!-- /raw-html -->

### Flex Ratio — Algorithm Location

| Algorithm | Location | Scope | Function | HAS Reference |
|-----------|----------|-------|----------|---------------|
| **Flex Ratio Delivery** | **PrimeCode (iMH)** | Socket | Send FlexRatio via HPM DISTRIBUTE_STRAPS_CBB | DMR CBB HAS |
| **Flex Ratio Programming** | **PCode (CBB PUNIT)** | Module | Program CORE_STRAPS with FlexRatio | DMR CBB HAS |
| **P1 Enforcement** | **Microcode** | Core | Enforce Effective P1 = min(fused_P1, FlexRatio) | DMR CBB HAS |

### Key Registers

| Register / Interface | Address | Purpose |
|---------------------|---------|---------|
| **CPU Configuration Register (DW1)** | — | Contains Flex Ratio field (bits [8:1], 8 bits, RW) |
| **CORE_STRAPS** | — | PCode programs FlexRatio; consumed by microcode |
| **IA32_PERF_STATUS** | 0x198 | Read effective ratio (reflects FlexRatio clip) |
| **MSR_FLEX_RATIO** | 0x194 | Legacy MSR for Flex Ratio (if supported) |

### BIOS Knobs

| Knob | Purpose |
|------|---------|
| **FlexRatio** | BIOS-configured P1 ceiling (8-bit ratio value) |
| **FlexRatioOverrideEnable** | Enable/disable FlexRatio override |

### Fuses

| Fuse | Purpose |
|------|---------|
| **FLEX_RATIO_DISABLE** | If set, Flex Ratio feature is disabled; fused_P1 is used directly |

---

## Section 2: Interfaces and Protocols

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Configure FlexRatio value and enable override | BIOS Setup |
| 2 | BIOS | Write FlexRatio to CPU Configuration Register DW1 | Register Write |
| 3 | PrimeCode | At reset exit, send HPM DISTRIBUTE_STRAPS_CBB.DATA_OFFSET=1 | HPM Mailbox |
| 4 | PCode | Receive soft-strap; program CORE_STRAPS with FlexRatio | Internal |
| 5 | Microcode | Read CORE_STRAPS; compute Effective P1 = min(fused_P1, FlexRatio) | Internal |
| 6 | Core | Operate with clipped P1 as guaranteed frequency ceiling | PLLs |
| 7 | OS | Read IA32_PERF_STATUS for effective ratio | MSR 0x198 |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | BIOS | CPU Config DW1 | Write FlexRatio value | Register |
| 2 | PrimeCode | PCode | DISTRIBUTE_STRAPS_CBB (DATA_OFFSET=1) | HPM |
| 3 | PCode | CORE_STRAPS | Program FlexRatio | Internal |
| 4 | Microcode | Core | Enforce Effective P1 | Internal |

---

## Section 3: Reset / Power / Clocking

- Flex Ratio is configured at **reset exit** — not a runtime-dynamic feature
- On **warm reset**, Flex Ratio persists if BIOS configuration unchanged
- On **cold reset**, BIOS re-programs FlexRatio via CPU Configuration Register
- **SST profile switch** may interact with FlexRatio — see cross-product TC

---

## Section 4: Programming Model

```
// BIOS: Enable FlexRatio override
Set FlexRatioOverrideEnable = 1

// BIOS: Configure FlexRatio (e.g., 30 = 3.0 GHz at 100 MHz BCLK)
Write CPU_CONFIG_DW1.FlexRatio = 30  // 8-bit ratio

// Reset exit: PrimeCode sends soft-strap
HPM DISTRIBUTE_STRAPS_CBB.DATA_OFFSET=1: FlexRatio = 30

// PCode: Programs CORE_STRAPS
CORE_STRAPS.FlexRatio = 30

// Microcode: Enforces clipped P1
Effective_P1 = min(fused_P1, 30)

// OS: Read effective ratio
Read IA32_PERF_STATUS (0x198) → Current ratio (should not exceed FlexRatio)
```

---

## Section 5: Operational Behavior

- **P1 clipping:** Effective P1 = min(fused_P1, FlexRatio); cores cannot request higher than FlexRatio
- **Turbo unaffected:** Turbo ratios above P1 are still available if within power/thermal budget
- **SST interaction:** FlexRatio must interact correctly with SST profile switches (see cross-product TC)
- **SKU differentiation:** Lower FlexRatio can create lower-performance SKUs from same silicon

---

## Section 6: Corner Cases and Error Handling

| Corner Case | Expected Behavior |
|-------------|-------------------|
| FlexRatio > fused_P1 | Effective P1 = fused_P1 (min clips to fuse) |
| FlexRatio = 0 | Feature disabled; use fused_P1 directly |
| FLEX_RATIO_DISABLE fuse set | FlexRatio ignored; use fused_P1 |
| SST profile switch with FlexRatio | FlexRatio still enforced; SST P1 clipped by FlexRatio if needed |
| Warm reset | FlexRatio persists from prior boot (if BIOS unchanged) |

---

## Section 7: Security / Safety / Policy

- FlexRatio is set by BIOS at boot; cannot be changed at runtime by OS/malware
- FLEX_RATIO_DISABLE fuse provides OEM control to lock out FlexRatio feature
- Does not bypass other power/thermal limits (PL1, PL2, thermal throttling)

---

## Section 8: References

| Document | URL |
|----------|-----|
| DMR CBB P-State Stack HAS | https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html |
| PrimeCode HPM Interface | DISTRIBUTE_STRAPS_CBB — DATA_OFFSET=1 (FlexRatio soft-strap) |
| MSR Reference | IA32_PERF_STATUS (0x198), MSR_FLEX_RATIO (0x194) |

---

## TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422287 — Flex ratio configuration and functionality](https://hsdes.intel.com/appstore/article-one/#/22022422287) | Base FlexRatio | Verify Effective P1 = min(fused_P1, FlexRatio) across ratio sweep |
| [22022422292 — Flex ratio configuration and functionality X SST](https://hsdes.intel.com/appstore/article-one/#/22022422292) | SST cross-product | Verify FlexRatio interacts correctly with SST profile switches |

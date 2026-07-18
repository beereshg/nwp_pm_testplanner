# TCD 22022420976 -- ICCP: License request and grant flow

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420976](https://hsdes.intel.com/appstore/article-one/#/22022420976) |
| **Title** | ICCP: License request and grant flow |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [22022420466 -- Pstate-Core ICCP](https://hsdes.intel.com/appstore/article-one/#/22022420466) |
| **Child TCs** | 6 TCs (AVX License PreGrant, AMX/AVX-256/AVX-512/AVX-128 license flows, Min_ICCP_Level) |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**ICCP (IccMax Current Control Protocol)** manages per-core current contribution based on the instruction set being executed. Cores declare their license level and PCode applies the appropriate TRL row and IccMax current budget.

> **HAS Reference:** [DMR CBB P-State Stack HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html) - ICCP license level hierarchy, FACT table, TRL interaction.

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.3px;">ICCP - License Request and Grant Flow (PCode)</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <div style="margin-bottom:16px;">
      <div style="font-size:10px;color:#0f4c81;font-weight:700;margin-bottom:8px;border-bottom:1px dashed #90caf9;padding-bottom:4px;">License Request/Grant Flow:</div>
      <table style="border-collapse:separate;border-spacing:8px 0;margin:0 auto;">
        <tr>
          <td style="background:#f3e5f5;border:2px solid #7b1fa2;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#7b1fa2;font-size:11px;">Core</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">Executes AVX/AMX<br>instruction<br>HW auto-request</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#7b1fa2;font-size:10px;">req</span></td>
          <td style="background:#ede7f6;border:2px solid #5e35b1;border-radius:6px;padding:10px 14px;min-width:160px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#5e35b1;font-size:11px;">PCode ICCP</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;"><b>CBB PUNIT</b><br>Evaluate platform limits<br>Grant license level</div>
            <div style="margin-top:8px;padding-top:8px;border-top:1px dashed #5e35b1;">
              <div style="font-weight:700;color:#e65100;font-size:10px;">License Hierarchy</div>
              <div style="font-size:9px;color:#555;">SSE &lt; AVX-256 &lt; AVX-512 &lt; AMX</div>
            </div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#2e7d32;font-size:10px;">grant</span></td>
          <td style="background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#e65100;font-size:11px;">FACT/TRL</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;"><b>Select TRL row</b><br>FACT[license][N_cores]<br>IccMax budget</div>
          </td>
          <td style="text-align:center;vertical-align:middle;padding:0 4px;"><span style="color:#555;">-></span></td>
          <td style="background:#e0f2f1;border:2px solid #00796b;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;vertical-align:top;">
            <div style="font-weight:700;color:#00796b;font-size:11px;">Core Freq</div>
            <div style="font-size:10px;color:#555;line-height:1.5;margin-top:4px;">License-level<br>TRL ceiling<br>applied</div>
          </td>
        </tr>
      </table>
    </div>
    <div style="background:#e3f2fd;border:1px solid #64b5f6;border-radius:5px;padding:8px 12px;font-size:11px;margin-bottom:8px;">
      <strong>Key:</strong> Higher license = higher power draw = lower TRL ceiling. Core throttles to license-granted level.
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>PLR:</strong> <code>CORE_PERF_LIMIT_REASONS (0x64F)</code> AVX bit set when license is limiting reason.
    </div>
  </div>
</div>
<!-- /raw-html -->

### ICCP License Levels

| Level | Instruction Set | Current Budget | TRL Impact |
|-------|-----------------|----------------|------------|
| **SSE** | Scalar/SSE | Lowest Cdyn | Highest TRL ceiling |
| **AVX-256** | AVX2 | Medium Cdyn | Lower TRL ceiling |
| **AVX-512** | AVX-512 | High Cdyn | Lower TRL ceiling |
| **AMX** | AMX | Highest Cdyn | Lowest TRL ceiling |

### PCode ICCP - Algorithm Location

| Algorithm | Location | Scope | Function | HAS Reference |
|-----------|----------|-------|----------|---------------|
| **ICCP License Grant** | **PCode (CBB PUNIT)** | Per-core | Evaluate platform limits, grant license level | DMR CBB P-State Stack HAS |
| **FACT Table Lookup** | **PCode (CBB PUNIT)** | Module | Select TRL row based on license + N_active_cores | DMR CBB HAS |
| **IccMax Enforcement** | **PCode (CBB PUNIT)** | Socket | Apply current budget per license level | DMR CBB HAS |

### Key Registers

| Register / Interface | Address | Purpose |
|---------------------|---------|---------|
| **IA32_PERF_STATUS** | 0x198 | Effective ratio after ICCP TRL clip |
| **CORE_PERF_LIMIT_REASONS (PLR)** | 0x64F | AVX/license throttle bit indicates ICCP limiting |
| **CORE_LICENSE_REQ** | - | Core writes license request |
| **XPMA_CR_ICCP_LICENSE_CONTROL** | - | PCode writes granted license |

### BIOS Knobs

| Knob | Purpose |
|------|---------|
| **AvxLicensePreGrant** | Pre-grant license level at boot (0=SSE, 1=AVX-256, 2=AVX-512, 3=AMX) |
| **AvxIccpLevel** | Cdyn bucket selection for license levels |

### B2P Mailbox - Min_ICCP_Level

| Command | SubCommand | Field | Purpose |
|---------|------------|-------|---------|
| **WRITE_PM_CONFIG** | 0x95 | Min_ICCP_Level (0x0-0xF) | Sets minimum license floor; PCode will not grant below this level |

---

## Section 2: Interfaces and Protocols

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Configure AvxLicensePreGrant, AvxIccpLevel knobs | BIOS Setup |
| 2 | BIOS | Optionally set Min_ICCP_Level via B2P WRITE_PM_CONFIG | B2P Mailbox |
| 3 | OS/App | Execute AVX/AMX instruction | Instruction |
| 4 | Core HW | Auto-request license level (HW-triggered) | CORE_LICENSE_REQ |
| 5 | PCode ICCP | Evaluate platform limits (IccMax, VR, thermal) | Internal |
| 6 | PCode ICCP | Grant license (may be lower than requested) | XPMA_CR_ICCP_LICENSE_CONTROL |
| 7 | Core HW | Acknowledge grant; throttle if needed | Internal |
| 8 | PCode | Select TRL row = FACT[license_level][N_active_cores] | FACT Table |
| 9 | PCode | Apply IccMax current budget for granted license | Internal |
| 10 | Core | Operate at license-level TRL ceiling | PLLs |
| 11 | OS | Read IA32_PERF_STATUS for effective ratio | MSR 0x198 |
| 12 | OS | Read PLR for license-limiting indication | MSR 0x64F |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | Core | PCode | License request (SSE/AVX-256/AVX-512/AMX) | CORE_LICENSE_REQ |
| 2 | PCode | Core | License grant (may be <= request) | XPMA_CR_ICCP_LICENSE_CONTROL |
| 3 | Core | PCode | Acknowledge | Internal |
| 4 | PCode | FACT | TRL lookup for granted license | Internal |
| 5 | PCode | Core | Frequency grant at TRL ceiling | Internal |

---

## Section 3: Reset / Power / Clocking

- On **C6 exit**, ICCP handshake repeats; core re-requests license
- On **workload termination**, license is revoked and TRL restored to higher ceiling
- **AvxLicensePreGrant** sets initial license at boot (before first AVX instruction)

---

## Section 4: Programming Model

``
// BIOS: Set pre-grant level
Set AvxLicensePreGrant = 2  // Pre-grant AVX-512

// BIOS: Set Cdyn bucket
Set AvxIccpLevel = <bucket>

// BIOS: Set min license floor via B2P
B2P WRITE_PM_CONFIG (0x95, subcmd=0x2): Min_ICCP_Level = 0x1  // Min AVX-256

// Runtime: Core auto-requests on AVX/AMX instruction
// PCode grants license, selects TRL row
// Core operates at license-level ceiling

// OS: Check if ICCP is limiting
Read PLR (0x64F) -> Check AVX/license bit
Read IA32_PERF_STATUS (0x198) -> Effective ratio
``

---

## Section 5: Operational Behavior

- **License escalation:** When core executes higher instruction set, HW auto-requests higher license
- **License de-escalation:** When AVX/AMX workload terminates, license revoked, TRL restored
- **Partial grant:** If platform limits prevent full license, PCode grants lower level; core throttles
- **PLR indication:** CORE_PERF_LIMIT_REASONS (0x64F) AVX bit asserts when frequency clipped by license

---

## Section 6: Corner Cases and Error Handling

| Corner Case | Expected Behavior |
|-------------|-------------------|
| Request > platform limit | PCode grants lower license; core throttles |
| Min_ICCP_Level > request | PCode grants Min_ICCP_Level floor |
| C6 exit during AVX workload | ICCP handshake re-executes |
| All cores requesting AMX | TRL ceiling reduced across all cores |
| License revoke during execution | TRL restored; frequency may increase |

---

## Section 7: Security / Safety / Policy

- ICCP enforces IccMax limits to prevent VR overcurrent
- BIOS can lock Min_ICCP_Level to prevent runtime changes
- Malicious workload cannot exceed granted license

---

## Section 8: References

| Document | URL |
|----------|-----|
| DMR CBB P-State Stack HAS | https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html |
| B2P Mailbox Spec | WRITE_PM_CONFIG - Min_ICCP_Level field |
| Core P-state HAS | ICCP - license level hierarchy, FACT table, TRL interaction |

---

## TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422259 - AVX License PreGrant and Level BIOS Knob checks](https://hsdes.intel.com/appstore/article-one/#/22022422259) | BIOS knobs | Verify AvxLicensePreGrant and AvxIccpLevel initialize PCode state |
| [22022422262 - ICCP: AMX License request and grant flow](https://hsdes.intel.com/appstore/article-one/#/22022422262) | AMX license | Verify AMX triggers correct TRL/FACT row |
| [22022422266 - ICCP: AVX 256 License request and grant flow](https://hsdes.intel.com/appstore/article-one/#/22022422266) | AVX-256 license | Verify AVX-256 triggers correct TRL/FACT row |
| [22022422267 - ICCP: AVX 512 License request and grant flow](https://hsdes.intel.com/appstore/article-one/#/22022422267) | AVX-512 license | Verify AVX-512 triggers correct TRL/FACT row |
| [16031014909 - ICCP: AVX 128 License request and grant flow](https://hsdes.intel.com/appstore/article-one/#/16031014909) | AVX-128 license | Verify AVX-128/SSE triggers correct TRL/FACT row |
| [22022422270 - ICCP: Min_ICCP_Level B2P MB Functionality](https://hsdes.intel.com/appstore/article-one/#/22022422270) | B2P mailbox | Verify Min_ICCP_Level floor across 0x0-0xF sweep |

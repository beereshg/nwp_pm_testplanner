# TPF 16030767553 — [NWP PM] TPMI (Topology-aware PM Interface)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030767553](https://hsdes.intel.com/appstore/article-one/#/16030767553) |
| **Title** | [NWP PM] TPMI (Topology-aware PM Interface) |
| **Parent TP** | [16030765561 — [NWP PM] PM Interfaces (OS2P/TPMI/PECI/PMT)](https://hsdes.intel.com/appstore/article-one/#/16030765561) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-20 |

---

## Section 1: Feature Classification & Introduction

**TPMI (Topology-aware Platform Management Interface)** is a flexible, extendable, and software-enumerable MMIO interface for platform management features on NWP. TPMI replaces legacy MSR/mailbox interfaces with a unified, hierarchical, and PCIe/ACPI-discoverable register model for PM feature access.

**Classification**: Hardware-heavy interface with firmware initialization. OOBMSM hardware hosts TPMI control, VSEC, PFS tables, and security rules. PrimeCode firmware initializes TPMI SRAM contents at boot. Software discovers and accesses features via standard PCIe enumeration.

**Gating mechanism**: TPMI is **always present** on NWP when OOBMSM is functional. Individual TPMI features are gated by their own fuses/knobs. The TPMI infrastructure itself has no independent disable.

**NWP scope**: NWP aligns with GNR baseline for TPMI (SRAM sticky across warm reset, unlike DMR gap). Up to 256 features (8-bit TPMI_ID). NWP-specific TPMI features include SST-CP, SST-TF, RAPL, UFS, PEM, PLR.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| TPMI BAR | 64-bit PCIe BAR (tBIR=0x2) | TPMI HAS |
| Register width | 64 bits | TPMI HAS |
| Feature alignment | 4 KB per feature | TPMI HAS |
| Max features | 256 (8-bit TPMI_ID) | TPMI HAS |
| PFS location | VSEC → PFS table → feature offsets | TPMI HAS |
| SRAM reset behavior | Sticky across warm reset (NWP = GNR baseline) | NWP PM MAS |
| Cold reset | HW MBIST zeros SRAM; PCode re-initializes | TPMI HAS |
| OOBMSM host | Primary-to-sideband converter | NWP architecture |
| Access attributes | RW, RO, RW-L (uniform per register) | TPMI HAS |
| Header register | Offset 0 per feature: INTERFACE_VERSION + validity | TPMI HAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / ACPI / Tool</strong><br/>
    <small>Linux intel_tpmi driver · ACPI DSDT · PythonSV · intel-speed-select</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: PCIe Enumeration / VSEC Discovery</strong><br/>
    <small>PCIe config space VSEC capability · BAR mapping · PFS table enumeration</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PrimeCode TPMI Initialization</strong><br/>
    <small>SRAM content init at boot · feature register programming · security policy setup</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: OOBMSM TPMI Controller HW</strong><br/>
    <small>Primary-to-sideband bridge · LTM SRAM · access control · MMIO decode</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: TPMI SRAM / Register Storage</strong><br/>
    <small>4KB-aligned feature blocks · sticky across warm reset · MBIST cold-reset zeroing</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L5: OS / ACPI / Tool | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted Linux + intel_tpmi driver |
| L4: PCIe Enumeration / VSEC | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | FV: real PCIe enum; HSLE: limited model |
| L3: PrimeCode TPMI Init | ✅ | ✅ | ✅ | ✅ | indirect | All pre-si tiers validate FW init |
| L2: OOBMSM TPMI Controller HW | ❌ | ✅ | ✅ | ✅ | indirect | HSLE has RTL; VP model limited |
| L1: TPMI SRAM / Register Storage | ⚠️ | ✅ | ✅ | ✅ | indirect | VP: functional model; HSLE: RTL fidelity |

### TPMI Discovery and Access Flow

`
OS / Tool
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 1. PCIe enumeration finds OOBMSM device                 │
│ 2. Read VSEC capability in PCIe config space            │
│ 3. VSEC points to TPMI MMIO BAR base address            │
│ 4. Read PFS (Platform Feature Structure) table          │
│    - Each entry: TPMI_ID, offset, size, access_attr     │
│ 5. Access feature registers at BAR + feature_offset     │
│ 6. First register (offset 0) = HEADER:                  │
│    INTERFACE_VERSION[15:0], VALID[16]                    │
└─────────────────────────────────────────────────────────┘
`

### NWP TPMI Feature IDs (PM-relevant)

| TPMI_ID | Feature | Description |
|---|---|---|
| 0x01 | RAPL | Running Average Power Limit |
| 0x02 | PBF | Priority Base Frequency |
| 0x03 | SST-CP | Speed Select Core Power |
| 0x04 | SST-TF | Speed Select Turbo Frequency |
| 0x05 | UFS | Uncore Frequency Scaling |
| 0x0A | PEM | Power and Energy Monitoring |
| 0x0B | PLR | Performance Limit Reasons |
| 0x0C | DLCP | Die-Level Cherry Picking |

### Interface & Register Matrix

| Register / MSR | Path | Description | Tier Validated |
|---|---|---|---|
| TPMI VSEC | PCIe config space | Points to TPMI BAR | FV, PV |
| PFS table | BAR + 0x0 | Feature enumeration table | FV, PSS (HSLE) |
| Feature HEADER | BAR + feature_offset + 0x0 | Interface version + validity | FV, PSS |
| Feature registers | BAR + feature_offset + N×8 | Per-feature register block | FV, PSS |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| TPMI BAR address | PCIe config | `lspci -vvv` / PythonSV PCIe enum | Whether TPMI BAR is mapped |
| PFS feature count | MMIO read | `sv.socket0.nio.oobmsm.tpmi.pfs.*` | Enumerated feature count |
| Feature HEADER validity | MMIO read | Read offset 0 of each feature | Whether FW initialized the feature |
| SRAM content after warm reset | MMIO read | Compare pre/post warm reset | Sticky behavior verification |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| Feature fused off | PFS entry present but HEADER.VALID=0 | TPMI feature enumeration TCD |
| OOBMSM disabled | Entire TPMI unavailable | All |
| Security policy locked | RW-L registers become RO after lock | TPMI access control TCD |

---

## Section 3: Validation Strategy

TPMI validation requires multiple tiers because the feature spans PCIe discovery hardware, OOBMSM controller logic, firmware initialization, and OS driver enumeration.

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | FW initialization logic, feature register content |
| PSS — HSLE | Single-die RTL | PythonSV → TPMI RTL | OOBMSM HW decode, SRAM behavior, access control |
| PSS — XOS | Both-die RTL (IMH+CBB) | PythonSV → full RTL | Cross-die TPMI (if applicable) |
| FV | Post-silicon NWP | PythonSV → namednodes | Real PCIe enumeration + VSEC + PFS + register access |
| PV | Post-silicon NWP + Ubuntu | `intel_tpmi` driver | OS driver enumeration and sysfs exposure |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| FW fails to initialize SRAM | ✅ | ✅ | ✅ | ✅ | indirect |
| SRAM not sticky across warm reset | ❌ | ✅ | ✅ | ✅ | ✅ |
| PFS entry offset wrong | ❌ | ✅ | ✅ | ✅ | ✅ |
| VSEC capability missing | ❌ | ⚠️ | ⚠️ | ✅ | ✅ |
| Access control not enforced (RW-L bypass) | ❌ | ✅ | ✅ | ✅ | ❌ |
| Feature register returns wrong value | ✅ | ✅ | ✅ | ✅ | indirect |
| OS driver enumeration failure | ❌ | ❌ | ❌ | ❌ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| PFS enumeration → all features found | ⚠️ | ✅ | ✅ | FV: real PCIe; PV: OS driver |
| SRAM warm-reset stickiness | HSLE | ✅ | ✅ | Silicon verification |
| Feature HEADER.VALID = 0 (fused off) | ✅ | ✅ | ✅ | Negative test |
| RW-L register lock after boot | HSLE | ✅ | ❌ | Security enforcement |
| Cold reset → SRAM zeroed, FW re-inits | ✅ | ✅ | ✅ | Reset sequence |

---

## Section 5: Risks & Dependencies

### Active Risks

- **OOBMSM model gap**: VP (Simics) has limited OOBMSM model fidelity — PFS enumeration and VSEC discovery may not work in VP.
- **SRAM warm-reset stickiness**: NWP claims GNR-baseline stickiness; must verify no DMR-style gap exists.
- **Security policy enforcement**: RW-L lock timing depends on BIOS CPL3 handshake; any timing issue leaves registers unlocked.

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | OS intel_tpmi driver enumeration | PV only | Requires booted Linux + PCIe stack |
| **G-2** | VSEC PCIe config space discovery | FV + PV only | VP model does not implement PCIe config space |

---

## Section 6: DFX Considerations

- **TPMI register dump**: PythonSV can dump all TPMI feature registers via `sv.socket0.nio.oobmsm.tpmi.*`
- **PFS table inspection**: Read PFS table entries to verify feature enumeration matches expected topology
- **VISA capture**: OOBMSM TPMI SRAM access can be observed via ITH T2 VISA on OOBMSM domain
- **Error injection**: Force PFS entry corruption in HSLE to test OS driver robustness

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| Feature fused off but PFS entry present | (no TCD yet) | HEADER.VALID=0; OS driver skips feature |
| SRAM corruption after unexpected warm reset | (no TCD yet) | PCode re-initializes on next boot |
| Concurrent TPMI access from OS + FW | (no TCD yet) | HW serializes; no data corruption |
| BAR not mapped by BIOS | (no TCD yet) | All MMIO reads return 0xFFFFFFFF; driver reports error |
| TPMI register write during RW-L lock | (no TCD yet) | Write silently ignored; no error |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| *(none — TCDs not yet created)* | | | |

### References

- [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/TPMI/TPMI.html) — TPMI architecture, PFS, VSEC, register model
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP TPMI feature IDs and topology
- [OOBMSM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/OOBMSM/OOBMSM.html) — OOBMSM as TPMI host

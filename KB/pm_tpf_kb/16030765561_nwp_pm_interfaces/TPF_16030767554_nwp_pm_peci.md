# TPF 16030767554 — [NWP PM] PECI (Platform Environment Control Interface)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030767554](https://hsdes.intel.com/appstore/article-one/#/16030767554) |
| **Title** | [NWP PM] PECI (Platform Environment Control Interface) |
| **Parent TP** | [16030765561 — [NWP PM] PM Interfaces (OS2P/TPMI/PECI/PMT)](https://hsdes.intel.com/appstore/article-one/#/16030765561) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-20 |

---

## Section 1: Feature Classification & Introduction

**PECI (Platform Environment Control Interface)** is the out-of-band management interface for BMC-to-CPU communication on NWP. On NWP, the legacy serial PECI wire is deprecated; PECI protocol is now carried over MCTP (Management Component Transport Protocol) using PCIe or I3C transport via the OOBMSM IP.

**Classification**: Hardware-heavy with firmware command servicing. OOBMSM hardware handles PECI-over-MCTP transport. PrimeCode firmware services PECI power management commands (RdPkgConfig, WrPkgConfig, GetTemp). Silicon provides temperature sensors and package configuration space.

**Gating mechanism**: PECI-over-MCTP is **always available** when OOBMSM is functional and the BMC transport (PCIe VDM or I3C) is active. Legacy serial PECI wire is deprecated on NWP.

**NWP scope**: NWP carries over DMR's PECI-over-MCTP architecture. GetTemp is supported but deprecated (PMT/PLDM preferred). RdPkgConfig/WrPkgConfig provide access to Package Configuration Space (PCS) for power/thermal management. RdIAMSR/RdIAMSREx provide MSR access over PECI.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Transport | PECI-over-MCTP (PCIe VDM or I3C) | NWP PM MAS |
| Legacy PECI wire | Deprecated | NWP architecture |
| OOBMSM host | Routes PECI commands to PrimeCode | OOBMSM HAS |
| GetTemp | Supported (deprecated; use PMT) | PECI HAS |
| RdPkgConfig/WrPkgConfig | Supported | PECI HAS |
| RdIAMSR/RdIAMSREx | Supported | PECI HAS |
| Max response time | Implementation-defined; BMC timeout applies | PECI HAS |
| Package Configuration Space (PCS) | Index/Parameter encoding for PM registers | PECI HAS |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: BMC / Management Controller</strong><br/>
    <small>OpenBMC · IPMI · Redfish · Node Manager · PECI client library</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: MCTP Transport (PCIe VDM / I3C)</strong><br/>
    <small>MCTP packet encapsulation · routing · endpoint discovery</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: OOBMSM PECI Protocol Engine</strong><br/>
    <small>PECI command decode · request routing to PrimeCode · response packaging</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: PrimeCode PECI Command Handler</strong><br/>
    <small>GetTemp servicing · RdPkgConfig/WrPkgConfig dispatch · PCS access · error response</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon Sensors / PCS HW</strong><br/>
    <small>DTS temperature sensors · Package Configuration Space registers · fuse state</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L5: BMC / Management Controller | ❌ | ❌ | ❌ | ❌ | ✅ | Requires real BMC + MCTP transport |
| L4: MCTP Transport (PCIe VDM / I3C) | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | FV: real transport; HSLE: limited model |
| L3: OOBMSM PECI Protocol Engine | ❌ | ✅ | ✅ | ✅ | indirect | HSLE has RTL; VP no OOBMSM model |
| L2: PrimeCode PECI Command Handler | ✅ | ✅ | ✅ | ✅ | indirect | All tiers validate FW logic |
| L1: Silicon Sensors / PCS HW | ❌ | ✅ | ✅ | ✅ | indirect | Real sensors on silicon only |

### PECI-over-MCTP Transaction Flow

`
BMC (OpenBMC / Node Manager)
       │
       ▼ MCTP message (PCIe VDM or I3C)
┌─────────────────────────────────────────────────────────┐
│ OOBMSM — PECI Protocol Engine                           │
│ 1. Receive MCTP packet from BMC                         │
│ 2. Decode PECI command (GetTemp / RdPkgConfig / etc.)   │
│ 3. Route to PrimeCode via sideband mailbox              │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ PrimeCode PECI Handler                                  │
│ - GetTemp: read max DTS, return temperature delta       │
│ - RdPkgConfig[idx,param]: read PCS entry → response     │
│ - WrPkgConfig[idx,param,data]: write PCS entry          │
│ - RdIAMSR: read specified MSR → response                │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ Response → OOBMSM → MCTP → BMC                         │
│ Completion code: 0x40 (success) or error                │
└─────────────────────────────────────────────────────────┘
`

### Key PECI PM Commands

| Command | Index/Param | Description |
|---|---|---|
| GetTemp | — | Returns max DTS temperature delta below Tjmax |
| RdPkgConfig | Index=0, Param=0 | Read PCS entry (thermal status, power info) |
| WrPkgConfig | Index=N, Param=N, Data | Write PCS entry (power limit, config) |
| RdIAMSR / RdIAMSREx | MSR address | Read IA MSR via PECI path |

### Interface & Register Matrix

| Register / MSR | Path | Description | Tier Validated |
|---|---|---|---|
| OOBMSM PECI mailbox | `sv.socket0.nio.oobmsm.peci.*` | PECI command/response registers | FV, PSS (HSLE) |
| Package Configuration Space | PCS index/param encoding | PM register access via PECI | FV, PSS |
| DTS temperature | `sv.socket0.cbb{0,1}.compute*.module*.dts_*` | Die temperature sensors | FV |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| PECI command trace | FW trace | `fw_trace_parser` | PECI command receive/dispatch/response events |
| OOBMSM PECI status | MMIO register | `sv.socket0.nio.oobmsm.peci.status.show()` | Transport status, errors |
| BMC PECI response | BMC tool | `peci_cmds` on BMC | End-to-end response verification |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| I3C transport only (no PCIe VDM) | Limited to I3C MCTP path | All PECI TCDs |
| GetTemp deprecated | Returns valid data but PMT preferred | GetTemp TCD |
| PCS entries gated by fuse/BIOS | Some RdPkgConfig indices return 0 | RdPkgConfig TCD |

---

## Section 3: Validation Strategy

PECI validation requires multiple tiers because the feature spans BMC management software, MCTP transport hardware, OOBMSM protocol engine, firmware command handling, and silicon sensors.

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → PECI model | FW command handler logic (limited) |
| PSS — HSLE | Single-die RTL | PythonSV → OOBMSM RTL | OOBMSM protocol engine, PCS access |
| PSS — XOS | Both-die RTL (IMH+CBB) | PythonSV → full RTL | Cross-die PCS data (DTS from CBB) |
| FV | Post-silicon NWP | PythonSV + BMC | Real MCTP transport + FW + sensors |
| PV | Post-silicon NWP + BMC | BMC tools (peci_cmds) | End-to-end BMC → CPU → response |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| FW command handler returns wrong data | ✅ | ✅ | ✅ | ✅ | indirect |
| OOBMSM PECI decode error | ❌ | ✅ | ✅ | ✅ | indirect |
| MCTP transport drops packet | ❌ | ⚠️ | ⚠️ | ✅ | ✅ |
| GetTemp returns wrong temperature | ❌ | ❌ | ❌ | ✅ | ✅ |
| WrPkgConfig fails to update PCS | ✅ | ✅ | ✅ | ✅ | ✅ |
| BMC timeout on PECI response | ❌ | ❌ | ❌ | ✅ | ✅ |
| RdIAMSR returns stale MSR value | ❌ | ✅ | ✅ | ✅ | indirect |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| GetTemp → valid temperature | ❌ | ✅ | ✅ | Real DTS sensor |
| RdPkgConfig power limits | ✅ | ✅ | ✅ | FW logic + silicon |
| WrPkgConfig → verify written | ✅ | ✅ | ✅ | Write + readback |
| Invalid PECI command → error response | ✅ | ✅ | ✅ | Negative test |
| MCTP transport stress (many commands) | ❌ | ❌ | ✅ | Real transport |

---

## Section 5: Risks & Dependencies

### Active Risks

- **MCTP transport reliability**: PECI-over-MCTP depends on PCIe VDM or I3C link stability; transport errors mask PECI failures.
- **GetTemp deprecation**: GetTemp still works but PMT is preferred; risk of OS/BMC tools relying on deprecated path.
- **OOBMSM model fidelity**: VP (Simics) has no OOBMSM PECI model — pre-si PECI testing is limited to HSLE.
- **Cross-die temperature**: GetTemp returns max DTS across all dies; requires XOS environment to validate aggregation.

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | BMC end-to-end PECI response | FV + PV only | Requires real BMC + MCTP hardware |
| **G-2** | Real DTS temperature accuracy | FV + PV only | VP/HSLE have no real thermal sensors |
| **G-3** | MCTP transport stress testing | FV + PV only | Requires real PCIe VDM / I3C link |

---

## Section 6: DFX Considerations

- **PECI trace**: PrimeCode firmware trace logs all PECI command receive/dispatch/response events.
- **OOBMSM debug registers**: OOBMSM has PECI status and error registers for transport-layer debug.
- **VISA capture**: PECI transaction on OOBMSM sideband can be observed via ITH T2 VISA.
- **BMC-side logging**: BMC peci_cmds tool provides response timing and error statistics.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| PECI command during CPU reset | (no TCD yet) | OOBMSM returns error; no hang |
| Concurrent PECI from multiple BMC clients | (no TCD yet) | Serialized by OOBMSM; no data corruption |
| RdPkgConfig to fused-off feature | (no TCD yet) | Returns 0 or error code; no hang |
| WrPkgConfig to locked PCS entry | (no TCD yet) | Write silently ignored or returns error |
| GetTemp during thermal event | (no TCD yet) | Returns real-time max DTS |
| MCTP packet corruption | (no TCD yet) | CRC check fails; OOBMSM drops; BMC retries |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| *(none — TCDs not yet created)* | | | |

### References

- [PECI HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PECI/PECI.html) — PECI command set, PCS encoding, transport
- [OOBMSM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/OOBMSM/OOBMSM.html) — OOBMSM PECI protocol engine
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PECI-over-MCTP scope
- [MCTP Architecture](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/MCTP/MCTP.html) — MCTP transport for PECI

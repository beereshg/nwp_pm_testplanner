# TPF 16030767552 — [NWP PM] OS2P Mailbox

| Field | Value |
|-------|-------|
| **TPF ID** | [16030767552](https://hsdes.intel.com/appstore/article-one/#/16030767552) |
| **Title** | [NWP PM] OS2P Mailbox |
| **Parent TP** | [16030765561 — [NWP PM] PM Interfaces (OS2P/TPMI/PECI/PMT)](https://hsdes.intel.com/appstore/article-one/#/16030765561) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-20 |

---

## Section 1: Feature Classification & Introduction

**OS2P (OS-to-Punit) Mailbox** is the primary in-band communication mechanism for the OS and BIOS to interact with PrimeCode (Punit) firmware on NWP. It provides a synchronous request-response interface for platform management operations including power limit configuration, turbo control, SST provisioning, and telemetry queries.

**Classification**: Firmware-heavy interface feature. PrimeCode firmware services all OS2P commands; hardware provides the register interface (MSR or TPMI MMIO) and the RUN_BUSY handshake mechanism.

**Gating mechanism**: OS2P is **always available** when the CPU is powered. No fuse or BIOS knob gates the mailbox interface itself; individual commands may be gated by feature fuses or BIOS policy.

**NWP scope**: NWP inherits the OS2P architecture from DMR with TPMI-based MMIO access as the preferred path. Legacy MSR access (0xB0/0xB1) is supported for backward compatibility. NWP adds no new OS2P commands beyond DMR; the command set is identical.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Interface register (MSR) | MSR 0xB0 (OS_MAILBOX_INTERFACE), MSR 0xB1 (OS_MAILBOX_DATA) | DMR PM HAS |
| TPMI MMIO path | `sv.socket0.nio.punit.tpmi.os_mailbox_interface` | NWP PM MAS |
| RUN_BUSY bit | Bit 31 of OS_MAILBOX_INTERFACE | DMR PM HAS |
| COMMAND field | Bits [7:0] | DMR PM HAS |
| ADDR field | Bits [28:8] | DMR PM HAS |
| Timeout | 5 ms (if RUN_BUSY does not clear) | DMR PM HAS |
| Package scope | Single-package; one mailbox per socket | NWP topology |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:700px">
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: OS / BIOS / Tool</strong><br/>
    <small>OS driver (intel_pstate, intel-speed-select) · BIOS UEFI · turbostat · PythonSV</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: MSR / TPMI Register Interface</strong><br/>
    <small>MSR 0xB0/0xB1 legacy path · TPMI MMIO OS_MAILBOX_INTERFACE/DATA · RUN_BUSY handshake HW</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: PrimeCode Mailbox Handler</strong><br/>
    <small>Command dispatch · parameter validation · response generation · error codes</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Punit HW / TPMI SRAM</strong><br/>
    <small>Register storage · RUN_BUSY logic · interrupt/polling notification</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| L4: OS / BIOS / Tool | $! safe | $! | $! | $! | ✅ | PV requires booted OS + tool stack; VP safe for BIOS negative |
| L3: MSR / TPMI Register Interface | ✅ | ✅ | ✅ | ✅ | ✅ | All tiers can exercise register reads/writes |
| L2: PrimeCode Mailbox Handler | ✅ | ✅ | ✅ | ✅ | indirect | FW logic validated at all pre-si tiers |
| L1: Punit HW / TPMI SRAM | $! | ✅ | ✅ | ✅ | indirect | VP model limited; HSLE has RTL |

### OS2P Transaction Flow

`
OS / BIOS / Tool
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Poll RUN_BUSY (bit 31) in OS_MAILBOX_INTERFACE = 0   │
│ 2. Write OS_MAILBOX_DATA (input data if required)       │
│ 3. Write OS_MAILBOX_INTERFACE:                          │
│    COMMAND[7:0] = opcode, ADDR[28:8] = sub-cmd,         │
│    RUN_BUSY[31] = 1                                     │
│ 4. Poll RUN_BUSY until 0 (timeout = 5 ms)              │
│ 5. Read COMMAND[7:0] for success/error code             │
│ 6. Read OS_MAILBOX_DATA for output                      │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ PrimeCode Mailbox Handler (NIO Punit)                   │
│ - Decode COMMAND + ADDR                                 │
│ - Validate parameters (bounds, fuse gates)              │
│ - Execute action (read/write internal state)            │
│ - Write response to OS_MAILBOX_DATA                     │
│ - Clear RUN_BUSY → transaction complete                 │
└─────────────────────────────────────────────────────────┘
`

### Key OS2P Command Categories (PM-relevant)

| Command Category | Example Opcodes | Description |
|---|---|---|
| Power Limits | READ_RAPL_LIMIT, WRITE_RAPL_LIMIT | Read/write PL1, PL2, PL4 limits |
| Turbo | READ_TURBO_RATIO_LIMIT | Read resolved turbo ratio limits |
| SST | SST_PP_GET_PROFILES, SST_PP_SET_CONFIG | Speed Select Technology provisioning |
| Thermal | READ_TEMPERATURE_TARGET | Read Tjmax and thermal offset |
| Misc | READ_OC_PARAMS, READ_PCODE_VERSION | Overclocking, firmware version |

### Interface & Register Matrix

| Register / MSR | Path | Description | Tier Validated |
|---|---|---|---|
| OS_MAILBOX_INTERFACE | MSR 0xB0 / `sv.socket0.nio.punit.tpmi.os_mailbox_interface` | Command + RUN_BUSY + ADDR | FV, PSS |
| OS_MAILBOX_DATA | MSR 0xB1 / `sv.socket0.nio.punit.tpmi.os_mailbox_data` | Input/output data | FV, PSS |
| OS_MAILBOX_INTERFACE (TPMI) | `sv.socket0.nio.punit.tpmi.os_mailbox.*` | TPMI MMIO variant | FV, PSS |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| RUN_BUSY state | TPMI register | `sv.socket0.nio.punit.tpmi.os_mailbox_interface.show()` | Whether a transaction is in-flight |
| Command response code | TPMI register | Read COMMAND field after RUN_BUSY=0 | Success (0x0) or error code |
| PrimeCode trace | FW trace | `fw_trace_parser` | OS2P command receive/dispatch/response events |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| SST fused off | SST-related OS2P commands return error | OS2P Mailbox Validation |
| Overclocking locked | OC-related commands rejected | OS2P Mailbox Validation |
| TPMI disabled (fallback to MSR) | MMIO path unavailable; MSR path only | OS2P Mailbox Validation |

---

## Section 3: Validation Strategy

OS2P Mailbox validation requires multiple tiers because the feature spans firmware command handling (PrimeCode logic), register interface HW (TPMI SRAM, MSR), and OS/tool integration (intel_pstate, intel-speed-select).

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | Firmware command dispatch, parameter validation, error codes, negative testing |
| PSS — HSLE | Single-die RTL | PythonSV → TPMI RTL | Register interface HW behavior, RUN_BUSY timing |
| PSS — XOS | Both-die RTL (IMH+CBB) | PythonSV → full RTL | Cross-die mailbox forwarding (if any) |
| FV | Post-silicon NWP | PythonSV → namednodes | Real silicon register interface + firmware logic |
| PV | Post-silicon NWP + Ubuntu | `intel-speed-select` / `turbostat` | End-to-end OS tool → mailbox → firmware flow |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| FW command handler logic error | ✅ | ⚠️ | ✅ | ✅ | indirect |
| RUN_BUSY not clearing (HW hang) | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Invalid command returns wrong error code | ✅ | ⚠️ | ✅ | ✅ | indirect |
| TPMI MMIO access failure | ❌ | ✅ | ✅ | ✅ | ✅ |
| MSR vs TPMI response mismatch | ❌ | ❌ | ❌ | ✅ | ✅ |
| OS driver mailbox timeout | ❌ | ❌ | ❌ | ❌ | ✅ |
| BIOS invalid mailbox programming | ✅ safe | ❌ | ❌ | ❌ risky | ❌ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| Valid command → correct response | ✅ | ✅ | ✅ | PSS: logic; FV: silicon; PV: E2E |
| Invalid command → error code | ✅ | ✅ | ❌ | Negative test |
| RUN_BUSY timeout handling | ⚠️ | ✅ | ✅ | Timing |
| Concurrent mailbox access | ✅ | ✅ | ✅ | Race conditions |
| TPMI vs MSR equivalence | ❌ | ❌ | ✅ | Cross-interface |

---

## Section 5: Risks & Dependencies

### Active Risks

- **RUN_BUSY hang**: If PrimeCode firmware hangs during command processing, RUN_BUSY never clears. OS driver must implement timeout + retry logic.
- **Command set evolution**: New commands added post-tapeout require firmware update; validation must track FW version vs command set.
- **TPMI MMIO vs MSR divergence**: If TPMI MMIO path has a silicon bug, MSR path may still work — must validate both independently.

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | OS driver mailbox timeout handling | PV only | Requires real OS driver stack with timeout logic |
| **G-2** | Multi-threaded concurrent mailbox access from OS | PV only | Requires real multi-core OS scheduling |

---

## Section 6: DFX Considerations

- **Mailbox trace**: PrimeCode firmware trace logs all OS2P command receive/dispatch/response events — use `fw_trace_parser` to decode.
- **VISA capture**: OS_MAILBOX_INTERFACE register writes can be captured via ITH T2 VISA on the OOBMSM TPMI domain.
- **Error injection**: VP (Simics) allows injection of malformed commands and RUN_BUSY stuck conditions for negative testing.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| Concurrent OS + BIOS mailbox access | 16030768338 | Second requester polls RUN_BUSY until first completes |
| Command to fused-off feature | 16030768338 | Returns error code in COMMAND field; OS_MAILBOX_DATA undefined |
| RUN_BUSY stuck (FW hang) | 16030768338 | OS times out at 5 ms; no crash; retries or reports error |
| Write during active transaction (RUN_BUSY=1) | 16030768338 | Write ignored until RUN_BUSY clears |
| TPMI MMIO BAR not configured | 16030768338 | MMIO access fails; MSR fallback must work |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| [16030768338](https://hsdes.intel.com/appstore/article-one/#/16030768338) | [NWP PM] OS2P Mailbox Validation | open | TBD |

### References

- [DMR PM HAS — OS2P Mailbox](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_OS2P.html) — OS_MAILBOX_INTERFACE/DATA register definition, command opcodes
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP OS2P applicability
- [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/TPMI/TPMI.html) — TPMI MMIO architecture for OS2P access

# Deep Analysis: [PSS] Mailbox Sweep — OS2P/B2P PCode Mailbox Interface

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715638 |
| **Title** | [PSS]Mailbox Sweep |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | PM Interfaces > OS2P Mailbox |
| **Sub-Feature** | PMSB Mailbox Command Sweep (B2P + OS2P + TPMI paths) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Parent TCD** | 16030768338 — [NWP PM] OS2P Mailbox Validation |
| **Parent TPF** | 16030767552 — [NWP PM] OS2P Mailbox |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test performs a **systematic sweep of PCode mailbox commands** via the PMSB (Power Management Side-Band) mailbox interface. The sweep validates:
- Every supported mailbox command opcode returns correct status and response data
- Reserved/unsupported command IDs return the defined error code (no hang, no MCA)
- Concurrent mailbox access from multiple agents is handled correctly (serialisation)

The OS2P/B2P mailbox interface is **architecturally unchanged on NWP** — the same command encoding, handler table, and completion code protocol are carried from DMR. Both the CSR transport path (`OS_MAILBOX_INTERFACE` IO registers) and the TPMI transport path (`TPMI_MAILBOX` opcode `0xe`) are supported. NWP topology difference: 2 CBBs (not 4) route through a single IMH die.

**Key Justification:**
- OS2P mailbox fully supported on NWP (same command set, same encoding, same response format)
- All three paths converge on the same PCode mailbox handler table — sweep is transport-agnostic
- NWP Primecode inherits `os_csr_common_v1_0` and `os_tpmi_common_v1_0` flow versions unchanged
- NWP topology simplification: single iMH (`imh0`) aggregates OS2P commands; 2 CBBs only

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions

- NWP silicon/emulation with PCode initialized and CPL3 handoff complete
- OS2P mailbox accessible (CSR path: `OS_MAILBOX_INTERFACE`/`OS_MAILBOX_DATA`; or TPMI path opcode `0xe`)
- TPMI SRAM initialized (for TPMI transport path)
- System in S0; no active thermal throttle or power limit event interfering

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Identify all supported PCode mailbox command IDs from NWP bios_mailbox.xml (`<mbox_access mbox="OS"/>` tags) | Replace DMR XML with NWP equivalent; command IDs unchanged |
| 2 | Issue each valid mailbox command in sequence; record opcode, sub-command, response data, completion code | Same encoding; verify completion code = `0x00` for each supported command |
| 3 | Issue a reserved/unsupported command ID; verify error handling | Expect defined error code, not hang or MCA; verify via NLOG `invalid-parameter` event |
| 4 | Issue concurrent mailbox commands from BIOS (B2P) and OS (OS2P) agents simultaneously | Verify serialisation — exactly one command processed at a time; no deadlock |
| 5 | Run automation script | `python runPmx.py -x nwp.xml -p mailbox_sweep --retry_count 2` |
| 6 | Check NLOG/fw trace for unexpected errors | No error-level events; `invalid-parameter` event appears only for reserved command test |

### Key OS2P Commands to Sweep (NWP)

| Command | Opcode | Sub-cmd | Transport | Notes |
|---------|--------|---------|-----------|-------|
| `READ_PM_CONFIG` | `0x94` | `0x2` (MIN_ICCP), `0x7` (PROG_SSC) | B2P + OS2P | Read PM configuration |
| `WRITE_PM_CONFIG` | write variant | same sub-cmds | B2P + OS2P | Write PM configuration |
| `PM_MISC_CONTROL` | `0xd0` | `0x20` (THERM_MONITOR_STATUS) | OS2P | EWMA decay factor + enable |
| `SET_MC_FREQ` / `READ_MC_FREQ` | varies | — | OS2P | MC refresh parameter lock |
| `PM_SECURITY_CONTROL` | `0xd5` | — | OS2P | UPI SAI filter (ACTM) |
| Reserved/invalid | `0xFF` or any unlisted | — | Any | Must return error, no hang |

### NWP Register Paths

| Register | DMR Path | NWP Path |
|----------|---------|---------|
| OS Mailbox Interface (CSR) | `sv.sockets.imhs.uncore.pcicfg_ubox_cfg.os_mailbox_interface` | `sv.socket0.imh0.uncore.pcicfg_ubox_cfg.os_mailbox_interface` |
| OS Mailbox Data (CSR) | `sv.sockets.imhs.uncore.pcicfg_ubox_cfg.os_mailbox_data` | `sv.socket0.imh0.uncore.pcicfg_ubox_cfg.os_mailbox_data` |
| TPMI OS Mailbox Interface | TPMI opcode `0xe`, line 0 | Same opcode; single iMH on NWP |
| IO Fastpath Mailboxes | CBB-side aggregator | NWP: `sv.socket0.cbb{0,1}.base.punit_regs` — 2 CBBs |

### NWP Pass Criteria

- All valid command IDs return completion code `0x00` and response data within spec range
- Reserved/invalid command IDs return non-zero error code; system remains stable, no MCA, no hang
- Concurrent access: commands serialised; all responses accurate; no deadlock or timeout
- NLOG: `invalid-parameter` event logged only for the reserved command negative test; no error-level events for valid commands

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| OS2P command set | Full set (DMR HAS) | Same set (inherited) | No delta; direct reuse |
| CBB count | 4 CBBs → 2 iMH dies | 2 CBBs → 1 iMH die | Simpler routing; command handling unchanged |
| TPMI transport | TPMI opcode `0xe` | Same opcode; single iMH | Direct reuse; verify NWP TPMI SRAM init |
| Fastpath aggregator | Per-die | Single iMH `imh0` | Routing simplified; no functional change |
| `NOT_SERVICED_ON_THIS_DIE` code | Possible on multi-die | N/A on NWP (single iMH) | Removed edge case on NWP |
| Mailbox availability | After CPL3 | Same | Test entry condition unchanged |

---

## Section D: Key Registers & Validation Points

```python
# NWP: OS2P Mailbox Sweep — CSR path
import time

imh = sv.socket0.imh0

def send_os2p_mailbox(opcode, subcmd=0, data=0, timeout_ms=100):
    """Issue an OS2P mailbox command and return (completion_code, response_data)."""
    # Write data first
    imh.uncore.pcicfg_ubox_cfg.os_mailbox_data.write(data)
    # Build interface register: opcode[7:0] | subcmd[15:8] | run_busy[31]
    intf_val = (opcode & 0xFF) | ((subcmd & 0xFF) << 8) | (1 << 31)
    imh.uncore.pcicfg_ubox_cfg.os_mailbox_interface.write(intf_val)
    # Poll until RUN_BUSY clears
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        val = imh.uncore.pcicfg_ubox_cfg.os_mailbox_interface.read()
        if not (val >> 31 & 1):
            break
        time.sleep(0.001)
    else:
        print(f"Mailbox TIMEOUT: opcode=0x{opcode:02x}")
        return None, None
    intf_final = imh.uncore.pcicfg_ubox_cfg.os_mailbox_interface.read()
    resp_data  = imh.uncore.pcicfg_ubox_cfg.os_mailbox_data.read()
    completion = (intf_final >> 8) & 0xFF
    return completion, resp_data

# Sweep: valid commands
sweep_cmds = [
    (0x94, 0x02, 0, "READ_PM_CONFIG/MIN_ICCP"),
    (0x94, 0x07, 0, "READ_PM_CONFIG/PROG_SSC"),
    (0xd0, 0x20, 0, "PM_MISC_CONTROL/THERM_MONITOR_STATUS read"),
    (0xd5, 0x00, 0, "PM_SECURITY_CONTROL"),
]
for opcode, subcmd, data, name in sweep_cmds:
    cc, resp = send_os2p_mailbox(opcode, subcmd, data)
    status = "PASS" if cc == 0 else f"FAIL (cc=0x{cc:02x})"
    print(f"{name}: cc=0x{cc:02x} resp=0x{resp:08x} [{status}]")

# Negative: reserved command
cc_neg, _ = send_os2p_mailbox(0xFF, 0x00, 0)
print(f"Reserved cmd 0xFF: cc=0x{cc_neg:02x} [{'PASS' if cc_neg != 0 else 'FAIL (no error)'}]")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP bios_mailbox.xml command list** — verify OS2P-tagged opcodes against NWP-specific XML; some DMR commands may be deprecated or added | Low | Walk `<mbox_access mbox="OS"/>` in NWP bios_mailbox.xml |
| 2 | **TPMI transport path** — verify NWP TPMI SRAM init completes before OS2P TPMI test step | Low | Check `tpmi_sram_init` readiness flag before issuing TPMI mailbox commands |
| 3 | **Concurrent access serialisation** — NWP single-iMH simplifies routing but test must still stress B2P + OS2P simultaneously | Medium | Use two threads: one writing B2P from BIOS callback; one issuing OS2P via PythonSV |
| 4 | **`NOT_SERVICED_ON_THIS_DIE` removal** — DMR multi-die edge case may be in existing test script; remove/skip on NWP | Low | Remove any `NOT_SERVICED_ON_THIS_DIE` completion code checks for NWP run |

---

## Section F: Recommendation

**Recommendation: ADOPT — update `dmr.xml` → `nwp.xml`; verify NWP bios_mailbox.xml command list**

The PCode mailbox sweep is a cornerstone PM interface validation test. OS2P is fully supported on NWP with an identical command set. Required adaptations are minimal:

1. Replace `dmr.xml` with `nwp.xml` in automation script invocation
2. Walk NWP `bios_mailbox.xml` for `mbox="OS"` tagged commands to build NWP sweep list
3. Update CBB reference from `cbbs[0-3]` (4-CBB) to `cbb0`, `cbb1` (2-CBB NWP)
4. Remove `NOT_SERVICED_ON_THIS_DIE` edge-case checks (single-iMH NWP)
5. Verify TPMI SRAM initialization before TPMI transport path step

**Priority**: High — fundamental PM interface validation; covers OS2P, B2P, and TPMI transport paths

## References

- [OS2P Mailbox KB Article](../../../../../KB/pm_features/platform_pm_interface/os2p_mailbox.md)
- [B2P Mailbox Specification (HAS)](https://docs.intel.com/documents/primecode/has/DMR/BIOS%20Mailbox/B2P_mailbox_specification.html)
- [HSD TC](https://hsdes.intel.com/appstore/article-one/#/16030715638)
- [Parent TCD HSD](https://hsdes.intel.com/appstore/article-one/#/16030768338)
- Updated: 2026-07-03

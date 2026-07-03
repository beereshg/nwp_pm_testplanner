# TC 16030715638: [PSS] Mailbox Sweep

**TCD:** 16030768338 -- [NWP PM] OS2P Mailbox Validation
**TPF:** 16030767552 -- [NWP PM] OS2P Mailbox
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/pss/mailbox/osmb_tpmi.py` -- `main()` sweeps all OS2P mailbox command IDs 0x00-0xFF
**Secondary Script:** `pm/pmutils/mailbox/os_mailbox.py` -- `os_mailbox()` for individual command invocations

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- DMR has 2 IMH dies (imh0, imh1). **NWP has 1 IMH per CBB** -- use `imh=0` only.
- Mailbox interface path: `socket.imh0.punit.ptpcfsms.ptpcfsms.os_mailbox_interface` -- same register layout on NWP.
- `_MAILBOX_ERRORS` dict in `osmb_tpmi.py` covers all expected return codes; verify NWP adds no new codes.
- PSS environment: requires NWP Simics model; `ACCESS_METHOD` auto-detected via `baseaccess.getaccess()`.

### Test Case Intent
Systematic sweep of all OS-to-PCode (OS2P) mailbox command IDs (0x00 to 0xFF) via the PMSB mailbox interface (`os_mailbox_interface`). For each command ID, issue the mailbox transaction and verify:
1. The mailbox completes without hang (run_busy clears within timeout)
2. Supported commands return `NO_ERROR` (0x00) with valid data
3. Unsupported commands return one of the defined error codes from `_MAILBOX_ERRORS` -- not an unhandled response or hang
4. The `os_mailbox_data` register returns consistent data for read-type commands

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP Simics/emulation booted; PythonSV initialized with `sv.get_all(stop_on_error=True)` |
| 2 | ACCESS_METHOD | `baseaccess.getaccess()` returns valid environment (simics/emulation/silicon) |
| 3 | IMH path | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.os_mailbox_interface` accessible |
| 4 | Mailbox idle | `os_mailbox_interface.run_busy == 0` before starting sweep |
| 5 | NWP IMH count | Only `imh0` used; verify no `imh1` access in NWP invocation |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | `import diamondrapids.pm.pss.mailbox.osmb_tpmi as osmb` | Module loads; `_MAILBOX_ERRORS` dict populated with 55+ error codes; `sv` initialized | ImportError or `sv.get_all()` failure -- check NWP namednodes path |
| 2 | Verify mailbox idle: `osmb.wait(socket.imh0.punit.ptpcfsms.ptpcfsms.os_mailbox_interface)` | `run_busy == 0` within timeout -- mailbox ready for first command | Timeout (>20 iterations) -- mailbox stuck; check PCode init state |
| 3 | Sweep all command IDs: `for i in range(0, 0xff): osmb.os_mailbox(0, 0, i, 0, 0)` | Each command: `run_busy` clears; return code is one of the keys in `_MAILBOX_ERRORS` (0x00-0xFF) | Unknown return code OR `run_busy` stuck -- indicates unhandled mailbox command or hang |
| 4 | For known-good commands (e.g. 0x78 READ_PKG_CONFIG, 0x94 READ_PM_CONFIG): verify return data | `return_code == 0x00` (NO_ERROR); `return_data != 0` for data-returning commands | `return_code != 0x00` for a supported command -- PCode handler error |
| 5 | For unsupported commands: verify error code is defined | Return code in `_MAILBOX_ERRORS` -- not a raw number; `return_data == 0` | Return code not in `_MAILBOX_ERRORS` -- unhandled opcode; PCode should return `UNSUPPORTED_COMMAND` (0x36) or `INVALID_COMMAND` (0x01) |
| 6 | Verify `os_mailbox_data` integrity after each command | Data register reads back the value written for write-path commands; no residual data from prior command | Stale data in mailbox data register -- `os_mailbox_data` not cleared between commands |
| 7 | Confirm "OMSB_TPMI DONE" printed (script completion marker) | All 255 command IDs swept without exception or hang | Exception mid-sweep -- capture last command ID; check `_MAILBOX_ERRORS` for the return code |

### Pass / Fail Criteria

- **PASS:** All 255 command IDs complete without hang; every return code is a defined entry in `_MAILBOX_ERRORS`; known-good commands return `NO_ERROR`; unsupported commands return a defined error code.
- **FAIL:** Any command causes `run_busy` to never clear (hang); return code not in `_MAILBOX_ERRORS`; exception raised mid-sweep; known-good command returns non-zero error.

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Write command to `os_mailbox_interface` (command + run_busy=1) | OS2P PMSB |
| 2 | PCode | Receive mailbox command; execute handler | Internal |
| 3 | PCode | Write result to `os_mailbox_data`; clear `run_busy` | OS2P PMSB |
| 4 | Test script | Read `return_code` from `os_mailbox_interface.command` | OS2P PMSB |
| 5 | Test script | Validate `return_code` in `_MAILBOX_ERRORS` | Python dict lookup |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | osmb_tpmi | `os_mailbox_interface` | write: command=i, run_busy=1 | PMSB register |
| 2 | PCode | handler table | dispatch to command handler i | Internal |
| 3 | PCode | `os_mailbox_data` | write return_data | PMSB register |
| 4 | PCode | `os_mailbox_interface.command` | write return_code; clear run_busy | PMSB register |
| 5 | osmb_tpmi | `_MAILBOX_ERRORS` | lookup return_code | Python |

---

## Section C: Coverage

| Dimension | Coverage |
|-----------|---------|
| **Command range** | 0x00-0xFF (all 255 command IDs) |
| **Known-good** | 0x78 READ_PKG_CONFIG, 0x94 READ_PM_CONFIG, 0xD0 cmd_pm_misc_control |
| **Error codes** | All 55 entries in `_MAILBOX_ERRORS` verified reachable |
| **IMH scope** | imh0 only (NWP) |
| **Environments** | Simics, emulation, silicon (auto-detected) |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `imh0.punit.ptpcfsms.ptpcfsms.os_mailbox_interface` | `command`, `run_busy` | `run_busy` clears within 20s; `command` field = return code |
| `imh0.punit.ptpcfsms.ptpcfsms.os_mailbox_data` | full register | Contains return data for data-returning commands |
| `_MAILBOX_ERRORS` dict | 0x00-0xFF | All return codes must be defined entries |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| NWP may not support all DMR mailbox commands (e.g. DIMM/memory commands if no DRAM) | Medium | Low | Expected to return `NOT_SERVICED_ON_THIS_DIE` (0xFF) or `UNSUPPORTED_COMMAND` -- not a failure |
| `osmb_tpmi.py` uses `imh1` in any path | Low | High | Verify NWP invocation uses `imh=0` only -- `imh1` not available |
| Simics model may not implement all command handlers | Medium | Medium | Mark unimplemented commands as KNOWN_GAP; compare to silicon results |

---

## Section F: Recommendations

1. **NWP port:** Change loop in `main()` to also log command name from `_MAILBOX_ERRORS` for easier debug.
2. **Classify return codes:** Pass = `NO_ERROR` for known commands; Pass = any defined error for unsupported; Fail = undefined return code or hang.
3. **NWP invocation:**
   ```python
   import diamondrapids.pm.pss.mailbox.osmb_tpmi as osmb
   for i in range(0, 0xff):
       data, err_str = osmb.os_mailbox(socket_number=0, imh=0, command=i, sub_command=0, parameter=0)
       assert err_str in osmb._MAILBOX_ERRORS.values(), f"cmd={i:#x}: unknown return code"
   print("OMSB_TPMI DONE")
   ```

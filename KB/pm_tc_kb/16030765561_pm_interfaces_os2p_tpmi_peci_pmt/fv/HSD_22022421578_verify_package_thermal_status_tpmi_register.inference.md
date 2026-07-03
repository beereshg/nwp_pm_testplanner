# TC 22022421578: [TPMI/PMT] Verify Package Thermal Status TPMI Register

**TCD:** 22022420612 -- [SoC Thermal Management] TPMI/PMT
**TPF:** 16030767555 -- [NWP PM] PMT
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/Active_PM/Thermal_Management/CPU_Thermal_Management/PMT_Thermals.py` -- `PMT.thermal_status(s, self.log)`
**Library:** `pmt_dataintegrity.thermal_status(socket)` -- reads mailbox, register, MSR 0x1B1 before and after thermal event

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- DMR Simics path for prochot inject: `run_command("oakstream.mb.mcp0.imh_die0.punit.punit[0]->prochot_trigger=TRUE")` -- **NWP Simics path will differ** (check NWP Simics model target name).
- Silicon path: `socket.imh0.pcodeio_map.io_throttle_signals_override.global_prochot_hw_inject = 0x1` -- same register on NWP.
- NWP has 2 CBBs; `ref_temp` reads from `cbb0.compute0.module0.core0.pcu_cr_temperature_target` -- valid for NWP CBB0.
- MSR 0x1B1 (`IA32_PACKAGE_THERM_STATUS`) is architecturally unchanged.

### Test Case Intent
Verify that the **Package Thermal Status TPMI register** (MSR 0x1B1) correctly reflects thermal events. The test:
1. Reads baseline status from mailbox, MMIO register, and MSR 0x1B1
2. Triggers a thermal event: core temperature injection above TjMax + global PROCHOT assertion
3. Reads status again and verifies the expected bit fields changed:
   - `thermal_monitor_status` = 1
   - `thermal_monitor_log` = 1
   - `prochot_status` = 1
   - `prochot_log` = 1
   - `out_of_spec_status` = 1

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP silicon/emulation booted; PythonSV initialized |
| 2 | Baseline | No active thermal events; MSR 0x1B1 status bits clear |
| 3 | PROCHOT inject | `io_throttle_signals_override.global_prochot_hw_inject` writable (silicon) OR Simics NWP model supports prochot trigger |
| 4 | Temperature ref | `cbb0.compute0.module0.core0.pcu_cr_temperature_target` bits[16:24] = TjMax readable |
| 5 | Status registers | Mailbox, MMIO register, MSR 0x1B1 all accessible |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Clear idle values: `clear_idle_values(socket)` + wait 1s | No active thermal events; all status bits clear; `run_busy == 0` | Pre-existing status bits set -- clear via MSR write before proceeding |
| 2 | Read baseline mailbox status: `Mailbox_Package_thermal_status = read_mailbox_status(socket)` | `thermal_monitor_status == 0`, `prochot_status == 0` | Non-zero status at baseline -- check for previous thermal events |
| 3 | Read baseline MSR 0x1B1: `pd.debug.access_to_msr(0x1b1, core=0)` | MSR thermal status bits = 0 at baseline | Pre-existing MSR status -- BIOS may need to clear |
| 4 | **Trigger thermal event:** `injection.Clear_Core(Temperature_limit + 10, external=True)` + `socket.imh0.pcodeio_map.io_throttle_signals_override.global_prochot_hw_inject = 0x1` | Core temperature exceeds TjMax; PROCHOT asserted; PCode updates TPMI Package Thermal Status | No change in status after injection -- check injection path on NWP |
| 5 | Read status after event: `Mailbox_Package_thermal_status_after = read_mailbox_status(socket)` | `thermal_monitor_status == 1`, `thermal_monitor_log == 1`, `prochot_status == 1`, `prochot_log == 1`, `out_of_spec_status == 1` | Missing status bits -- TPMI Package Thermal Status not updating from thermal event |
| 6 | Read MSR 0x1B1 after event | MSR bits 0 (thermal_monitor_status), 1 (log), 10 (prochot_status), 11 (prochot_log) = 1 | MSR not updated -- PCode not writing MSR 0x1B1 on thermal event |
| 7 | Read MMIO register status after event | Consistent with mailbox and MSR | Register inconsistent with mailbox -- data path bug |
| 8 | Compare mailbox_status_after, register_status_after, msr_status_after via tabulate | All "Pass" rows -- 3-way consistency confirmed | Any "Fail" row -- specific path not updating |
| 9 | Clear thermal event: disable PROCHOT inject; `injection.Clear_Core(40, external=True)` | Thermal event cleared; status bits de-assert (log bits remain set until cleared by software) | Status bits not de-asserting -- check override register |

### Pass / Fail Criteria

- **PASS:** After thermal event: `thermal_monitor_status`, `prochot_status`, `out_of_spec_status` all = 1 in mailbox, MMIO register, and MSR 0x1B1; 3-way consistency confirmed; `thermal_status()` returns `True`.
- **FAIL:** Status bits do not set after thermal event in any of the 3 readout paths; `thermal_status()` returns `False`.

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Read baseline mailbox/register/MSR status | PMSB / MMIO / MSR |
| 2 | Test script | Inject temperature + assert PROCHOT | DTS override + MMIO |
| 3 | PCode | Detect thermal event; update Package Thermal Status | Internal |
| 4 | PCode | Write TPMI register + MSR 0x1B1 | TPMI / MSR |
| 5 | Test script | Read post-event mailbox/register/MSR | PMSB / MMIO / MSR |
| 6 | Test script | Compare all 3 paths via tabulate | Python |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Script | clear_idle_values | clear status | namednodes |
| 2 | Script | imh0.pcodeio_map | global_prochot_hw_inject = 1 | MMIO |
| 3 | PCode | TPMI Package Thermal Status | set status bits | TPMI |
| 4 | PCode | MSR 0x1B1 | set IA32_PACKAGE_THERM_STATUS | MSR |
| 5 | Script | read_mailbox_status() | read via DFX mailbox | DFX mailbox |
| 6 | Script | read_register_status() | read MMIO | namednodes |
| 7 | Script | read_msr_status() | read MSR 0x1B1 | pstatesDebug |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `imh0.pcodeio_map.io_throttle_signals_override.global_prochot_hw_inject` | bit 0 | Set to 1 to trigger PROCHOT |
| MSR 0x1B1 `IA32_PACKAGE_THERM_STATUS` | bits 0,1,10,11 | Must set after thermal event |
| TPMI PackageThermalStatus (via DFX mailbox) | thermal_monitor_status, prochot_status | Must match MSR bits |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| NWP Simics prochot trigger path differs from DMR (`oakstream.mb.mcp0...`) | High | High | Identify NWP Simics model prochot trigger command before silicon test |
| `read_mailbox_status()` uses DMR-specific DFX mailbox opcodes | Medium | Medium | Verify opcodes against NWP HAS mailbox command table |

---

## Section F: Recommendations

1. Identify NWP Simics prochot trigger command (check NWP Simics model docs).
2. Verify `read_mailbox_status()` DFX mailbox opcodes are valid for NWP.
3. **NWP invocation:** `python runPmx.py -x nwp.xml -p PMT_Thermals -tM 60 -M 5`

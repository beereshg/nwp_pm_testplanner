# TC 22022421583: [TPMI/PMT] Verify Thermal Constrained Time PMT Register

**TCD:** 22022420612 -- [SoC Thermal Management] TPMI/PMT
**TPF:** 16030767555 -- [NWP PM] PMT
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/Active_PM/Thermal_Management/CPU_Thermal_Management/PMT_Thermals.py` -- `PMT.throttled_time(s, self.log)`
**Library:** `pmt_dataintegrity.throttled_time(socket)` -- reads `total_cbb_throttled_time` and DFX mailbox for each CBB, injects temperature above TjMax

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- DMR script reads `value0`-`value3` (CBB0-CBB3) via `cbb0`-`cbb3.pcode.vars.telemetry_handler.total_cbb_throttled_time.data`.
- **NWP: only CBB0 and CBB1 exist** -- remove CBB2 (`imh1.oobmsm` mailbox, `0x000a020012810908`) and CBB3 (`0x000b020012810908`).
- DMR uses `imh0` for CBB0/CBB1 and `imh1` for CBB2/CBB3. **NWP uses `imh0` only for both CBB0 and CBB1**.
- NWP DFX mailbox opcodes for CBB0: `0x000a020010810908`; CBB1: `0x000b020010810908` -- both via `imh0`.
- Temperature injection: `injection.Clear_SOC(107)` -- 107°C above TjMax to trigger throttling; valid on NWP.

### Test Case Intent
Verify that the **Thermal Constrained Time PMT register** (`total_cbb_throttled_time`) correctly tracks and increments when thermal throttling occurs. The test:
1. Reads initial throttled time from pcode vars and DFX mailbox for each CBB
2. Injects temperature above TjMax (107°C) to trigger SoC thermal throttling
3. Reads throttled time again and verifies the counter has increased (throttling was counted)

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP silicon/emulation; PythonSV initialized |
| 2 | CBB pcode vars | `sv.socket0.cbb0.pcode.vars.telemetry_handler.total_cbb_throttled_time.data` readable |
| 3 | DFX mailbox | `imh0.oobmsm.oobmsm0.oobmsm_reg.dfx_mailbox` accessible |
| 4 | Temperature injection | `injection.Clear_SOC(107)` functional -- can inject temperature above TjMax |
| 5 | No pre-throttling | `total_cbb_throttled_time.data == 0` or known baseline before test |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read initial CBB0 throttled time: `value0 = hex(socket.cbb0.pcode.vars.telemetry_handler.total_cbb_throttled_time.data)` | Value readable; note initial count (may be 0 or non-zero if previous throttling) | Access error -- check pcode vars path on NWP |
| 2 | Read initial CBB1 throttled time: `value1 = hex(socket.cbb1.pcode.vars.telemetry_handler.total_cbb_throttled_time.data)` | Value readable; note initial count | Access error -- check CBB1 path |
| 3 | Read initial CBB0 via DFX mailbox: opcode `0x000a020010810908`, dfx_mailbox[1]=0x12, dfx_mailbox_ctl[31]=1 | `dfx_throttle_initial_cbb0 = hex((dfx_mailbox[0] & 0xFFFFFFFF00000000) >> 40)` | Mailbox timeout -- check NWP opcode validity |
| 4 | Read initial CBB1 via DFX mailbox: opcode `0x000b020010810908` (NWP: via `imh0`, not `imh1`) | `dfx_throttle_initial_cbb1` extracted | Mailbox failure -- verify NWP CBB1 opcode and IMH path |
| 5 | Inject temperature: `injection.Clear_SOC(107, external=True)` + wait (simics: `run-cycles 1B`; silicon: `time.sleep(1)`) | Temperature injection accepted; SoC thermal throttling triggered | Injection not accepted -- check DTS override enable |
| 6 | Read final CBB0 pcode vars throttled time | `final_value0 > initial_value0` (counter incremented during throttling) | Counter not incremented -- throttling may not have been triggered or counter not updating |
| 7 | Read final CBB1 pcode vars throttled time | `final_value1 > initial_value1` | Counter not incremented for CBB1 |
| 8 | Read final via DFX mailbox for CBB0 and CBB1 | DFX mailbox values also incremented; match pcode vars final values | Mismatch between pcode vars and DFX mailbox -- PMT data integrity issue |
| 9 | Clear injection: `injection.Clear_SOC(40, external=True)` | Throttling stops; temperature returns to baseline | Throttling stuck -- override register not clearing |
| 10 | `throttled_time()` returns `True` | All counters incremented; pcode vars match DFX mailbox | Returns `False` -- "Thermal Constrained Time PMT Register Fail" |

### Pass / Fail Criteria

- **PASS:** `total_cbb_throttled_time` increments for both CBB0 and CBB1 after thermal injection; DFX mailbox readout matches pcode vars; `throttled_time()` returns `True`.
- **FAIL:** Counter does not increment (throttling not triggered); or counter increments but DFX mailbox does not match (PMT data integrity failure).

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Read initial throttled time (pcode vars) | namednodes |
| 2 | Test script | Read initial throttled time (DFX mailbox) | DFX mailbox |
| 3 | Test script | Inject 107°C via Clear_SOC | DTS override |
| 4 | PCode | Detect throttle condition; increment counter | Internal |
| 5 | Test script | Read final throttled time (pcode vars) | namednodes |
| 6 | Test script | Read final throttled time (DFX mailbox) | DFX mailbox |
| 7 | Test script | Compare initial vs final; pcode vars vs mailbox | Python |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Script | cbb0/cbb1.pcode.vars.telemetry_handler | read total_cbb_throttled_time | namednodes |
| 2 | Script | dfx_mailbox opcode 0x000a020010810908 | read CBB0 throttled time | DFX mailbox |
| 3 | Script | dfx_mailbox opcode 0x000b020010810908 | read CBB1 throttled time (NWP: imh0) | DFX mailbox |
| 4 | Thermal_DTS | SOC DTS | inject 107C | DTS override |
| 5 | PCode | total_cbb_throttled_time | increment counter | pcode vars |
| 6 | Script | re-read via pcode vars + mailbox | compare | Python |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `cbb0.pcode.vars.telemetry_handler.total_cbb_throttled_time.data` | full register | Must increment after throttle |
| DFX mailbox CBB0 opcode `0x000a020010810908` + sub 0x12 | bits[39:8] | Must match pcode vars |
| DFX mailbox CBB1 opcode `0x000b020010810908` + sub 0x12 | bits[39:8] | Must match pcode vars |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| Script uses `imh1` for CBB2/CBB3 DFX mailbox -- must be removed for NWP | High | High | Remove CBB2/CBB3 mailbox reads; remap CBB1 mailbox to `imh0` |
| DFX mailbox opcode for CBB1 on NWP may differ (was `imh1.oobmsm` on DMR) | Medium | High | Verify CBB1 opcode via NWP HAS; use `imh0` for both CBBs |
| 107°C injection may not trigger throttling if TjMax > 107°C | Low | Medium | Use `socket.imh0.punit.ptpcioregs.package_temperature` to confirm throttle triggered |

---

## Section F: Recommendations

1. **Remove CBB2/CBB3** reads from NWP invocation of `throttled_time()`.
2. **Remap CBB1 DFX mailbox** from `imh1.oobmsm` (DMR) to `imh0.oobmsm` (NWP).
3. Verify DFX mailbox opcode `0x000b020010810908` (CBB1 via IMH0) in NWP mailbox HAS.
4. **NWP invocation:** `python runPmx.py -x nwp.xml -p PMT_Thermals -tM 60 -M 5`

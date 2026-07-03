# TC 22022421581: [TPMI/PMT] Verify Temperature Target PMT Register

**TCD:** 22022420612 -- [SoC Thermal Management] TPMI/PMT
**TPF:** 16030767555 -- [NWP PM] PMT
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/Active_PM/Thermal_Management/CPU_Thermal_Management/PMT_Thermals.py` -- `PMT.temp_target(s, self.log)`
**Library:** `pmt_dataintegrity.temp_target(socket)` -- 3-way comparison of FAN_TEMP_TARGET_OFFSET, REF_TEMP, TJ_MAX_TCC_OFFSET

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- Reads `temperature_target` from `cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target` -- verify this path exists on NWP.
- MSR 0x1A2 (`IA32_TEMPERATURE_TARGET`) is architecturally unchanged on NWP.
- DFX mailbox opcodes: `0x000a020010810908` (CBB0) for ref_temp/tj_max_tcc_offset; `0x01a20010b10905` for fan_temp -- verify on NWP.
- NWP has 1 IMH (imh0); DFX mailbox via `imh0.oobmsm.oobmsm0.oobmsm_reg.dfx_mailbox`.

### Test Case Intent
Verify that the **Temperature Target PMT register** reflects correct thermal target values from three independent readout paths:
1. **Register:** `temperature_target` MMIO register (bits: FAN_TEMP_TARGET_OFFSET [15:8], REF_TEMP [23:16], TJ_MAX_TCC_OFFSET [31:24])
2. **MSR:** IA32_TEMPERATURE_TARGET (MSR 0x1A2) -- same fields
3. **DFX Mailbox:** PCS index 0x10 (ref_temp, tj_max_tcc_offset) and MSR-read opcode (fan_temp_target_offset)

All three must agree on the same values for FAN_TEMP_TARGET_OFFSET, REF_TEMP, and TJ_MAX_TCC_OFFSET.

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP silicon/emulation; PythonSV initialized |
| 2 | CBB0 path | `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target` accessible |
| 3 | MSR access | `read_msr(0x1a2, core=0)` via pstatesDebug functional |
| 4 | DFX mailbox | `imh0.oobmsm.oobmsm0.oobmsm_reg.dfx_mailbox` accessible; mailbox idle |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read register: `temperature_target = socket.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target` | Non-zero value; extract: `fan_temp_target_ofst = bits[15:8]`, `ref_temp = bits[23:16]`, `tj_max_tcc_offset = bits[31:24]` | Zero -- invalid register path on NWP; check namednodes path |
| 2 | Read MSR 0x1A2: `msr_read = read_msr(0x1a2, 0)` | Non-zero; same field extraction: `mrs_fan_temp = bits[15:8]`, `mrs_ref_temp = bits[23:16]`, `mrs_tj_max = bits[31:24]` | Zero -- MSR read path issue |
| 3 | Read via DFX mailbox (CBB0 PCS 0x10): write opcode `0x000a020010810908`, set dfx_mailbox[1]=0x10, dfx_mailbox_ctl[31]=1 | Mailbox completes; `mailbox_ref_temp = bits[31:24]`, `mailbox_tj_max_tcc_offset = bits[39:32]` | Mailbox timeout or zero -- NWP DFX mailbox opcode may differ |
| 4 | Read via DFX mailbox (FAN_TEMP opcode): write `0x01a20010b10905`, set dfx_mailbox_ctl[31]=1 | `mailbox_fan_temp_target_ofst = bits[23:16]` extracted | Zero -- FAN_TEMP mailbox opcode may differ on NWP |
| 5 | Compare FAN_TEMP_TARGET_OFFSET: register == MSR == mailbox | All 3 values equal; tabulate shows "Pass" | Mismatch -- one readout path inconsistent; log values for debug |
| 6 | Compare REF_TEMP: register == MSR == mailbox | All 3 values equal; tabulate shows "Pass" | Mismatch -- check if NWP PCS index 0x10 returns same encoding |
| 7 | Compare TJ_MAX_TCC_OFFSET: register == MSR == mailbox | All 3 values equal; tabulate shows "Pass" | Mismatch -- TCC offset may be customer-programmed (defaults to 0) |
| 8 | `temp_target()` returns `True` | All checks pass | Returns `False` -- `self.print_and_exit` called with "Temperature Target PMT Register Fail" |

### Pass / Fail Criteria

- **PASS:** FAN_TEMP_TARGET_OFFSET, REF_TEMP, and TJ_MAX_TCC_OFFSET all match across register, MSR 0x1A2, and DFX mailbox readouts; `temp_target()` returns `True`.
- **FAIL:** Any field mismatch between the 3 readout paths; `temp_target()` returns `False`.

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Read temperature_target MMIO | namednodes |
| 2 | Test script | Read MSR 0x1A2 via pstatesDebug | MSR |
| 3 | Test script | Write DFX mailbox opcode; read result | DFX mailbox |
| 4 | Test script | Compare all 3 paths via tabulate | Python |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Script | cbb0.temperature_target | read MMIO | namednodes |
| 2 | Script | pstatesDebug.access_to_msr(0x1a2) | read MSR | MSR |
| 3 | Script | dfx_mailbox opcode 0x10 | read PCS index | DFX mailbox |
| 4 | Script | dfx_mailbox opcode 0x01a20010b10905 | read FAN_TEMP via MSR path | DFX mailbox |
| 5 | Script | tabulate | 3-way compare | Python |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target` | bits [15:8], [23:16], [31:24] | Match MSR and mailbox |
| MSR 0x1A2 `IA32_TEMPERATURE_TARGET` | bits [15:8], [23:16], [31:24] | Match register and mailbox |
| DFX mailbox PCS 0x10 (opcode `0x000a020010810908`) | bits [31:24], [39:32] | Match register and MSR |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| NWP CBB path for `temperature_target` may differ | Low | High | Use `sv.socket0.search('temperature_target')` to find on NWP |
| DFX mailbox opcode `0x01a20010b10905` is MSR 0x1A2 read via mailbox -- NWP encoding may differ | Medium | Medium | Verify opcode against NWP mailbox command table |
| TJ_MAX_TCC_OFFSET = 0 by default (customer-programmed) -- not a failure | Low | Low | Accept 0 as valid if SKU does not apply TCC offset |

---

## Section F: Recommendations

1. Verify both DFX mailbox opcodes against NWP HAS mailbox command table before silicon test.
2. If `cbb0` register path fails on NWP, use `sv.socket0.search('temperature_target')` to find correct path.
3. **NWP invocation:** `python runPmx.py -x nwp.xml -p PMT_Thermals -tM 60 -M 5`

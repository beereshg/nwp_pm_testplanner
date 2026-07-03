# TC 22022421558: [TPMI/PMT] Verify Aggregate Margin to Tcontrol PMT Register

**TCD:** 22022420612 -- [SoC Thermal Management] TPMI/PMT
**TPF:** 16030767555 -- [NWP PM] PMT (Platform Monitoring Technology)
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/Active_PM/Thermal_Management/CPU_Thermal_Management/PMT_Thermals.py` -- `PMT.t_control(s, self.log)`
**Library:** `pm/Active_PM/Thermal_Management/CPU_Thermal_Management/pmt_dataintegrity.py` -- `t_control(socket)`
**Run via PMX:** `runPmx.py -x dmr.xml -p PMT_Thermals -tM 60 -M 5`

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- DMR has 4 CBBs; **NWP has 2 CBBs** -- `cbb0`, `cbb1` only. Script accesses `cbb0`-`cbb3` for throttled_time; adapt to `cbb0`, `cbb1`.
- DMR has 2 IMH dies; **NWP has 1 IMH** -- `imh0` only.
- Simics path for fuse: `socket.imh0.fuses.punit.virtual.pcode_t_control_offset_df` (same as DMR).
- Formula: `T_Control = (eff_TjMax - fused_T_control_offset + dts_config3 * Tcontrol_OFFSET) - Max_temperature` -- unchanged.
- `dmr.xml` PMX tag -- update to NWP equivalent XML or invoke standalone.

### Test Case Intent
Verify that the **Aggregate Margin to Tcontrol** PMT register correctly reports the thermal margin between the maximum die temperature and the TControl threshold. The margin is computed from:
- `EFFECTIVE_TJ_MAX` (from `temperature_target` register, bits 16:24)
- `FUSED_T_CONTROL_OFFSET` (from `imh0.fuses.punit.pcode_t_control_offset`)
- `DTS_CONFIG3.Tcontrol_OFFSET` (from `imh0.punit.ptpcioregs.ptpcioregs.dts_config3_cfg`)
- `MAX_TEMPERATURE` (from `imh0.punit.ptpcioregs.ptpcioregs.package_temperature` minus 64)

The register value is compared with the DFX mailbox readout of the same field to confirm PMT data integrity.

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP silicon/emulation booted; PythonSV initialized |
| 2 | CBBs | CBB0, CBB1 active (`sv.socket0.cbbs` accessible) |
| 3 | IMH | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature` readable |
| 4 | Fuse access | `sv.socket0.imh0.fuses.punit.pcode_t_control_offset` readable (silicon) or `.virtual.pcode_t_control_offset_df` (simics) |
| 5 | DTS injection | `Thermal_DTS.Clear_Core()` functional -- ability to inject random temperature |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Inject random temperature: `injection.Clear_Core(random.randint(40, 105), external=True)` | DTS temperature set on all cores; package_temperature register updates | DTS override not accepted -- check Simics model or silicon override enable |
| 2 | Read `temperature_target`: `socket.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target` | Register readable; `effective_tj_max = bits[16:24]` extracted correctly | Zero or invalid value -- check CBB0 register path on NWP |
| 3 | Read T_Control fuse: `socket.imh0.fuses.punit.pcode_t_control_offset` (silicon) | Non-zero value from fuse; matches expected NWP SKU TControl offset | Zero fuse -- may indicate fuse read path error |
| 4 | Compute T_Control formula from register/fuse values | `T_Control = (eff_tj_max - fused_t_ctrl_offset - fused_t_ctrl_offset + dts_config3 * Tcontrol_OFFSET) - Max_temp` matches expected range | Negative or out-of-range T_Control -- verify formula operands |
| 5 | Read T_Control via DFX mailbox: `dfx_mailbox[0] = 0x000a020010810908; dfx_mailbox[1] = 0x10; dfx_mailbox_ctl[31] = 1` | Mailbox completes; `DFX_Mailbox_TControl_decimal` computed via `s10_6_to_decimal(bits[8:23])` | Mailbox timeout or zero response -- IMH DFX mailbox not functional |
| 6 | Compare: `T_Control == DFX_Mailbox_TControl_decimal` | Values match within floating-point precision; tabulate() shows "Pass" for both rows | Mismatch -- PMT T_Control register not reflecting register/fuse computation; check formula operand source |
| 7 | Clear DTS injection: `injection.Clear_Core(40, external=True)` | Package temperature returns to ~40°C baseline; no thermal events remain | Temperature not clearing -- injection override stuck |

### Pass / Fail Criteria

- **PASS:** `T_Control` computed from register/fuse equals `DFX_Mailbox_TControl_decimal`; tabulate shows all rows "Pass"; `t_control()` returns `True`.
- **FAIL:** Mismatch between register-computed T_Control and DFX mailbox PMT value; `t_control()` returns `False`; `self.print_and_exit` called with "Aggregate Margin to Tcontrol PMT Register Fail".

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Inject random temperature via `Clear_Core()` | DTS override (Thermal_DTS) |
| 2 | PCode | Update `package_temperature` and T_Control computation | Internal |
| 3 | Test script | Read `temperature_target` and fuse registers | namednodes MMIO |
| 4 | Test script | Compute T_Control formula | Python math |
| 5 | Test script | Read T_Control via DFX mailbox | DFX mailbox (PMSB) |
| 6 | Test script | Compare register-computed vs mailbox PMT value | Python tabulate |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Thermal_DTS | Core DTS | inject temperature | DTS override |
| 2 | PCode | package_temperature register | update | IO register |
| 3 | Script | cbb0.temperature_target | read | namednodes |
| 4 | Script | imh0.fuses.punit | read T_Control offset | namednodes |
| 5 | Script | dfx_mailbox[0,1] + dfx_mailbox_ctl[31] | write opcode; set run bit; read result | DFX mailbox |
| 6 | Script | tabulate | compare & report | Python |

---

## Section C: Coverage

| Dimension | Coverage |
|-----------|---------|
| **Formula operands** | effective_tj_max, fused_t_control_offset, dts_config3, max_temperature |
| **Verification paths** | Register/fuse computation vs DFX mailbox PMT |
| **CBBs** | CBB0 (NWP); DMR uses CBB0-3 |
| **IMH** | imh0 only (NWP) |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target` | bits[16:24] = effective_tj_max | Non-zero; matches expected TjMax |
| `imh0.fuses.punit.pcode_t_control_offset` | full register | Non-zero fuse value for NWP SKU |
| `imh0.punit.ptpcioregs.ptpcioregs.dts_config3_cfg` | Tcontrol_OFFSET | Used in formula |
| `imh0.punit.ptpcioregs.ptpcioregs.package_temperature` | full register | Max_temperature = value - 64 |
| `imh0.oobmsm.oobmsm0.oobmsm_reg.dfx_mailbox[0]` | bits[8:23] after opcode 0x10 | T_Control in s10.6 format |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| NWP CBB path differs for `temperature_target` (cbb0 vs cbb1 CBB-specific register) | Low | Medium | Verify `cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.temperature_target` exists on NWP; use namednodes.search() |
| DFX mailbox opcode 0x10 may differ on NWP | Medium | High | Check NWP mailbox command table in HAS; confirm 0x000a020010810908 is valid |
| Formula discrepancy in double-subtraction of `fused_t_control_offset` | Low | Medium | Script has `- fused_t_control_offset - fused_t_control_offset` (appears twice); verify against HAS formula |

---

## Section F: Recommendations

1. Verify NWP mailbox opcode `0x000a020010810908` (CBB0 PCS index 0x10) is correct in NWP HAS.
2. Check the formula: the script subtracts `fused_t_control_offset` twice -- this may be intentional (offset applied twice) or a bug vs HAS spec.
3. **NWP invocation:** `python runPmx.py -x nwp.xml -p PMT_Thermals -tM 60 -M 5`

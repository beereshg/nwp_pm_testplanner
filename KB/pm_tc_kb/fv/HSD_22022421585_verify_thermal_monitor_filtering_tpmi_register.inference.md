# TC 22022421585: [TPMI/PMT] Verify Thermal Monitor Filtering TPMI Register

**TCD:** 22022420612 -- [SoC Thermal Management] TPMI/PMT
**TPF:** 16030767555 -- [NWP PM] PMT
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/Active_PM/Thermal_Management/CPU_Thermal_Management/PMT_Thermals.py` -- `PMT.thermal_status(s, self.log)` (Monitor_Filtering() is a stub)
**TPMI read path:** `pm/OOBMSM/tpmi/tpmi_register.py` -- `tpmi_get_set_state_mmio('THERMAL_MGMT', get_set=0)`
**Register:** `imh0.punit.ptpcfsms.ptpcfsms.opc_thermal_monitor` (partial -- stub in script; see recommendation)

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- `Monitor_Filtering()` in `pmt_dataintegrity.py` is a **stub** -- the body only has a single line accessing `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_thermal_monitor` with no logic. **Script not fully implemented for this TC.**
- Main verification path: `tpmi_get_set_state_mmio(tpmi_name='THERMAL_MGMT', get_set=0)` from `tpmi_register.py`.
- The TC extends TC 22022421578 (Package Thermal Status) by verifying the **Tau-derived time delay** for thermal monitor filtering.
- NWP: `imh0.punit.ptpcfsms.ptpcfsms.opc_thermal_monitor` -- same register path as DMR imh0.
- Gap: `Monitor_Filtering()` function needs to be implemented before this TC can run fully.

### Test Case Intent
Verify that the **Thermal Monitor Filtering TPMI register** correctly controls the time delay (derived from the Tau value) before the Thermal Monitor Filter (TM2) de-asserts after a thermal event clears. The test:
1. Reads the current Tau value from the TPMI `THERMAL_MONITOR_FILTERING` register
2. Triggers a thermal event (prochot or temperature above TjMax)
3. After thermal event clears, measures the de-assertion delay
4. Confirms de-assertion delay matches the Tau-derived value: `Delay = 2^Tau * 0.977ms`

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP silicon/emulation; PythonSV initialized |
| 2 | TPMI access | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_thermal_monitor` readable |
| 3 | Script | `Monitor_Filtering()` in `pmt_dataintegrity.py` must be implemented (currently stub) |
| 4 | TPMI register tool | `tpmi_get_set_state_mmio('THERMAL_MGMT', socket_id=0, imh_num=0, get_set=0)` functional |
| 5 | Package Thermal Status | TC 22022421578 must pass first (shared infrastructure) |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read TPMI Thermal Monitor Filtering register: `tpmi_get_set_state_mmio('THERMAL_MGMT', socket_id=0, imh_num=0, get_set=0)` | Register readable; Tau field extracted (bits for filter time constant) | Read failure -- TPMI path not accessible; check `tpmi_structure_dmr0_file` mapping for NWP |
| 2 | Read raw register: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_thermal_monitor.read()` | Returns current filter setting; Tau value in bits [N:M] per HAS | Zero or invalid -- register not initialized; check BIOS init |
| 3 | Trigger thermal event: `socket.imh0.pcodeio_map.io_throttle_signals_override.global_prochot_hw_inject = 0x1` | Thermal monitor asserts (`thermal_monitor_status == 1`); TPMI status register updated | Status not setting -- PROCHOT injection not working |
| 4 | Clear thermal event: disable prochot inject | Thermal event clears; start timer to measure de-assertion delay | Event not clearing -- check override register |
| 5 | Poll `opc_thermal_monitor` de-assertion (or `thermal_monitor_status` bit) with 1ms resolution | De-assertion occurs after delay matching `2^Tau * 0.977ms` | De-assertion too fast (no filter) or too slow (wrong Tau) -- Tau value mismatch |
| 6 | Write new Tau value: `tpmi_get_set_state_mmio('THERMAL_MGMT', get_set=1, state=new_tau)` | TPMI register updated to new Tau | Write rejected -- check lock bit in TPMI register |
| 7 | Repeat steps 3-5 with new Tau | De-assertion delay changes proportionally to new Tau: `delay = 2^new_tau * 0.977ms` | Delay unchanged -- TPMI write not taking effect |
| 8 | Restore original Tau value | TPMI register restored to initial value | Write failure |

### Pass / Fail Criteria

- **PASS:** Thermal monitor de-assertion delay matches Tau-derived formula (`2^Tau * 0.977ms`); TPMI write modifies the delay proportionally; `Monitor_Filtering()` (once implemented) returns `True`.
- **FAIL:** De-assertion delay does not match Tau value; TPMI write has no effect; `Monitor_Filtering()` stub -- test cannot be executed until implemented.

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Read TPMI Thermal Monitor Filtering register | TPMI MMIO |
| 2 | Test script | Trigger thermal event (prochot inject) | MMIO override |
| 3 | PCode | Assert thermal monitor; start filter timer | Internal |
| 4 | Test script | Clear thermal event; start measurement timer | MMIO |
| 5 | PCode | Count down Tau-derived filter time | Internal |
| 6 | Test script | Poll de-assertion; measure delay | namednodes polling |
| 7 | Test script | Compare measured delay to `2^Tau * 0.977ms` | Python math |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Script | tpmi_get_set_state_mmio | read THERMAL_MGMT TPMI | TPMI MMIO |
| 2 | Script | opc_thermal_monitor | read Tau field | namednodes |
| 3 | Script | global_prochot_hw_inject | set=1 | MMIO |
| 4 | PCode | thermal monitor filter | start Tau countdown | Internal |
| 5 | Script | global_prochot_hw_inject | set=0 | MMIO |
| 6 | Script | thermal_monitor_status polling | measure de-assertion | namednodes |
| 7 | Script | math | compare to 2^Tau * 0.977ms | Python |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `imh0.punit.ptpcfsms.ptpcfsms.opc_thermal_monitor` | Tau field (bits per HAS) | Must control filter time constant |
| TPMI `THERMAL_MGMT` feature | ThermalMonitorFiltering | Read matches opc_thermal_monitor; write accepted |
| De-assertion delay | measured via polling | Must match `2^Tau * 0.977ms` within tolerance |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| `Monitor_Filtering()` is a stub -- TC cannot be fully executed | High | Critical | **File gap with script owner**: implement `Monitor_Filtering()` in `pmt_dataintegrity.py` before silicon test |
| TPMI `THERMAL_MGMT` feature name may differ in NWP TPMI structure files | Medium | High | Check `tpmi_structure_dmr0_file` for NWP thermal feature name |
| Sub-ms timing measurement via Python polling may not be accurate enough | Medium | Medium | Use SVOS timestamping or hardware timer for precise delay measurement |

---

## Section F: Recommendations

1. **Critical:** `Monitor_Filtering()` function body is a stub -- must be implemented before TC can run. Implement: read Tau, trigger event, measure de-assertion delay, compare to formula.
2. Contact script owner (Thermal team, `PMT_Thermals.py`) to complete `Monitor_Filtering()` implementation.
3. Verify TPMI feature name `THERMAL_MGMT` in NWP TPMI structure CSV files.
4. **Current partial invocation:** `runPmx.py -x nwp.xml -p PMT_Thermals -tM 60 -M 5` (runs thermal_status path; Monitor_Filtering stub will not execute meaningful validation)

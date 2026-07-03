# TC 22022421576: [TPMI/PMT] Verify Package Temperature PMT Register

**TCD:** 22022420612 -- [SoC Thermal Management] TPMI/PMT
**TPF:** 16030767555 -- [NWP PM] PMT
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/Active_PM/Thermal_Management/CPU_Thermal_Management/PMT_Thermals.py` -- `PMT.package_temp(s, self.log)`
**Library:** `pmt_dataintegrity.package_temp(socket)` -- `get_package_temp_values()` for CBB/Uncore/IMH checks
**Run via PMX:** `runPmx.py -x dmr.xml -p PMT_Thermals -tM 60 -M 5`

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- DMR: 4 CBBs, 2 IMH dies. **NWP: 2 CBBs (cbb0, cbb1), 1 IMH (imh0)**.
- `package_temp()` runs 3 injection scenarios: Core, Uncore (SOC), IMH -- all valid on NWP.
- `Clear_Core()`, `Clear_SOC()`, `Clear_IMH()` injection paths should work on NWP with 2-CBB topology.
- `get_package_temp_values()` reads register, MSR, mailbox -- verify all 3 paths accessible on NWP.

### Test Case Intent
Verify that the **Package Temperature PMT register** correctly reflects the maximum die temperature across all thermal domains. The test:
1. Clears DTS to 40°C baseline
2. Injects elevated temperature separately into Core, Uncore (SoC), and IMH domains
3. After each injection reads `package_temperature` via: (a) MMIO register, (b) MSR, (c) DFX mailbox
4. Confirms all three readout paths return the same temperature value

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP silicon/emulation; PythonSV initialized |
| 2 | DTS injection | `injection.Clear_Core()`, `Clear_SOC()`, `Clear_IMH()` functional |
| 3 | Package temp register | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature` readable |
| 4 | DFX mailbox | `imh0.oobmsm.oobmsm0.oobmsm_reg.dfx_mailbox` accessible |
| 5 | MSR access | MSR 0x1A1 (or equivalent) readable via `pstatesDebug.debug.access_to_msr()` |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Clear all DTS to baseline: `injection.Clear_All_DTS(40)` | All thermal sensors at ~40°C; no throttling active | DTS not clearing -- injection override stuck; check simics/silicon path |
| 2 | **Core injection:** `injection.Clear_Core(random.randint(40, 105))` then `cbb_values = get_package_temp_values(socket)` | Register, MSR, and mailbox all reflect elevated Core temperature; `cbb_values[-1] == "Pass"` | "Fail" in cbb_values -- Core temperature not propagating to PMT package_temp |
| 3 | Reset Core injection: `injection.Clear_Core(40, external=True)` | Package temperature returns to baseline | Temperature not clearing -- stuck injection |
| 4 | **Uncore injection:** `injection.Clear_SOC(random.randint(40, 105))` then `get_package_temp_values(socket)` | Uncore elevated temperature reflected in register, MSR, mailbox; `uncore_values[-1] == "Pass"` | Mismatch -- Uncore temperature not propagating to PMT |
| 5 | Reset Uncore injection: `injection.Clear_SOC(40, external=True)` | Package temperature returns to baseline | Temperature not clearing |
| 6 | **IMH injection:** `injection.Clear_IMH(random.randint(40, 105))` then `get_package_temp_values(socket)` | IMH elevated temperature reflected in all 3 readout paths; `imh_values[-1] == "Pass"` | Mismatch -- IMH temperature not propagating to PMT |
| 7 | Reset IMH injection: `injection.Clear_IMH(40, external=True)` | All temperatures return to baseline | Stuck injection |
| 8 | Log 3 tables: CBB table, Uncore table, IMH table; verify all rows show "Pass" | tabulate output shows: Register Value == MSR Value == Mailbox Value for each check | Any "Fail" row -- data consistency issue between PMT readout paths |

### Pass / Fail Criteria

- **PASS:** All 3 injection scenarios (Core, Uncore, IMH) produce consistent Package Temperature across register, MSR, and DFX mailbox readouts; `package_temp()` returns `True`.
- **FAIL:** Any mismatch in the 3 readout paths; `package_temp()` returns `False`; `self.print_and_exit` called with "Package Temperature PMT Register Fail".

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Inject temperature via Clear_Core/SOC/IMH | DTS override |
| 2 | PCode | Update package_temperature register | Internal |
| 3 | Test script | Read via MMIO register | namednodes |
| 4 | Test script | Read via MSR | pstatesDebug |
| 5 | Test script | Read via DFX mailbox | DFX mailbox (PMSB) |
| 6 | Test script | Compare all 3 values via tabulate | Python |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Thermal_DTS | DTS sensors | inject temperature | DTS override |
| 2 | PCode | package_temperature MMIO | update | IO register |
| 3 | Script | imh0.punit.ptpcioregs.package_temperature | read | namednodes |
| 4 | Script | MSR via pstatesDebug | read | MSR |
| 5 | Script | dfx_mailbox | read via opcode | DFX mailbox |
| 6 | Script | tabulate | compare & classify | Python |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `imh0.punit.ptpcioregs.ptpcioregs.package_temperature` | full | Must equal MSR and mailbox readings |
| MSR 0x1A1 (via pstatesDebug) | thermal status | Must reflect injected temperature |
| DFX mailbox (package temp opcode) | bits for package temp | Must equal register reading |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| `get_package_temp_values()` has DMR-specific mailbox opcodes for CBB1/CBB2/CBB3 | Medium | Medium | Verify opcode `0x000b020010810908` (CBB1 PCS) is valid on NWP; remove CBB2/CBB3 mailbox reads |
| IMH injection `Clear_IMH()` path differs on NWP (1 IMH vs 2) | Low | Low | NWP has imh0 only; `Clear_IMH()` should use imh0 path |

---

## Section F: Recommendations

1. Verify 3 temperature readout paths (MMIO, MSR, mailbox) on NWP before full run.
2. Adapt `get_package_temp_values()` to use only CBB0, CBB1 mailbox opcodes (remove CBB2, CBB3).
3. **NWP invocation:** `python runPmx.py -x nwp.xml -p PMT_Thermals -tM 60 -M 5`

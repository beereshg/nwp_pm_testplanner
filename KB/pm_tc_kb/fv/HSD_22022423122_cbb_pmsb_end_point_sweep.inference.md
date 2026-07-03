# TC 22022423122: CBB PMSB end point sweep

**TCD:** 22022421311 -- EndPoint Sweep
**TPF:** 22022562325 -- PM Integration Testing
**Val Environment:** silicon, virtual_platform
**Primary Script:** `pm/SB_Harasser/sb_harasser_DMR.py` -- `run_acode_harasser()` with `pmsb=1, gpsb=0`
**Endpoint DB:** `pm/SB_Harasser/cbb_sb_portID.xlsx` (column: `local PorIDs`)

---

## Section A: NWP Delta

**NWP Adaptation Notes:**
- DMR supports CBB0-CBB3 (`die_id=[0,1,2,3]`). **NWP has 2 CBBs only** -- use `die_id=[0,1]`.
- `die_id_map` in `sb_harasser_DMR.py`: `{0:'cbb0', 1:'cbb1'}` -- both valid for NWP.
- PkgC6 is **ZBB** on NWP -- any PC6 assertions must be removed; assert PC6 is NOT entered.
- Skip port IDs remain: `skip_port_ids = [61, 62, 64]` (hardcoded in script).
- CBB PMSB endpoint list comes from `cbb_sb_portID.xlsx` -- verify NWP-specific port IDs are included.

### Test Case Intent
Systematically sweep all registered **PMSB (Power Management Sideband)** endpoints on the CBB (Compute Building Block) die(s). For each endpoint in `cbb_sb_portID.xlsx`, issue a PMSB read (and optionally write/RMW) transaction via the ACODE harasser path. The test verifies that every CBB PMSB endpoint:
1. Is reachable (no timeout, no NAK/unreachable response)
2. Returns a valid response within the sideband transaction timeout
3. Produces no MCA, soft-hang, or NLOG error on access
4. Returns read-back data consistent with written values (write-readback mode)

The sweep is scoped to PMSB only (`pmsb=1, gpsb=0`); GPSB is covered by TC 22022423121.

### Pre-Conditions

| # | Item | Requirement |
|---|------|-------------|
| 1 | Platform | NWP silicon or emulation booted to SVOS; PythonSV initialized |
| 2 | CBB count | Confirm 2 CBBs active: `sv.socket0.cbbs.target_info` lists cbb0, cbb1 |
| 3 | Endpoint file | `pm/SB_Harasser/cbb_sb_portID.xlsx` present with NWP-validated port IDs |
| 4 | Skip list | `skip_port_ids = [61, 62, 64]` confirmed correct for NWP |
| 5 | SAI policy | `sv.socket0.imhs.pcodeio_map.io_msg_sai_policy_check_disable` -- set if needed to allow harasser traffic |
| 6 | MCA baseline | Read `sv.sockets.cbbs.computes.module0.ml2_cr_mc3_status.uc` = 0 before start |
| 7 | NLOG clean | No pre-existing NLOG errors at harasser start |
| 8 | PkgC6 ZBB | Confirm NWP PkgC6 never entered during test (`pc6_entry_count` stays 0) |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | **Load script:** `import diamondrapids.pm.SB_Harasser.sb_harasser_DMR as hr` | Import succeeds; `cbb_sb_portID.xlsx` loaded into `df_cbb`; endpoint DataFrame populated | ImportError or FileNotFoundError -- check path and Excel engine (`openpyxl`) |
| 2 | **Verify endpoint count:** `df = pd.read_excel(cbb_xls_path); df.set_index('local PorIDs'); print(len(df))` | >= 20 CBB PMSB endpoints (PUnit, CorePM, FIVR0/1, PMA, RAPL, thermal, CCF); NWP port IDs validated | Zero or unexpectedly low count -- missing NWP entries in xlsx |
| 3 | **Baseline MCA check:** `ok, detail = hr.check_mca_errors(socket=0)` | Returns `(False, {})` -- no MCA errors before sweep | Pre-existing MCA: log details, abort, flag as pre-condition failure |
| 4 | **CBB0 PMSB read sweep:** `result = hr.run_acode_harasser(socket=0, die_id=[0], pmsb=1, gpsb=0, acode_operation=0, acode_operation_type=0)` | All CBB0 PMSB endpoints iterated from `df_cbb`; no NAK/timeout; `error_detected=False`; `result["acode"] > 0` | `error_detected=True` -- PMSB endpoint returned error; log port ID and row data |
| 5 | **CBB1 PMSB read sweep:** `result = hr.run_acode_harasser(socket=0, die_id=[1], pmsb=1, gpsb=0, acode_operation=0, acode_operation_type=0)` | All CBB1 PMSB endpoints respond; `result["acode"] > 0` | Same as step 4 -- log failing port ID |
| 6 | **MCA check after read sweep:** `ok, detail = hr.check_mca_errors(socket=0)` | `ok == False` -- no MCA errors after PMSB read sweep across both CBBs | MCA detected -- capture `pmas.pmsb.io_spare0`, dump NLOG |
| 7 | **Write-readback sweep:** `result = hr.run_acode_harasser(socket=0, die_id=[0,1], pmsb=1, gpsb=0, acode_operation=2, acode_operation_type=1)` | Configurable PMSB registers accept write; read-back matches written value; no bus error | Mismatch between written and read-back -- PMSB write path broken or register is read-only |
| 8 | **NLOG scan for sideband timeouts:** examine SVOS NLOG for `PMSB_TIMEOUT` or `SB_TIMEOUT` | Zero sideband timeout entries in NLOG for duration of sweep | Timeout entry -- PMSB endpoint unreachable; record port ID and IP name |
| 9 | **Stop harasser and verify:** `hr.stop_harasser()` then read `sv.socket0.cbbs.computes.pmas.pmsb.io_spare0` | io_spare0 = 0 after stop -- confirms harasser stopped cleanly | Non-zero value -- call `stop_harasser()` manually; check for stuck harasser |
| 10 | **Optional loop stability:** `hr.run_harasser_loop(socket=0, die_id=[0,1], pmsb=1, gpsb=0, acode=1, pcode=0, ocode=0, interval=30, t_time=300)` | 5-minute PMSB sweep loop completes; no hang/MCA/timeout; endpoint coverage increases each iteration | Hang or MCA during loop -- capture timestamp, last port ID, NLOG snapshot |

### Pass / Fail Criteria

- **PASS:** All CBB PMSB endpoints in `cbb_sb_portID.xlsx` accessed successfully on both CBB0 and CBB1; no NAK, no timeout, no MCA, no NLOG error; write-readback matches; `check_mca_errors()` returns `(False, {})`.
- **FAIL:** Any of: PMSB endpoint returns NAK or timeout; `error_detected=True`; MCA detected; NLOG contains `PMSB_TIMEOUT`; write-readback mismatch; CBB PMSB stops responding mid-sweep.

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Load `cbb_sb_portID.xlsx`; build endpoint iterator (`df_cbb.iterrows()`) | Python / pandas |
| 2 | Test script | Call `run_acode_harasser(die_id=[0], pmsb=1, gpsb=0)` | PythonSV namednodes |
| 3 | ACODE harasser | Issue PMSB read to each `local PorID` in DataFrame | CBB PMSB fabric |
| 4 | CBB PUnit/FIVR/CorePM/PMA | Respond to PMSB read; return register data | CBB PMSB sideband |
| 5 | ACODE harasser | Log response; check NAK/timeout; increment `covered_endpoints` | Internal harasser loop |
| 6 | Test script | Call `check_mca_errors()` after each CBB sweep | PythonSV / MCA MSRs |
| 7 | Test script | Run RMW sweep (`acode_operation=2`), verify read-back | CBB PMSB |
| 8 | Test script | Call `stop_harasser()`; verify `io_spare0 = 0` | PMSB spare register |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Script | `df_cbb` | `iterrows()` -- iterate CBB PMSB port IDs | pandas DataFrame |
| 2 | ACODE harasser | CBB PMSB fabric | NonPosted read (op=0) to `local PorID` | PMSB sideband |
| 3 | CBB endpoint (PUnit/FIVR/CorePM) | ACODE harasser | Response data, no error flag | PMSB response |
| 4 | Script | `check_mca_errors()` | Poll `ml2_cr_mc3_status.uc` across both CBBs | MSR / namednodes |
| 5 | ACODE harasser | CBB PMSB fabric | Posted RMW (op=2, type=1) to configurable registers | PMSB sideband |
| 6 | CBB endpoint | ACODE harasser | Read-back confirms write | PMSB response |
| 7 | Script | `stop_harasser()` | Write 0 to `cbbs.computes.pmas.pmsb.io_spare0` | namednodes |

---

## Section C: Coverage

| Dimension | Coverage |
|-----------|---------|
| **CBBs covered** | CBB0, CBB1 (NWP; DMR adds CBB2/3) |
| **Bus type** | PMSB only (`pmsb=1, gpsb=0`) |
| **Operation types** | Read (op=0, NonPosted), RMW (op=2, Posted) |
| **IPs swept** | PUnit, FIVR0/FIVR1, CorePM, PMA, RAPL unit, thermal sensors, CCF PM regs |
| **Error detection** | NAK/timeout detection, MCA check, NLOG scan, write-readback |
| **Skipped ports** | `[61, 62, 64]` -- reserved/unsafe for harasser access |

---

## Section D: Spec Refs

| Register / Log | Field / Offset | Pass/Fail Criteria |
|----------------|---------------|-------------------|
| `sv.socket0.cbbs.computes.module0.ml2_cr_mc3_status.uc` | bit 0 Uncorrectable Error | Must remain 0 throughout |
| `sv.socket0.cbbs.computes.pmas.pmsb.io_spare0` | full register | Must be 0 after `stop_harasser()` |
| `sv.socket0.cbbs.base.punit.pc6_entry_count` | full register | Must remain 0 (PkgC6 ZBB on NWP) |
| NLOG CBB | `PMSB_TIMEOUT`, `SB_TIMEOUT`, error-level events | Zero occurrences |
| `cbb_sb_portID.xlsx` | `local PorIDs` column | All entries iterated; `covered_endpoints > 0` |

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| `cbb_sb_portID.xlsx` may contain DMR-only port IDs not valid on NWP | Medium | High | Cross-check port IDs against NWP CBB PMSB HAS; add NWP-specific entries if missing |
| NWP `die_id=[2]` or `[3]` will KeyError or access wrong CBB | Low | Medium | Hardcode `die_id=[0,1]` for NWP; add guard assertion |
| Posted write may trigger unexpected PMSB response on some NWP endpoints | Medium | Medium | Start with read-only (`acode_operation=0`) first; add write only after read sweep passes |
| `check_mca_errors()` polls `compute0.module0` only -- may miss CBB1 errors | Low | Medium | Explicitly call for both CBBs; extend to `sv.sockets.cbbs` |
| SAI policy check may block harasser traffic if not disabled | Low | High | Set `io_msg_sai_policy_check_disable.cmp_cmpd_sai_check_disable = 1` as precondition |

---

## Section F: Recommendations

1. **NWP port:** Change `die_id=[0,1,2,3]` to `die_id=[0,1]` -- NWP has exactly 2 CBBs.
2. **Validate xlsx:** Print all port IDs and cross-check against NWP CBB PMSB HAS before silicon run.
3. **Read-before-write:** Always run read sweep (`acode_operation=0`) first, then proceed to RMW (`acode_operation=2`).
4. **Extend MCA scope:** Call `check_mca_errors()` explicitly for both `cbb0` and `cbb1`.
5. **PkgC6 guard:** Add `assert int(sv.socket0.cbbs.base.punit.pc6_entry_count) == 0` before and after sweep.
6. **NWP invocation:**
   ```python
   import diamondrapids.pm.SB_Harasser.sb_harasser_DMR as hr
   # CBB PMSB sweep -- NWP 2-CBB
   result = hr.run_harasser(socket=0, die_id=[0,1], pmsb=1, gpsb=0,
                             pcode=0, ocode=0, acode=1,
                             acode_operation=0, acode_operation_type=0)
   print(f"ACODE endpoints covered: {result['acode']}")
   ok, detail = hr.check_mca_errors(socket=0)
   assert not ok, f"MCA detected: {detail}"
   ```

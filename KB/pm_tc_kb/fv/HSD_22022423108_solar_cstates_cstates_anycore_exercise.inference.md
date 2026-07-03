## Test Case Intent

Standard Solar C-state stress / verification test. Mode: **Exercise**. Systematic all-core scope. Exercises **supported** CC6 MWAIT sub-states only: 0x0=CC6A, 0x3=CC6S, 0x4=CC6S-P. (0x0=CC6A autonomous, 0x3=CC6S supervised, 0x4=CC6S-P power-gate) CC6 FailTolerance=0/10 — zero tolerance: all CC6 entries must succeed. **On NWP**: PkgC6 is ZBB — residency must remain 0 throughout. **Reference XML**: `Focus_Testing/Cstates_anycore_exercise.xml`

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or virtual platform; SVOS booted with C-states enabled |
| Solar framework | Installed at `/usr/bin/solar/`; XML config present at `Focus_Testing/Cstates_anycore_exercise.xml` |
| C-states | CC6A, CC6S, CC6S-P enabled in BIOS (`C6Enable=1`) |
| PythonSV | `sv.socket0.*` accessible for post-run register inspection |
| NWP constraint | PkgC6 is ZBB — Solar scope must NOT include PkgC6 |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|--------------------|
| 1 | Boot platform to SVOS; verify no pending MCA. | Clean S0, no MCA in NLOG. | MCA or boot hang. |
| 2 | Run Solar: `/usr/bin/solar/solar.sh /cfg /usr/lib/python3/dist-packages/diamondrapids/pm/Solar/Focus_Testing/Cstates_anycore_exercise.xml /logpath . /log_ip_disables` | Solar exits; all CC6 entries succeed (FaultTol=0). | Solar hangs, crash, or kernel panic. |
| 3 | [Exercise mode] Solar stress-cycles CC6 entry/exit on all cores in scope. | No hang during rapid CC6 entry/exit cycles. | Solar FAIL logged or system hang. |
| 4 | Post-run: read core C6 residency counters (all 96 cores, 2 CBBs). | Residency advanced on cores that attempted CC6. | Residency stuck at 0 on all cores. |
| 5 | Verify PkgC6 residency = 0 (ZBB). | IA32_PKG_C6_RESIDENCY (0x3F9) = 0. | PkgC6 > 0. |

### Health Checks

| Register / Log | Access | Pass Criterion |
|----------------|--------|----------------|
| Solar log | Solar output file | No HANG/CRASH; CC6 PASS/FAIL ratio within tolerance. |
| Core C6 residency | `sv.socket0.cbb{0,1}.compute0.module0.core{k}.msr.ia32_c6_residency.read()` | Non-zero after Solar run. |
| PkgC6 residency | `sv.socket0.uncore.msr.ia32_pkg_c6_residency.read()` | Must be 0 (ZBB). |
| NLOG | `nlog -t MCA` | No FATAL entries. |

### Pass / Fail Criteria

**PASS**: Solar completes; CC6 failures ≤ 0/10; core C6 residency advanced on exercised cores; PkgC6 = 0; no MCA/hang.

**FAIL**: Solar hang or crash; CC6 failures > 0/10; PkgC6 > 0; MCA or IERR.

### References

- [Core C-States HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- Solar Framework documentation: `solar.sh --help`
- Solar XML: `Focus_Testing/Cstates_anycore_exercise.xml`
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423108
- NWP TP: https://hsdes.intel.com/appstore/article-one/#/15019478558
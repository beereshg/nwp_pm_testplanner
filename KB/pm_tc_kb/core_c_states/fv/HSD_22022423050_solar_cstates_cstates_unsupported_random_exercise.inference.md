## Test Case Intent

**Negative / graceful-degradation test.** Solar exercises ALL MWAIT C-state hint encodings (via `AllMwaitReq` knob) including encodings that map to **unsupported** C-states on NWP. Mode: **Exercise**. Random core scope selection. CC6 sub-states exercised: 0x0=CC6A, 0x1=CC6S-1, 0x2=CC6S-2, 0x3=CC6S, 0x4=CC6S-P, 0x5=CC6S-P2. Fault tolerance CC6=10/10 cycles — CC6 **not** entering is the expected outcome for unsupported MWAIT encodings. **Pass criteria**: no hang, no MCA, no system reset regardless of CC6 entry result. **On NWP**: PkgC6 is ZBB — any MWAIT hint requesting PkgC6 must be rejected gracefully. **Reference XML**: `SOLAR_DMR_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_random_exercise.xml`

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or virtual platform; SVOS booted with C-states enabled |
| Solar framework | Installed at `/usr/bin/solar/`; XML config present at `SOLAR_DMR_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_random_exercise.xml` |
| C-states | CC6A, CC6S, CC6S-P enabled in BIOS (`C6Enable=1`) |
| PythonSV | `sv.socket0.*` accessible for post-run register inspection |
| NWP constraint | PkgC6 is ZBB — Solar scope must NOT include PkgC6 |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|--------------------|
| 1 | Boot platform to SVOS; verify no pending MCA before test. | Clean S0 with no MCA errors in NLOG. | Any MCA or IERR during boot. |
| 2 | Run Solar with AllMwaitReq knob: `/usr/bin/solar/solar.sh /cfg /usr/lib/python3/dist-packages/diamondrapids/pm/Solar/SOLAR_DMR_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_random_exercise.xml /logpath . /log_ip_disables` | Solar exits with PASS or FAIL-CC6 (CC6 entry failure is tolerated, fault tolerance=10). | Solar hangs, segfault, kernel panic, or system reset. |
| 3 | [Exercise mode] Solar stress-cycles through all MWAIT encodings without per-state verification. | All MWAIT encodings attempted without hang. | Any hang or crash during MWAIT attempts. |
| 4 | Post-run: read NLOG and PM error counters. | No uncorrected MCA, no NLOG FATAL entries. | Any FATAL in NLOG; MCA_STATUS non-zero. |
| 5 | Verify PkgC6 residency stays 0 (ZBB invariant). | IA32_PKG_C6_RESIDENCY (MSR 0x3F9) = 0. | PkgC6 residency > 0 (ZBB violation). |

### Health Checks

| Register / Log | Access | Pass Criterion |
|----------------|--------|----------------|
| Solar log output | `grep -iE 'FAIL|ERROR|HANG|CRASH' solar.log` | No HANG/CRASH lines; CC6 FAIL is tolerated. |
| NLOG errors | `nlog -t MCA` | No FATAL entries. |
| PkgC6 residency | `sv.socket0.uncore.msr.ia32_pkg_c6_residency.read()` | Must be 0 (ZBB). |
| CC6 entry status | Solar log CC6 pass/fail count | CC6 failures ≤ 10/10 tolerated. |

### Pass / Fail Criteria

**PASS**: Solar completes without hang/MCA/reset; CC6 entry failures ≤ 10 out of 10 cycles; PkgC6 residency = 0; no NLOG FATAL entries.

**FAIL**: System hang, MCA, IERR, or reset; CC6 failures > 10/10; PkgC6 residency > 0 (ZBB violation); or Solar process crash.

### References

- [Core C-States HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- Solar Framework documentation: `solar.sh --help`
- Solar XML: `SOLAR_DMR_XMLS/Exercise/CSTATES/Cstates_unsupported_Mwait_random_exercise.xml`
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423050
- NWP TP: https://hsdes.intel.com/appstore/article-one/#/15019478558
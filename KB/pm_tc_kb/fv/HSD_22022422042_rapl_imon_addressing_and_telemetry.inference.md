# TC: RAPL IMON Addressing and Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422042](https://hsdes.intel.com/appstore/article-one/#/22022422042) |
| **Title** | RAPL IMON Addressing and Telemetry |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL — SVID IMON Telemetry |
| **Sub-Feature** | SVID IMON addressing (ADDR_CONFIG, IFC_CONFIG, IMON_MASK) and telemetry accuracy |
| **Parent TCD** | [22022420826 — Socket RAPL SVID Reporting Verification](https://hsdes.intel.com/appstore/article-one/#/22022420826) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **Owner** | mps |
| **Val Framework** | os-svos, python-sv |

---

## Test Case Intent

Validates the **SVID IMON addressing and telemetry accuracy** scenario defined in [TCD 22022420826 — Socket RAPL SVID Reporting Verification](https://hsdes.intel.com/appstore/article-one/#/22022420826) §5 ("IMON values in expected range; TPMI ENERGY_STATUS consistent with IMON-derived power estimate"). Environment: NWP post-silicon (SVOS).

**Micro-architecture:** PrimeCode on the NIO die is the SVID master, managing up to 2 external SVID buses with max 16 logical VRs. SVID carries IMON (current monitor) telemetry from the VR back to PrimeCode, which computes P = V × I to derive socket power for the NN-PID RAPL loop. This TC validates three aspects: (1) SVID addressing — `SVID_ADDR_CONFIG[0:15]` maps logical VR IDs to correct physical bus addresses matching the NWP platform BOM, (2) SVID interface configuration — `SVID_IFC_CONFIG` matches NWP platform (2-rail topology), (3) telemetry accuracy — IMON-derived power at TDP load correlates with `TPMI ENERGY_STATUS` within tolerance.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon, SVOS |
| Sockets | 1S minimum |
| BIOS knobs | Default SVID and RAPL configuration; TPMI unlocked |
| OS / Driver | Ubuntu/SVOS; PTU available |
| PythonSV | `pm.pmutils.cpu_rapl` module; SVID register access via namednodes |
| Feature state | Socket RAPL enabled; SVID bus operational (VR present) |
| NWP topology | Single NIO die as SVID master; 2 CBBs; VCCIN VR as primary rail |
| Interface | SVID registers via PythonSV; TPMI for ENERGY_STATUS |
| Platform BOM | NWP VR SVID addresses known from platform documentation |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read `SVID_ADDR_CONFIG[0:15]` via PythonSV: `sv.socket0.nio.punit.svid_addr_config.read()` (per VR ID) | Each VR ID has: Valid bit set for present VRs; `VR_ADDR[3:0]` matches NWP platform BOM physical addresses; `SVID_Bus_ID[1:0]` correct | VR address mismatch vs BOM; invalid addresses for present VRs |
| 2 | Read `SVID_IFC_CONFIG`: `sv.socket0.nio.punit.svid_ifc_config.read()` | Interface configuration matches NWP platform (2-rail SVID topology; correct clock speed) | Wrong interface mode; unexpected rail count |
| 3 | Read `SVID_IMON_MASK`: `sv.socket0.nio.punit.svid_imon_mask.read()` | IMON telemetry enabled for VCCIN rail(s); relevant bits set for all power monitoring VRs | IMON disabled for VCCIN; missing VR mask bits |
| 4 | Verify SVID VR enumeration: read VRCI CAPABILITY register per VR | All expected VRs report as present; capability fields match VR datasheet | Missing VR; capability mismatch |
| 5 | Record system at idle; read IMON telemetry via SVID VR status registers | IMON reading is low (idle current); non-zero (link functional) | IMON = 0 at idle (SVID link dead) or unexpectedly high |
| 6 | Read `TPMI ENERGY_STATUS` at idle: `sv.socket0.nio.punit.tpmi.energy_status.read()` | Energy counter incrementing at idle power rate | Counter stale or not incrementing |
| 7 | Start PTU TDP workload: `./ptu -ct 3` across all 96 cores | All cores loaded; socket power rises to TDP level | PTU fails; insufficient load |
| 8 | Read IMON telemetry under TDP load | IMON reading is high; consistent with TDP-level current draw | IMON too low or stuck at idle value |
| 9 | Compute RAPL-derived average power: read `TPMI ENERGY_STATUS` at t1 and t2 (5 s apart); compute `power = Δenergy × energy_unit / Δtime` | Computed power approximately equals TDP (±10%) | Power far from TDP; energy counter not tracking load |
| 10 | Cross-check IMON-derived power vs RAPL energy-derived power | IMON-derived power agrees with RAPL energy power within ±5% | Mismatch > 5% — indicates IMON calibration or addressing error |
| 11 | Stop workload; verify IMON drops to idle levels | IMON reading returns to idle current; ENERGY_STATUS accumulation rate drops | IMON stuck high; energy rate unchanged |
| 12 | Verify `SVID_POLL_PRIORITY_CONFIG` | Status polling priority includes IMON VRs; polling active | IMON VRs not in poll priority |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022420826](https://hsdes.intel.com/appstore/article-one/#/22022420826) §5: IMON values in expected range; TPMI ENERGY_STATUS consistent with IMON-derived power estimate.

**PASS** when ALL of the following are true:
- `SVID_ADDR_CONFIG` maps VR IDs to correct physical SVID addresses per NWP platform BOM
- `SVID_IFC_CONFIG` matches NWP SVID interface (2-rail)
- `SVID_IMON_MASK` enables IMON for all relevant power monitoring VRs
- IMON telemetry at idle: low current (functional link, non-zero)
- IMON telemetry at TDP: high current consistent with TDP draw
- RAPL energy-derived power at TDP: within ±10% of expected TDP
- IMON-derived power vs RAPL energy-derived power: agreement within ±5%
- No MCAs, dmesg errors, or system hangs

**FAIL** when ANY of the following are true:
- SVID address mismatch vs NWP platform BOM
- IMON stuck at zero or stuck at max under varying workload
- RAPL energy-derived power disagrees with IMON-derived power by > 5%
- Energy counter not tracking workload changes
- System hang, MCA, or SVID bus error

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| `SVID_ADDR_CONFIG` | `sv.socket0.nio.punit.svid_addr_config.read()` | Valid bits set for present VRs; addresses match BOM |
| `SVID_IFC_CONFIG` | `sv.socket0.nio.punit.svid_ifc_config.read()` | Correct interface configuration |
| `SVID_IMON_MASK` | `sv.socket0.nio.punit.svid_imon_mask.read()` | IMON enabled for VCCIN rails |
| `TPMI ENERGY_STATUS` (idx=7) | `sv.socket0.nio.punit.tpmi.energy_status.read()` | Counter incrementing; tracks workload |
| `TPMI PL_INFO` (idx=9) | `sv.socket0.nio.punit.tpmi.pl_info.read()` | MAX_PL1 = TDP (reference for power validation) |
| `dmesg` | `dmesg \| grep -i 'mca\|error\|svid\|rapl'` | No unexpected errors |

### Post-Process

N/A — SVID register reads and RAPL energy cross-check captured inline by PythonSV.

### References

- [TCD 22022420826 — Socket RAPL SVID Reporting Verification](https://hsdes.intel.com/appstore/article-one/#/22022420826)
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) — IMON telemetry role in NN-PID
- [SVID KB — svid.md](../../pm_features/power_rapl/svid.md) — SVID bus architecture, ADDR_CONFIG, IMON_MASK
- [NWP PM MAS — SVID](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Intel RAPL HAS — IMON / SVID telemetry](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html)

---

## NWP Adaptation Notes

| DMR | NWP |
|-----|-----|
| `dmr.xml` | `nwp.xml` |
| Dual IMH SVID masters (DMR-AP) | **Single NIO** SVID master |
| `sv.socket0.imh0.punit.svid_*` | `sv.socket0.nio.punit.svid_*` |
| 4 CBBs, dual VCCIN (AP) | 2 CBBs, single VCCIN |
| Safe WP change request | **Not POR on NWP** — skip |

**Disposition: Runnable_On_N-1** — Change XML config and register path prefix. NWP single-NIO simplifies SVID topology. SVID IMON addressing must be verified against NWP platform BOM (different VR physical addresses than DMR).

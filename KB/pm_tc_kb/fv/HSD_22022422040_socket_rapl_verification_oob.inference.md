# TC Description: Socket RAPL Verification - OOB

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422040](https://hsdes.intel.com/appstore/article-one/#/22022422040) |
| **Title** | Socket Rapl verification - OOB |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | OOB access path — PECI-over-MCTP / OOBMSM consistency with inband TPMI |
| **Parent TCD** | [22022420821 -- Socket RAPL Registers Verification - CSR and TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **OOB Access Path** scenario defined in [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) §5-D: "OOB register reads via PECI-over-MCTP/OOBMSM are consistent with inband TPMI reads for all Socket RAPL registers." BMC/NM accesses Socket RAPL TPMI registers via OOBMSM/PECI-over-MCTP. This TC reads all Socket RAPL TPMI registers via both inband (PythonSV) and OOB paths, verifies value consistency, and tests OOB write capability including PLR source attribution (OOB writes should set PLR bit[12] = PKG_PL1_OOB).

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system with BMC/OOBMSM connectivity |
| OS / Driver | SVOS with PythonSV; BMC Redfish/PECI tools available |
| BIOS | Default RAPL settings |
| Feature state | RAPL active; OOB/PECI path functional (BMC connected) |
| Starting state | System booted; OOBMSM initialized; Socket RAPL TPMI registers accessible |
| TPMI base path | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.* (inband) |
| OOB path | BMC -> PECI-over-MCTP -> NIO PCode -> TPMI |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Inband read all 8 Socket RAPL TPMI registers via PythonSV: domain_header, energy_status, perf_status, pl1_control, pl2_control, pl4_control, pl_info, power_unit. Record all values. | All 8 registers readable. Values non-zero where expected (energy_status progressing, pl_info populated). | Any register read failure. |
| 2 | OOB read the same 8 registers via PECI-over-MCTP/OOBMSM (using BMC tooling or pd.debug.tpmi_oob_read). Record all values. | All 8 registers readable via OOB. | OOB read failure or timeout. |
| 3 | Compare inband vs OOB values for each register. Allow small delta for energy_status (counter progresses between reads). | All static registers match exactly (pl_info, power_unit, domain_header, pl1_control, pl2_control, pl4_control). Energy_status and perf_status within timing tolerance. | Any static register mismatch between inband and OOB. |
| 4 | Verify domain_header: check capability bits, instance count, and RAPL domain ID. | domain_header reports valid Socket RAPL domain with correct capabilities for NWP. | Invalid domain ID or capability bits. |
| 5 | Verify power_unit via OOB: energy_unit, time_unit, power_unit fields. | Same encoding as inband. power_unit consistent with U11.3 spec. | Power unit mismatch between OOB and inband. |
| 6 | OOB write test: write a custom PL1 limit via OOB path (PECI WrIAMSREx or OOBMSM TPMI write). | OOB write accepted. PL1_CONTROL.PWR_LIM reflects new value via inband readback. | OOB write rejected or inband readback mismatch. |
| 7 | Verify PLR source attribution after OOB PL1 write: trigger throttle condition with the OOB-programmed PL1. Read PLR reason bits. | PLR bit[12] (PKG_PL1_OOB) set — identifies OOB as the PL1 source. Inband PL1 bit[10] NOT set. | Wrong PLR source bit or PLR = 0. |
| 8 | OOB write while LOCK=1: if PL1_CONTROL.LOCK is set, attempt OOB write to PL1. | OOB write rejected. PL1_CONTROL unchanged. LOCK enforcement applies to OOB path as well. | OOB bypasses LOCK — PL1 changed despite LOCK=1. |
| 9 | Restore original PL1 value. Verify no MCA or hang. | Test completes cleanly. OOB and inband paths both functional. | System instability. |

### Pass / Fail Criteria

- **PASS**: Per TCD 22022420821 §5-D — All 8 Socket RAPL TPMI registers readable via OOB. OOB values consistent with inband TPMI reads (static registers exact match; counters within timing tolerance). OOB PL1 write accepted and reflected in inband readback. PLR correctly attributes OOB source (bit[12]). LOCK enforcement applies to OOB writes. No MCA or hang.
- **FAIL**: OOB read failure. Inband/OOB register mismatch on static registers. OOB write not reflected in inband state. PLR source misattributed. OOB bypasses LOCK. System instability.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| TPMI domain_header | Inband + OOB | Exact match; valid domain ID |
| TPMI power_unit | Inband + OOB | Exact match; correct encoding |
| TPMI pl_info | Inband + OOB | Exact match; MAX_PL1/PL2/MIN_PL correct |
| TPMI pl1_control | Inband + OOB | Exact match; OOB write reflected |
| TPMI pl2_control | Inband + OOB | Exact match |
| TPMI energy_status | Inband + OOB | Within timing tolerance |
| TPMI perf_status | Inband + OOB | Within timing tolerance |
| PLR reason bits | plr_die_level | PKG_PL1_OOB (bit 12) set after OOB PL1 write |

### Post-Process

N/A

### References

- [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821)
- [Wave 3 Common HAS -- Socket RAPL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)

---

## Section A: NWP Delta

NIO replaces IMH as TPMI endpoint. OOB path: BMC -> PECI-over-MCTP -> NIO PCode -> TPMI (same architecture as DMR).

| Aspect | DMR | NWP |
|--------|-----|-----|
| TPMI base | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.* | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.* |
| OOB path | BMC -> IMH OOBMSM | BMC -> NIO OOBMSM |
| PLR OOB bit | bit[12] PKG_PL1_OOB | bit[12] PKG_PL1_OOB (unchanged) |

## Section F: Recommendations

Recommendation: ADOPT — imh0 -> nio; OOB read/write/PLR attribution validation. Priority: High — OOB register access is critical for BMC/NM power management on managed platforms.

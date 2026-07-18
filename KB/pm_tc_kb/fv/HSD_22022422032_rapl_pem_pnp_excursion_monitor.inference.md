# TC Description: RAPL PEM (PnP Excursion Monitor)

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422032](https://hsdes.intel.com/appstore/article-one/#/22022422032) |
| **Title** | RAPL PEM (PnP Excursion Monitor) |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PEM (PnP Excursion Monitor) — excursion detection and reporting |
| **Parent TCD** | [16031169448 -- Socket RAPL - Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) |
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

Validates the **PEM (PnP Excursion Monitor) excursion detection and reporting** scenario defined in [TCD 16031169448 -- Socket RAPL - Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) §5-C: "PEM registers accessible via TPMI; excursion events visible when RAPL limits exceeded; PEM events correlate with active RAPL throttling." PEM is a Pcode (CBB-scoped) feature that uses an EWMA algorithm to filter transient frequency drops and reports sustained excursions below a configurable FET (Frequency Excursion Threshold). Gen3 (DMR/NWP) supports 32 event types including per-interface PL1/PL2, FastRAPL, RACL, and RAS. This TC enables PEM, triggers RAPL excursions by reducing PL1/PL2 limits under load, and verifies PEM_STATUS bits are set correctly on both NWP CBBs, including PEM_STATUS clear (W0C) semantics.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system (2 CBBs, single NIO die) or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment; ptu or equivalent workload available |
| BIOS knobs | Socket RAPL PL1 enabled (default); PL1/PL2 limits unlocked or programmable via TPMI |
| Feature state | PEM disabled by default (PEM_CONTROL.ENABLE_PEM = 0); RAPL active at TDP |
| Tool | runPmx.py accessible; diamondrapids.pm.pmutils.cpu_rapl importable |
| Starting state | System booted to SVOS; cores active; no prior RAPL throttle condition |
| PEM registers | pem_control: sv.socket0.cbb{0,1}.base.tpmi.pem_control; pem_status: sv.socket0.cbb{0,1}.base.tpmi.pem_status |
| PEM HAS | Wave 3 Common HAS PEM_STATUS-Gen3-DMR; gen3 supports 32 events including RACL (bit 22) and RAS (bit 30) |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read PEM_HEADER (TPMI index 0) on both CBBs to confirm gen3 PEM. Check INTERFACE_VERSION field. | INTERFACE_VERSION = 1 (gen3) on both cbb0 and cbb1. | Version mismatch or register unreadable. |
| 2 | Configure PEM_CONTROL on both CBBs: set FET to a ratio below P1 but above Pm (e.g., P1 - 2), set TW to small window (e.g., TW=2 for ~9ms), set ENABLE_PEM=1. | PEM_CONTROL shows FET, TW, and ENABLE_PEM=1 on readback for both cbb0 and cbb1. | PEM_CONTROL write rejected or readback mismatch. |
| 3 | Start sustained all-core workload (ptu -ct 1) to establish baseline power near TDP. Verify cores running at P1. | Cores at P1 frequency; power draw near TDP; PEM_STATUS reads 0 (no excursion yet). | Workload fails to start or PEM_STATUS already non-zero before stimulus. |
| 4 | Set PL1 to aggressive low value via TPMI (socket_rapl_pl1_control.pwr_lim) to force RAPL PL1 throttling below FET. Wait for EWMA convergence (~2.3 x 2^TW ms + margin). | PEM_STATUS.PKG_PL1_INBAND (bit 10) set on both cbb0 and cbb1. PEM_STATUS.ANY (bit 0) also set. | PL1 PEM bit not set after convergence wait; PEM_STATUS remains 0. |
| 5 | Read PEM_STATUS on both CBBs and decode all 32 bits. Verify only RAPL-related PL1 bits are set (bit 10 for INBAND if TPMI was used). | PKG_PL1_INBAND (bit 10) set. PEM_ANY (bit 0) set. No spurious bits (thermal, PROCHOT, PMAX) unless those conditions exist. | Wrong PEM_STATUS bits set or expected bits missing. |
| 6 | Read PEM_COUNTER for event 10 (PKG_PL1_INBAND) via PMT. Verify counter is non-zero and progressing. | PEM_COUNTER[10] > 0 and incrementing (unit = 1ms). | Counter stuck at 0 or not incrementing during active excursion. |
| 7 | Clear PEM_STATUS.PKG_PL1_INBAND by writing 0 to bit 10 (W0C semantics). Read back PEM_STATUS. | Bit 10 cleared. If no other bits remain set, PEM_ANY (bit 0) also auto-clears. | Bit 10 not cleared after W0C write; PEM_ANY remains set incorrectly. |
| 8 | Verify PEM_STATUS re-asserts: since excursion is still active (PL1 still low), PEM should re-detect and set bit 10 again within one EWMA window. | PEM_STATUS.PKG_PL1_INBAND (bit 10) re-asserts after EWMA reconvergence. | Bit does not re-assert — indicates EWMA not running continuously. |
| 9 | Restore PL1 to TDP. Wait for RAPL to become unconstrained (~5 seconds). | Core frequencies recover above FET threshold. RAPL throttle ceases. | Frequency does not recover. |
| 10 | Clear PEM_STATUS (W0C all bits). Verify PEM_STATUS remains 0 after clearance since no excursion is active. | PEM_STATUS = 0 on both cbb0 and cbb1 after clear. | PEM_STATUS re-asserts despite no active excursion. |
| 11 | Trigger PL2 excursion: set PL2 low enough that burst power exceeds PL2 during active workload. Wait for PL2 timer expiry and PEM EWMA convergence. | PEM_STATUS.PKG_PL2_INBAND (bit 13) set on both CBBs. PEM_ANY (bit 0) set. | PL2 PEM bit not set after timer expiry. |
| 12 | Restore PL2 to default (1.2 x TDP). Disable PEM (PEM_CONTROL.ENABLE_PEM=0). Restore all original register values. | PEM disabled; test exits cleanly (exit code 0); no MCA or system hang. | Script error or system instability during cleanup. |

### Pass / Fail Criteria

- **PASS**: Per TCD 16031169448 §5-C — PEM registers accessible via TPMI on both NWP CBBs. PEM_STATUS excursion bits correctly set when RAPL limits cause sustained frequency drop below FET. PEM_STATUS.PKG_PL1_INBAND (bit 10) asserts during PL1 throttle; PEM_STATUS.PKG_PL2_INBAND (bit 13) asserts during PL2 throttle. PEM_ANY (bit 0) auto-set when any excursion bit is set. PEM_COUNTER non-zero and incrementing during active excursion. W0C semantics work correctly. PEM re-asserts after clear if excursion still active. PEM_STATUS stays 0 after clear when no excursion active. All checks pass on both cbb0 AND cbb1. No MCA or hang.
- **FAIL**: PEM_STATUS bits not set during active RAPL throttle below FET. Wrong bits set (e.g., thermal bit when only RAPL is limiting). PEM_COUNTER stuck at 0 during active excursion. W0C clear fails. PEM re-asserts when no excursion is active. Any check fails on either cbb0 or cbb1. MCA or system hang at any point.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| PEM_CONTROL (cbb0) | sv.socket0.cbb0.base.tpmi.pem_control | FET, TW, ENABLE_PEM fields match programmed values |
| PEM_CONTROL (cbb1) | sv.socket0.cbb1.base.tpmi.pem_control | FET, TW, ENABLE_PEM fields match programmed values |
| PEM_STATUS (cbb0) | sv.socket0.cbb0.base.tpmi.pem_status | Correct excursion bits set during throttle; 0 after clear with no excursion |
| PEM_STATUS (cbb1) | sv.socket0.cbb1.base.tpmi.pem_status | Correct excursion bits set during throttle; 0 after clear with no excursion |
| PEM_COUNTER (PMT) | PMT read via TPMI | Counter > 0 and incrementing during active excursion |
| PEM_HEADER | sv.socket0.cbb{0,1}.base.tpmi.pem_header | INTERFACE_VERSION = 1 (gen3) |
| socket_rapl_pid_output | sv.socket0.nio.pcudata.socket_rapl_pid_output | Confirms RAPL is actively throttling (output below FET) |
| Per-core frequency | die.core_pmsb target_wp1.core_frequence | Frequency below FET during excursion; above FET after restore |

### Post-Process

N/A

### References

- [TCD 16031169448 -- Socket RAPL - Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448)
- [Wave 3 Common HAS -- PEM_STATUS-Gen3-DMR](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html#pem_status-gen3---dmr)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)

---

## Section A: NWP Delta

NWP carries forward DMR PEM (gen3) behavior. PEM is a Pcode (CBB-scoped) feature — each CBB has its own PEM instance. NWP has 2 CBBs (vs 4 on DMR).

| Aspect | DMR | NWP |
|--------|-----|-----|
| CBB count | 4 (cbb0-cbb3) | 2 (cbb0-cbb1) |
| PEM instances | 4 (one per CBB) | 2 (one per CBB) |
| PEM register path | sv.socket0.cbb{0-3}.base.tpmi.pem_status | sv.socket0.cbb{0,1}.base.tpmi.pem_status |
| Gen | gen3 (32 events) | gen3 (32 events) |
| Interfaces | TPMI + PMT (PCS deprecated) | TPMI + PMT (PCS deprecated) |

## Section F: Recommendations

Recommendation: ADOPT — dmr.xml -> nwp.xml; PEM verification on both NWP CBBs (cbb0 and cbb1). Test PL1 and PL2 excursion detection including W0C clear and re-assertion semantics. Priority: Medium — plc.feature.p2; PEM provides critical visibility into RAPL excursion events for CSP manageability.

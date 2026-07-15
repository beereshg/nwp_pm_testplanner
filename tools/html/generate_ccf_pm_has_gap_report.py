"""
Generate HTML coverage gap report: CBB CCF PM HAS vs NWP TP 22022420505.
Source: https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html
Usage: python tools/html/generate_ccf_pm_has_gap_report.py
Output: tcd_description_output/CCF_PM_HAS_Coverage_Gap_Report.html
"""

import json, pathlib

# ─────────────────────────────────────────────────────────────────────────────
# DATA: HAS PM flows (from DMR_CBB + NWP spec queries)
# ─────────────────────────────────────────────────────────────────────────────

HAS_FLOWS = [
    # ── AREA 1: GV Management ─────────────────────────────────────────────────
    {
        "area": "GV Management",
        "area_id": "gv",
        "flows": [
            {
                "id": "GV-01",
                "name": "NonAutoGV mode — default workpoint execution",
                "has_detail": "Default and only supported GV mode in CBB. PCode provides workpoint via CCF_WP register. CCF executes GV transitions without autonomous frequency selection. Active at reset/boot and C-state exit.",
                "registers": ["CCF_WP", "UFS_CONTROL.MAX_RATIO", "UFS_CONTROL.MIN_RATIO", "UFS_STATUS"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422878 — CBB CCF NonAutoGV Mode Fast GV"],
                "gap": None
            },
            {
                "id": "GV-02",
                "name": "BIOS-time UFS_CONTROL initialization (P0/Pm cap)",
                "has_detail": "During TPMI_INIT (PH1.x), BIOS writes UFS_CONTROL with min/max ratios derived from fused P0/Pm caps in UFS_HEADER. AUTONOMOUS_UFS_DISABLED flag prevents autonomous override post-BIOS.",
                "registers": ["UFS_HEADER", "UFS_CONTROL.MAX_RATIO", "UFS_CONTROL.MIN_RATIO", "AUTONOMOUS_UFS_DISABLED"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422850 — CBB CCF GV BIOS Configuration"],
                "gap": None
            },
            {
                "id": "GV-03",
                "name": "PEGA mailbox GV injection (B2P path)",
                "has_detail": "PEGA injects synthetic P-state requests via B2P mailbox, bypassing OS/TPMI path. Used for validation to directly control GVFSM without OS involvement.",
                "registers": ["pega_mailbox.pega_pstate(meshgv=...)", "UFS_STATUS"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422851 — CBB CCF GV PEGA Injection"],
                "gap": None
            },
            {
                "id": "GV-04",
                "name": "TPMI UFS_CONTROL runtime GV requests (OS path)",
                "has_detail": "OS/FW writes UFS_CONTROL.MAX_RATIO at runtime to request ring frequency changes. CCF PMA transitions via GVFSM. UFS_STATUS reflects current ratio.",
                "registers": ["UFS_CONTROL", "UFS_STATUS", "TPMI per-die instances"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422859 — CBB CCF GV TPMI Request"],
                "gap": None
            },
            {
                "id": "GV-05",
                "name": "VF curve enforcement (voltage-frequency operating points)",
                "has_detail": "CCF must not operate outside defined VF curve points. BIOS/fuse-derived VF table sets legal (V, F) pairs. GV transitions must land on or between VF table entries.",
                "registers": ["VF_CURVE_TABLE", "UFS_STATUS.CURRENT_RATIO"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422863 — CBB CCF VF Curves"],
                "gap": None
            },
            {
                "id": "GV-06",
                "name": "GVFSM state machine progression",
                "has_detail": "GVFSM progresses through: IDLE → BLOCK → INC_GB (increment global barrier) → DEC_DB (decrement database) → RESUME → BLK_INTF (block interface). Each state must complete before advancing. No partial transitions allowed.",
                "registers": ["UFS_STATUS.GVFSM_STATE", "CCF_GV_STATE"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC validates the GVFSM state machine progression. NWP only checks final frequency outcome, not the intermediate IDLE→BLOCK→INC_GB→DEC_DB→RESUME transition states."
            },
            {
                "id": "GV-07",
                "name": "Per-die independent GV (NWP multi-die)",
                "has_detail": "NWP CBB dies can independently scale mesh frequency. Each die exposes its own UFS_CONTROL/UFS_STATUS TPMI registers. Frequency steps in 100 MHz increments due to PLL/UCIE limitations. No inter-die handshake for GV.",
                "registers": ["sv.socket0.cbb0.base.tpmi.ufs_control", "sv.socket0.cbb1.base.tpmi.ufs_control"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "NWP tests single-CBB TPMI GV. No TC validates that each CBB die scales independently, or that per-die GV does not affect adjacent dies."
            },
            {
                "id": "GV-08",
                "name": "AGV/FGV contention under simultaneous C-state transitions",
                "has_detail": "When multiple GV requestors (AGV from CCF PMA, FGV via PCode) issue simultaneous requests during C6/MC3 entry or exit, PCode arbitrates. The winning workpoint must be applied atomically. didt prevention via staggered transitions.",
                "registers": ["CCF_WP", "UFS_STATUS", "PMA_FSM_STATE"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC tests simultaneous AGV+FGV contention. NWP validates each GV path in isolation. Contention scenarios and arbitration atomicity under C-state transitions are uncovered."
            },
        ]
    },
    # ── AREA 2: Idle States ───────────────────────────────────────────────────
    {
        "area": "Idle States",
        "area_id": "idle",
        "flows": [
            {
                "id": "IDLE-01",
                "name": "Fast Ring C3 — autonomous clock gating",
                "has_detail": "CCF PMA autonomously enters Fast Ring C3 by gating main global Uclk tree drivers. No Punit involvement. UCIE Uclk remains running. PMA can autonomously exit unless locked by Punit for PKGC6 entry.",
                "registers": ["UDI resource", "UFS_STATUS.FAST_RING_C3"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422865 — CBB CCF Fast Ring C3"],
                "gap": None
            },
            {
                "id": "IDLE-02",
                "name": "Ring C3 — Punit-directed CCF drain + PLL shutdown",
                "has_detail": "Punit instructs CCF PMA to enter Ring C3 (requires Fast Ring C3 first). CCF drains all transactions, transitions D2D to L1, shuts down ring PLLs, asserts global clock gating. Wake: PLL restore → deassert resets → resume.",
                "registers": ["UFS_STATUS.RING_C3", "D2D_LINK_STATE"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422873 — CBB CCF Ring C3"],
                "gap": None
            },
            {
                "id": "IDLE-03",
                "name": "Cstate wake events across active/idle (HPM, PECI, stagger)",
                "has_detail": "Wake events from HPM, PECI, and stagger injection trigger C-state exit. CCF PMA must restore clocks/frequency correctly. Wake injection timing affects exit latency.",
                "registers": ["WAKE_EVENT_SOURCE", "UFS_STATUS"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422868 — CBB CCF PM Cstate wake events"],
                "gap": None
            },
            {
                "id": "IDLE-04",
                "name": "D2D → L1 transition during Ring C3 entry",
                "has_detail": "Before ring PLLs are shut down in Ring C3, D2D link must be transitioned to L1 state. CCF must verify L1 acknowledgment before proceeding. On exit, D2D must be restored to L0 in correct order.",
                "registers": ["D2D_LINK_STATE", "D2D_PM_CTRL"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "Ring C3 TC exists but does not validate D2D L1 entry/exit as part of the Ring C3 sequence. D2D state transitions are not checked."
            },
            {
                "id": "IDLE-05",
                "name": "Ring C3 abort on wake event (mid-entry race)",
                "has_detail": "If a wake event arrives after Ring C3 entry has started but before PLLs are shut down, CCF must abort entry cleanly and return to active state without losing in-flight transactions.",
                "registers": ["UFS_STATUS.RING_C3", "WAKE_ABORT_COUNT"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC injects wake events mid-Ring-C3 entry. The abort/race path is completely uncovered."
            },
            {
                "id": "IDLE-06",
                "name": "PKGC6 (PC6) entry/exit — CCF coordination with Ring C3",
                "has_detail": "PC6 entry: Punit directs CCF to enter Ring C3 as prerequisite. CCF drains, blocks cNCUs, disables PLLs, gates clocks. PC6 exit: CCF unblocks, restores PLLs, resumes normal operation. Timing must meet platform latency budgets.",
                "registers": ["PCU_PM_STATUS", "UFS_STATUS", "PKG_CSTATE"],
                "nwp_coverage": "PARTIAL",
                "nwp_tc": ["22022422873 — CBB CCF Ring C3 (covers Ring C3 which is prerequisite)"],
                "gap": "NWP tests Ring C3 but does not test full PC6 entry+exit coordination sequence. cNCU block/unblock and PLL restore timing under PC6 not validated."
            },
            {
                "id": "IDLE-07",
                "name": "LC6 / FC6 ring coordination",
                "has_detail": "LC6 (Light C6) and FC6 (Full C6) are additional CCF idle states with distinct entry/exit sequences. LC6 allows partial CCF state retention; FC6 is complete shutdown. Both require specific ring drain sequences.",
                "registers": ["PKG_CSTATE", "CCF_IDLE_STATE"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC covers LC6 or FC6 ring state transitions. Only Ring C3 (for PC6) is tested. LC6/FC6 specific ring drain sequences and wake latencies are uncovered."
            },
            {
                "id": "IDLE-08",
                "name": "D2D active-idle state (NWP-specific)",
                "has_detail": "NWP supports a D2D active-idle state where the TX direction is gated independently per die. No inter-chiplet signaling required. CCF must be able to resume from active-idle on demand.",
                "registers": ["D2D_ACTIVE_IDLE_CTRL", "D2D_LINK_STATE"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "NWP-specific flow. No TC validates D2D active-idle entry/exit interaction with CCF idle state management."
            },
            {
                "id": "IDLE-09",
                "name": "Staggered module C6 entry ordering",
                "has_detail": "When multiple CBB modules enter C6, the order must be staggered to prevent simultaneous didt events. PCode controls the staggering sequence. Incorrect ordering can cause voltage droop or stability issues.",
                "registers": ["MODULE_C6_STAGGER_CTRL", "PMA_FSM_STATE"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC validates module staggering order or timing. NWP tests single-module C6 entry only. Multi-module simultaneous entry with didt prevention is uncovered."
            },
        ]
    },
    # ── AREA 3: Ring Frequency Scalability ────────────────────────────────────
    {
        "area": "Ring Frequency Scalability",
        "area_id": "scalability",
        "flows": [
            {
                "id": "SCALE-01",
                "name": "PMON counters (LLC access, hit, TOR occupancy)",
                "has_detail": "Each CBO contains PMON counters for LLC accesses, LLC hits, and TOR occupancy. These feed into SBO distress telemetry.",
                "registers": ["CBO_PMON_CTL", "CBO_PMON_CTR"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422886 — CBB CCF PMON"],
                "gap": None
            },
            {
                "id": "SCALE-02",
                "name": "CBO telemetry per-cluster grade accumulation",
                "has_detail": "Each CBO accumulates distress grades based on LLC event telemetry. CBOs report to SBO for cluster-level aggregation per RSE interval.",
                "registers": ["CBO_DISTRESS_GRADE", "CBO_TELEMETRY_STATUS"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422889 — CBB CCF CBO Telemetry"],
                "gap": None
            },
            {
                "id": "SCALE-03",
                "name": "SBO telemetry — cluster distress aggregation + IA_DISTRESS",
                "has_detail": "SBO accumulates CBO grades and sends IA_DISTRESS[3:0] to Punit via IO register once per RSE (every 2k/4k/8k/16k uclk cycles). SBO provides per-cluster status and snoop information.",
                "registers": ["SBO_DISTRESS_OUTPUT", "IA_DISTRESS[3:0]"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422900 — CBB CCF SBO Telemetry"],
                "gap": None
            },
            {
                "id": "SCALE-04",
                "name": "Distress signal → PCode ring scaling (message to Punit)",
                "has_detail": "SBO-to-Punit message carries IA_DISTRESS value. Pcode translates distress into ia_ring_factor and adjusts ring frequency. Slow loop ~1ms; fast path on distress change or every DistressCycleUpdate (100us).",
                "registers": ["SBO_TO_PUNIT_IO_REG", "IA_RING_FACTOR"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422896 — CBB CCF Message to Punit"],
                "gap": None
            },
            {
                "id": "SCALE-05",
                "name": "IA distress signal (snoop scalability)",
                "has_detail": "Snoop distress is integrated into the IA_DISTRESS telemetry path. Pcode samples snoop counters (one per SBO, four per CBB) every 1ms and adjusts ring frequency accordingly.",
                "registers": ["SNOOP_PMON_CTR", "IA_DISTRESS"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422894 — CBB CCF Distress signal", "22022422895 — CBB CCF Snoop Scalability/Distress"],
                "gap": None
            },
            {
                "id": "SCALE-06",
                "name": "PCode distress algorithm (EWMA, ia_ring_factor mapping)",
                "has_detail": "Pcode uses exponential moving averages to smooth distress values. Maps distress level to scaling parameters (min/max value, up/down step, high distress level). Algorithm is tunable post-silicon.",
                "registers": ["DISTRESS_ALGO_CONFIG", "IA_RING_FACTOR", "RING_FREQ_CTRL"],
                "nwp_coverage": "COVERED",
                "nwp_tc": ["22022422905 — CBB CCF PCODE algorithm for distress input"],
                "gap": None
            },
            {
                "id": "SCALE-07",
                "name": "Distress fast path (DistressCycleUpdate 100us)",
                "has_detail": "Beyond the 1ms slow loop, PCode has a fast response path triggered on distress state change or every DistressCycleUpdate interval (~100us). This fast path reduces latency in ring frequency recovery.",
                "registers": ["DISTRESS_CYCLE_UPDATE_INTERVAL", "IA_RING_FACTOR"],
                "nwp_coverage": "PARTIAL",
                "nwp_tc": ["22022422905 — PCode algorithm (slow loop only)"],
                "gap": "TC covers PCode algorithm but timing of the fast path (100us DistressCycleUpdate) is not validated. No test verifies that the fast path triggers correctly on distress level change."
            },
            {
                "id": "SCALE-08",
                "name": "PVP → IA_DISTRESS → ring frequency reduction",
                "has_detail": "Power Virus Protection (PVP) throttling via EXE port dispatch halt triggers IA_DISTRESS signaling to CCF. This reduces ring frequency to protect silicon from dV/dt excursions caused by power virus patterns.",
                "registers": ["PVP_STATUS", "IA_DISTRESS", "IA_RING_FACTOR"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "PVP-to-CCF distress path is not tested. NWP tests IA_DISTRESS from LLC telemetry but not from PVP throttle events. PVP trigger conditions (64/1024-cycle windows) are not exercised."
            },
            {
                "id": "SCALE-09",
                "name": "ProcHot assertion → ring frequency reduction",
                "has_detail": "PROCHOT assertion causes CCF PMA to reduce ring frequency to safe minimum. PROCHOT_STATUS reports current assertion state and source. PROCHOT_OVERRIDE allows firmware to mask for debug.",
                "registers": ["PROCHOT_STATUS", "PROCHOT_OVERRIDE", "UFS_STATUS.CURRENT_RATIO"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC validates ProcHot → ring frequency reduction flow. PROCHOT_STATUS and PROCHOT_OVERRIDE registers are not exercised in NWP CCF PM TP."
            },
            {
                "id": "SCALE-10",
                "name": "Thermal throttling → ring frequency and VCCRING voltage reduction",
                "has_detail": "Thermal events (DTS-based, from Punit/Pcode signals) cause CCF PMA to lower ring frequency and VCCRING via VID/SVID. Telemetry interfaces report throttling actions.",
                "registers": ["THERMAL_STATUS", "VCCRING_VID", "UFS_STATUS.CURRENT_RATIO"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC validates thermal-triggered ring frequency or voltage reduction. DTS-to-CCF throttling path and VCCRING voltage management are completely uncovered."
            },
        ]
    },
    # ── AREA 4: Uniform Fabric Frequency ─────────────────────────────────────
    {
        "area": "Uniform Fabric Frequency",
        "area_id": "uniform",
        "flows": [
            {
                "id": "UFF-01",
                "name": "UNIFORM_CBB_FABRIC_FREQ_MODE enable via BIOS knob",
                "has_detail": "BIOS sets UFS_CONTROL bit 30 to enable uniform frequency mode. All CBB dies must be programmed to the same mode. BIOS knob exposes this to platform configuration.",
                "registers": ["UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE (bit 30)"],
                "nwp_coverage": "TCD_NO_TC",
                "nwp_tc": ["TCD 22022421214 — exists, 0 TCs"],
                "gap": "TCD 22022421214 exists but has no TCs. BIOS knob enable/verify path is not tested."
            },
            {
                "id": "UFF-02",
                "name": "UNIFORM_CBB_FABRIC_FREQ_MODE enable/disable via TPMI at runtime",
                "has_detail": "SW can enable or disable uniform mode at runtime by writing UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE. All dies must be programmed consistently.",
                "registers": ["UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE"],
                "nwp_coverage": "TCD_NO_TC",
                "nwp_tc": ["TCD 22022421216 — exists, 0 TCs"],
                "gap": "TCD 22022421216 exists but has no TCs. Runtime enable/disable via TPMI not validated."
            },
            {
                "id": "UFF-03",
                "name": "HPM messaging — CBB_CCF_FREQUENCY upstream/downstream",
                "has_detail": "When uniform mode is active, each CBB sends HPM opcode 0x1b with UPSTREAM_CCF_DESIRED_RATIO (bits 39:32). IMH collects, selects maximum, sends DOWNSTREAM_CCF_RESOLVED_MIN_RATIO (bits 47:40) back to all CBBs.",
                "registers": ["HPM_MSG_CCF_FREQUENCY (opcode 0x1b)", "UPSTREAM_CCF_DESIRED_RATIO", "DOWNSTREAM_CCF_RESOLVED_MIN_RATIO"],
                "nwp_coverage": "TCD_NO_TC",
                "nwp_tc": ["TCD 22022421218 — exists, 0 TCs"],
                "gap": "TCD 22022421218 exists but has no TCs. HPM message fields and IMH max-select logic not validated."
            },
            {
                "id": "UFF-04",
                "name": "Uniform frequency cross Fast Ring C3",
                "has_detail": "When uniform mode is enabled, Fast Ring C3 entry on one CBB must not break the uniform frequency contract. Resolved min frequency must be re-negotiated on exit.",
                "registers": ["UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE", "UFS_STATUS"],
                "nwp_coverage": "TCD_NO_TC",
                "nwp_tc": ["TCD 22022421207 — exists, 0 TCs"],
                "gap": "TCD 22022421207 exists but has no TCs. Interaction between uniform mode and Fast Ring C3 not tested."
            },
            {
                "id": "UFF-05",
                "name": "Uniform frequency cross PC6",
                "has_detail": "PC6 entry suspends uniform frequency mode. On PC6 exit, CBBs renegotiate uniform frequency via HPM messaging.",
                "registers": ["UFS_CONTROL", "HPM_MSG_CCF_FREQUENCY", "PKG_CSTATE"],
                "nwp_coverage": "TCD_NO_TC",
                "nwp_tc": ["TCD 22022421209 — exists, 0 TCs"],
                "gap": "TCD 22022421209 exists but has no TCs. PC6 entry/exit + uniform frequency re-negotiation not validated."
            },
            {
                "id": "UFF-06",
                "name": "Uniform frequency cross ProcHot",
                "has_detail": "ProcHot assertion reduces ring frequency below the uniform mode minimum. ProcHot takes priority over the uniform fabric frequency floor.",
                "registers": ["PROCHOT_STATUS", "UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE"],
                "nwp_coverage": "TCD_NO_TC",
                "nwp_tc": ["TCD 22022421211 — exists, 0 TCs"],
                "gap": "TCD 22022421211 exists but has no TCs. ProcHot override of uniform frequency floor not validated."
            },
            {
                "id": "UFF-07",
                "name": "Uniform frequency cross RAPL",
                "has_detail": "RAPL power cap can restrict ring frequency below the uniform mode minimum. RAPL constraint takes priority over uniform frequency floor.",
                "registers": ["RAPL_LIMIT", "UFS_CONTROL.UNIFORM_CBB_FABRIC_FREQ_MODE"],
                "nwp_coverage": "TCD_NO_TC",
                "nwp_tc": ["TCD 22022421212 — exists, 0 TCs"],
                "gap": "TCD 22022421212 exists but has no TCs. RAPL power cap interaction with uniform frequency floor not tested."
            },
        ]
    },
    # ── AREA 5: Boot / Reset Initialization ──────────────────────────────────
    {
        "area": "Boot & Reset Initialization",
        "area_id": "boot",
        "flows": [
            {
                "id": "BOOT-01",
                "name": "Post-reset CCF frequency defaults (fused P0/Pm)",
                "has_detail": "On cold boot or reset, CCF starts in NonAutoGV mode. Default frequency is set from fused caps in UFS_HEADER. BIOS must update UFS_CONTROL before BIOS_DONE.",
                "registers": ["UFS_HEADER", "UFS_CONTROL", "BIOS_DONE"],
                "nwp_coverage": "PARTIAL",
                "nwp_tc": ["22022422850 — BIOS Config (covers BIOS init, not reset default)"],
                "gap": "No TC validates post-reset CCF frequency before BIOS writes UFS_CONTROL. The fused default state (UFS_HEADER values) is not verified independently."
            },
            {
                "id": "BOOT-02",
                "name": "VID/SVID voltage management during GV (VCCRING)",
                "has_detail": "CCF PMA manages VCCRING voltage via VID/SVID protocol during GV transitions. Voltage must be adjusted in sync with frequency changes per VF table. Up-transitions: voltage first; down-transitions: frequency first.",
                "registers": ["SVID_CTRL", "VCCRING_VID", "VF_CURVE_TABLE"],
                "nwp_coverage": "GAP",
                "nwp_tc": [],
                "gap": "No TC validates VCCRING SVID voltage management during GV. VF curve TC checks frequency endpoints but not voltage sequencing (V before F on up-GV, F before V on down-GV)."
            },
        ]
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def get_stats():
    total = sum(len(a["flows"]) for a in HAS_FLOWS)
    covered = sum(1 for a in HAS_FLOWS for f in a["flows"] if f["nwp_coverage"] == "COVERED")
    partial = sum(1 for a in HAS_FLOWS for f in a["flows"] if f["nwp_coverage"] == "PARTIAL")
    tcd_no_tc = sum(1 for a in HAS_FLOWS for f in a["flows"] if f["nwp_coverage"] == "TCD_NO_TC")
    gap = sum(1 for a in HAS_FLOWS for f in a["flows"] if f["nwp_coverage"] == "GAP")
    return {"total": total, "covered": covered, "partial": partial, "tcd_no_tc": tcd_no_tc, "gap": gap}

# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY TABLE
# ─────────────────────────────────────────────────────────────────────────────

PRIORITY_GAPS = [
    # P1 — Critical
    {
        "priority": "P1", "color": "#dc2626",
        "id": "GV-08",
        "title": "AGV/FGV contention under C-state transitions",
        "where": "Add to TCD 22022421168 (PEGA) or new TCD under TPF 22022420507",
        "why": "GV arbitration during C-state transitions is the core CCF PM correctness gate. A missed arbitration causes frequency glitch or system hang."
    },
    {
        "priority": "P1", "color": "#dc2626",
        "id": "IDLE-05",
        "title": "Ring C3 abort on mid-entry wake event",
        "where": "Add to TCD 22022421179 (Idle States)",
        "why": "Unhandled abort during Ring C3 entry causes in-flight transaction loss and potential deadlock."
    },
    {
        "priority": "P1", "color": "#dc2626",
        "id": "SCALE-08",
        "title": "PVP → IA_DISTRESS → CCF ring frequency",
        "where": "New TC under TCD 22022421197 (Distress Signal)",
        "why": "PVP throttle is the primary dV/dt protection path. If the PVP→distress chain breaks, silicon damage risk on power virus workloads."
    },
    {
        "priority": "P1", "color": "#dc2626",
        "id": "IDLE-07",
        "title": "LC6 / FC6 ring coordination",
        "where": "New TCD under TPF 22022420512 (Idle States)",
        "why": "LC6/FC6 are package-level C-states used in production. No coverage means entire power-off CCF sequence is unvalidated."
    },
    # P2 — High
    {
        "priority": "P2", "color": "#f59e0b",
        "id": "UFF-01..07",
        "title": "All 7 Uniform Fabric Frequency TCs (TPF 22022420515)",
        "where": "7 existing TCDs (22022421207–22022421218) each need at least 1 TC",
        "why": "Entire TPF 22022420515 has 0 TCs. Uniform fabric mode is a shipped feature used by VMM workloads — completely unvalidated."
    },
    {
        "priority": "P2", "color": "#f59e0b",
        "id": "SCALE-09",
        "title": "ProcHot → ring frequency reduction",
        "where": "New TC under TCD 22022421197 (Distress Signal) or new TCD",
        "why": "ProcHot is a key thermal protection path. Ring frequency not scaling down on ProcHot causes thermal violation."
    },
    {
        "priority": "P2", "color": "#f59e0b",
        "id": "IDLE-04",
        "title": "D2D → L1 transition during Ring C3",
        "where": "Extend TC 22022422873 (Ring C3) to check D2D link state",
        "why": "Ring C3 without D2D L1 is not a complete ring drain. Leaving D2D in L0 during PLL shutdown causes UCIe link errors."
    },
    {
        "priority": "P2", "color": "#f59e0b",
        "id": "GV-07",
        "title": "Per-die independent GV — NWP multi-die",
        "where": "New TC under TCD 22022421171 (TPMI Interface)",
        "why": "NWP-specific critical path. If per-die GV is broken, one CBB die can stall while another scales, breaking cache coherency latency."
    },
    {
        "priority": "P2", "color": "#f59e0b",
        "id": "IDLE-09",
        "title": "Staggered module C6 entry ordering",
        "where": "New TC under TCD 22022421179 (Idle States)",
        "why": "didt from simultaneous module C6 entry can cause voltage droops. Stagger ordering validation prevents silicon reliability issues."
    },
    # P3 — Medium
    {
        "priority": "P3", "color": "#22c55e",
        "id": "GV-06",
        "title": "GVFSM state machine progression",
        "where": "Add assertions to existing GV TCs or new TC under TPF 22022420507",
        "why": "GVFSM stuck in intermediate state causes CCF hang. State visibility helps debug future GV failures."
    },
    {
        "priority": "P3", "color": "#22c55e",
        "id": "SCALE-07",
        "title": "Distress fast path (100us DistressCycleUpdate)",
        "where": "Extend TC 22022422905 (PCode algorithm)",
        "why": "Fast path timing is important for ring frequency recovery under bursty LLC load. Slow path only validation misses timing SLA."
    },
    {
        "priority": "P3", "color": "#22c55e",
        "id": "IDLE-06",
        "title": "PKGC6 full entry/exit coordination (cNCU block/unblock)",
        "where": "New TC under TCD 22022421179 (Idle States) or new TCD under TPF 22022420512",
        "why": "Ring C3 TC covers PLL shutdown but not cNCU block/unblock, which is the PC6 handshake with IMH. Incomplete PC6 path validation."
    },
    {
        "priority": "P3", "color": "#22c55e",
        "id": "BOOT-02",
        "title": "VCCRING SVID voltage management during GV",
        "where": "Extend TC 22022422863 (VF Curves) to check voltage transitions",
        "why": "Incorrect V-before-F or F-before-V sequencing during GV is a voltage drooping risk. VF curve TC only checks frequency endpoints."
    },
    {
        "priority": "P3", "color": "#22c55e",
        "id": "SCALE-10",
        "title": "Thermal throttling → ring frequency + VCCRING reduction",
        "where": "New TC, possibly under a new TPF (CCF Thermal/Protection)",
        "why": "Thermal-triggered ring scaling path is distinct from distress-based scaling. Complete thermal protection chain is unvalidated."
    },
    {
        "priority": "P3", "color": "#22c55e",
        "id": "IDLE-08",
        "title": "D2D active-idle state (NWP-specific)",
        "where": "New TC under TPF 22022420512 (Idle States)",
        "why": "NWP-only power-saving feature. Active-idle bugs manifest as unnecessary power consumption on compute chiplets."
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# HTML GENERATION
# ─────────────────────────────────────────────────────────────────────────────

COVERAGE_STYLE = {
    "COVERED":    ("#dcfce7", "#16a34a", "Covered", "✓"),
    "PARTIAL":    ("#fef9c3", "#ca8a04", "Partial",  "~"),
    "TCD_NO_TC":  ("#fff7ed", "#ea580c", "TCD — 0 TCs", "!"),
    "GAP":        ("#fee2e2", "#dc2626", "GAP",      "✗"),
}

def coverage_badge(cov):
    bg, fg, label, icon = COVERAGE_STYLE[cov]
    return f'<span class="cov-badge" style="background:{bg};color:{fg};border:1px solid {fg}">{icon} {label}</span>'

def tc_list(tc_items):
    if not tc_items:
        return '<span class="no-tc">None</span>'
    items = "".join(f'<span class="tc-chip">{t}</span>' for t in tc_items)
    return f'<div class="tc-chips">{items}</div>'

def reg_list(regs):
    items = "".join(f'<code class="reg-chip">{r}</code>' for r in regs)
    return f'<div class="reg-chips">{items}</div>'

def flow_row(flow):
    cov = flow["nwp_coverage"]
    bg, fg, _, _ = COVERAGE_STYLE[cov]
    gap_cell = f'<td class="gap-cell">{flow["gap"]}</td>' if flow["gap"] else '<td class="gap-cell ok">—</td>'
    return f"""<tr class="flow-row" style="background:{bg}10">
      <td class="fid"><code>{flow["id"]}</code></td>
      <td class="fname">{flow["name"]}</td>
      <td class="fhas">{flow["has_detail"]}</td>
      <td class="fregs">{reg_list(flow["registers"])}</td>
      <td class="fcov">{coverage_badge(cov)}</td>
      <td class="ftcs">{tc_list(flow["nwp_tc"])}</td>
      {gap_cell}
    </tr>"""

def priority_row(p):
    color = p["color"]
    return f"""<tr>
      <td><span class="pri-badge" style="background:{color}">{p["priority"]}</span></td>
      <td><code class="fid-inline">{p["id"]}</code></td>
      <td class="ptitle">{p["title"]}</td>
      <td class="pwhere">{p["where"]}</td>
      <td class="pwhy">{p["why"]}</td>
    </tr>"""

def generate_html():
    stats = get_stats()
    coverage_pct = int(100 * stats["covered"] / stats["total"])
    risk_pct = int(100 * (stats["gap"] + stats["tcd_no_tc"]) / stats["total"])

    # Per-area summary bars
    area_bars = ""
    for area in HAS_FLOWS:
        flows = area["flows"]
        n = len(flows)
        covered = sum(1 for f in flows if f["nwp_coverage"] == "COVERED")
        partial = sum(1 for f in flows if f["nwp_coverage"] == "PARTIAL")
        tcd_no_tc = sum(1 for f in flows if f["nwp_coverage"] == "TCD_NO_TC")
        gap = sum(1 for f in flows if f["nwp_coverage"] == "GAP")
        pct = int(100 * covered / n)
        w_cov = int(100 * covered / n)
        w_par = int(100 * partial / n)
        w_tcd = int(100 * tcd_no_tc / n)
        w_gap = int(100 * gap / n)
        area_bars += f"""<div class="area-bar-row">
          <div class="area-bar-label">{area["area"]}</div>
          <div class="stacked-bar">
            <div class="bar-seg covered" style="width:{w_cov}%" title="Covered: {covered}"></div>
            <div class="bar-seg partial" style="width:{w_par}%" title="Partial: {partial}"></div>
            <div class="bar-seg tcd-no-tc" style="width:{w_tcd}%" title="TCD/No TC: {tcd_no_tc}"></div>
            <div class="bar-seg gap" style="width:{w_gap}%" title="GAP: {gap}"></div>
          </div>
          <div class="area-bar-stats">{covered}✓ {partial}~ {tcd_no_tc}! {gap}✗ / {n}</div>
        </div>"""

    # Per-area tables
    area_sections = ""
    for area in HAS_FLOWS:
        rows = "".join(flow_row(f) for f in area["flows"])
        area_sections += f"""
<div class="area-section" id="area-{area['area_id']}">
  <h2 class="area-title">{area["area"]}</h2>
  <div class="table-wrapper">
    <table class="flow-table">
      <thead>
        <tr>
          <th style="width:70px">ID</th>
          <th style="width:220px">HAS PM Flow</th>
          <th style="width:260px">HAS Description</th>
          <th style="width:200px">Key Registers</th>
          <th style="width:110px">NWP Coverage</th>
          <th style="width:200px">NWP TCs</th>
          <th>Gap Detail</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""

    # Priority table
    p_rows = "".join(priority_row(p) for p in PRIORITY_GAPS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>CBB CCF PM HAS — NWP Coverage Gap Report</title>
<style>
:root {{
  --primary: #1e3a5f; --accent: #2563eb; --bg: #f8fafc;
  --card: #fff; --border: #e2e8f0; --text: #1e293b; --muted: #64748b;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; }}

.header {{
  background: linear-gradient(135deg, #0f2744 0%, #1e4d8c 60%, #2563eb 100%);
  color: white; padding: 36px 48px 28px;
}}
.header h1 {{ font-size: 1.85rem; font-weight: 800; margin-bottom: 6px; }}
.header-sub {{ font-size: 0.92rem; opacity: 0.85; margin-bottom: 20px; }}
.header-sub a {{ color: #93c5fd; text-decoration: none; }}
.header-sub a:hover {{ text-decoration: underline; }}
.header-meta {{ display: flex; gap: 36px; flex-wrap: wrap; }}
.meta-item {{ display: flex; flex-direction: column; }}
.meta-label {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.06em; opacity: 0.65; }}
.meta-value {{ font-size: 1rem; font-weight: 700; }}

.stats-bar {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(130px,1fr));
  gap: 12px; padding: 20px 48px; background: white;
  border-bottom: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,.06);
}}
.stat {{ text-align: center; padding: 10px 6px; border-radius: 8px; border: 1px solid var(--border); }}
.stat-num {{ font-size: 1.8rem; font-weight: 800; }}
.stat-num.green {{ color: #16a34a; }}
.stat-num.yellow {{ color: #ca8a04; }}
.stat-num.orange {{ color: #ea580c; }}
.stat-num.red {{ color: #dc2626; }}
.stat-num.blue {{ color: #2563eb; }}
.stat-label {{ font-size: 0.72rem; color: var(--muted); margin-top: 2px; }}

.legend-bar {{
  display: flex; gap: 16px; flex-wrap: wrap;
  padding: 12px 48px; background: white; border-bottom: 1px solid var(--border);
  align-items: center; font-size: 0.8rem;
}}
.legend-item {{ display: flex; align-items: center; gap: 6px; }}
.legend-dot {{ width: 14px; height: 14px; border-radius: 3px; }}

.main {{ display: flex; min-height: calc(100vh - 280px); }}
.sidebar {{ width: 240px; flex-shrink: 0; background: white; border-right: 1px solid var(--border); padding: 20px 16px; position: sticky; top: 0; max-height: 100vh; overflow-y: auto; }}
.sidebar-title {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); font-weight: 700; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
.sidebar-link {{ display: block; font-size: 0.8rem; color: var(--accent); text-decoration: none; padding: 5px 6px; border-radius: 4px; margin-bottom: 2px; }}
.sidebar-link:hover {{ background: #eff6ff; }}
.sidebar-section {{ margin-top: 16px; }}

.content {{ flex: 1; padding: 28px 40px; min-width: 0; }}

.coverage-overview {{ background: white; border: 1px solid var(--border); border-radius: 10px; padding: 20px 24px; margin-bottom: 28px; }}
.coverage-overview h2 {{ font-size: 1rem; font-weight: 700; color: var(--primary); margin-bottom: 16px; }}
.area-bar-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
.area-bar-label {{ font-size: 0.8rem; font-weight: 600; color: var(--text); min-width: 180px; }}
.stacked-bar {{ flex: 1; height: 16px; background: #f1f5f9; border-radius: 8px; overflow: hidden; display: flex; }}
.bar-seg {{ height: 100%; transition: width 0.3s; }}
.bar-seg.covered {{ background: #16a34a; }}
.bar-seg.partial {{ background: #ca8a04; }}
.bar-seg.tcd-no-tc {{ background: #ea580c; }}
.bar-seg.gap {{ background: #dc2626; }}
.area-bar-stats {{ font-size: 0.72rem; color: var(--muted); min-width: 100px; white-space: nowrap; }}

.priority-section {{ background: white; border: 1px solid var(--border); border-radius: 10px; padding: 20px 24px; margin-bottom: 28px; }}
.priority-section h2 {{ font-size: 1.1rem; font-weight: 700; color: var(--primary); margin-bottom: 14px; padding-bottom: 8px; border-bottom: 2px solid var(--accent); }}
.pri-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
.pri-table th {{ background: var(--primary); color: white; padding: 9px 12px; text-align: left; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; }}
.pri-table td {{ padding: 9px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
.pri-table tr:hover {{ background: #f8fafc; }}
.pri-badge {{ display: inline-block; font-size: 0.7rem; font-weight: 800; color: white; border-radius: 4px; padding: 2px 8px; }}
.ptitle {{ font-weight: 600; }}
.pwhere {{ font-size: 0.78rem; color: #1d4ed8; }}
.pwhy {{ font-size: 0.78rem; color: var(--muted); }}
.fid-inline {{ font-size: 0.75rem; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }}

.area-section {{ margin-bottom: 32px; }}
.area-title {{
  font-size: 1.1rem; font-weight: 700; color: white;
  background: var(--primary); padding: 10px 16px; border-radius: 8px 8px 0 0;
  border-bottom: 2px solid var(--accent);
}}
.table-wrapper {{ overflow-x: auto; border: 1px solid var(--border); border-top: none; border-radius: 0 0 8px 8px; }}
.flow-table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; }}
.flow-table th {{ background: #f1f5f9; color: var(--muted); padding: 8px 10px; text-align: left; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 2px solid var(--border); white-space: nowrap; }}
.flow-table td {{ padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }}
.flow-row:hover {{ background: #f8fafc !important; }}
.fid code {{ font-size: 0.72rem; font-weight: 700; color: var(--accent); background: #eff6ff; padding: 2px 6px; border-radius: 4px; }}
.fname {{ font-weight: 600; color: var(--text); }}
.fhas {{ font-size: 0.77rem; color: var(--muted); line-height: 1.5; }}
.fregs {{ }}
.reg-chips {{ display: flex; flex-wrap: wrap; gap: 3px; }}
.reg-chip {{ font-size: 0.68rem; background: #f1f5f9; color: #374151; border: 1px solid #d1d5db; border-radius: 3px; padding: 1px 5px; font-family: monospace; }}
.cov-badge {{ font-size: 0.72rem; font-weight: 700; border-radius: 4px; padding: 3px 8px; white-space: nowrap; }}
.tc-chips {{ display: flex; flex-direction: column; gap: 3px; }}
.tc-chip {{ font-size: 0.7rem; color: #1d4ed8; background: #dbeafe; border-radius: 4px; padding: 2px 6px; }}
.no-tc {{ font-size: 0.75rem; color: var(--muted); font-style: italic; }}
.gap-cell {{ font-size: 0.77rem; color: #7f1d1d; background: #fff5f5; border-left: 3px solid #dc2626; padding-left: 8px; }}
.gap-cell.ok {{ color: var(--muted); background: transparent; border-left: none; }}

.footer {{ background: var(--primary); color: white; text-align: center; padding: 16px; font-size: 0.78rem; opacity: 0.8; }}

@media (max-width: 900px) {{
  .main {{ flex-direction: column; }}
  .sidebar {{ width: 100%; max-height: none; position: static; }}
  .content {{ padding: 20px; }}
  .stats-bar {{ padding: 16px; }}
  .header {{ padding: 24px 20px; }}
  .legend-bar {{ padding: 10px 20px; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>CBB CCF PM HAS — NWP Coverage Gap Report</h1>
  <div class="header-sub">
    Source: <a href="https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html" target="_blank">CBB CCF PM HAS (docs.intel.com)</a>
    &nbsp;|&nbsp; Target TP: <a href="https://hsdes.intel.com/appstore/article-one/#/22022420505" target="_blank">22022420505 — [NWP PM] CBB CCF PM</a>
    &nbsp;|&nbsp; Analyzed: 2026-07-15 &nbsp;|&nbsp; Projects queried: DMR_CBB, NWP
  </div>
  <div class="header-meta">
    <div class="meta-item"><span class="meta-label">HAS PM Flows Analyzed</span><span class="meta-value">{stats["total"]}</span></div>
    <div class="meta-item"><span class="meta-label">Fully Covered</span><span class="meta-value">{stats["covered"]} ({coverage_pct}%)</span></div>
    <div class="meta-item"><span class="meta-label">Partial Coverage</span><span class="meta-value">{stats["partial"]}</span></div>
    <div class="meta-item"><span class="meta-label">TCD Exists / 0 TCs</span><span class="meta-value">{stats["tcd_no_tc"]}</span></div>
    <div class="meta-item"><span class="meta-label">Coverage Gaps</span><span class="meta-value">{stats["gap"]}</span></div>
    <div class="meta-item"><span class="meta-label">Risk Exposure</span><span class="meta-value">{risk_pct}%</span></div>
  </div>
</div>

<div class="stats-bar">
  <div class="stat"><div class="stat-num blue">{stats["total"]}</div><div class="stat-label">HAS PM Flows</div></div>
  <div class="stat"><div class="stat-num green">{stats["covered"]}</div><div class="stat-label">✓ Fully Covered</div></div>
  <div class="stat"><div class="stat-num yellow">{stats["partial"]}</div><div class="stat-label">~ Partially Covered</div></div>
  <div class="stat"><div class="stat-num orange">{stats["tcd_no_tc"]}</div><div class="stat-label">! TCD / 0 TCs</div></div>
  <div class="stat"><div class="stat-num red">{stats["gap"]}</div><div class="stat-label">✗ Coverage Gap</div></div>
  <div class="stat"><div class="stat-num red">{risk_pct}%</div><div class="stat-label">Risk Exposure</div></div>
  <div class="stat"><div class="stat-num blue">14</div><div class="stat-label">NWP TCs (total)</div></div>
  <div class="stat"><div class="stat-num orange">0</div><div class="stat-label">TPF UFF TCs</div></div>
</div>

<div class="legend-bar">
  <strong style="font-size:0.78rem;color:var(--muted)">Coverage Legend:</strong>
  <div class="legend-item"><div class="legend-dot" style="background:#16a34a"></div> Covered</div>
  <div class="legend-item"><div class="legend-dot" style="background:#ca8a04"></div> Partial — TC exists but incomplete</div>
  <div class="legend-item"><div class="legend-dot" style="background:#ea580c"></div> TCD exists, 0 TCs — scaffolded but empty</div>
  <div class="legend-item"><div class="legend-dot" style="background:#dc2626"></div> GAP — no TCD or TC exists</div>
</div>

<div class="main">
  <div class="sidebar">
    <div class="sidebar-title">Navigation</div>
    <a class="sidebar-link" href="#overview">Coverage Overview</a>
    <a class="sidebar-link" href="#priority">Priority Gap Table</a>
    <div class="sidebar-section">
      <div class="sidebar-title">HAS Areas</div>
      {''.join(f'<a class="sidebar-link" href="#area-{a["area_id"]}">{a["area"]}</a>' for a in HAS_FLOWS)}
    </div>
  </div>

  <div class="content">

    <!-- Coverage Overview -->
    <div class="coverage-overview" id="overview">
      <h2>Coverage by HAS Area</h2>
      {area_bars}
      <div style="margin-top:12px;font-size:0.75rem;color:var(--muted)">
        <span style="color:#ea580c;font-weight:700">⚠ TPF 22022420515 (Uniform Fabric Frequency): 7 TCDs with 0 TCs each</span> — this entire TPF is scaffolded but never executed.
      </div>
    </div>

    <!-- Priority Table -->
    <div class="priority-section" id="priority">
      <h2>Prioritized Gap Action Plan</h2>
      <table class="pri-table">
        <thead>
          <tr>
            <th style="width:50px">Priority</th>
            <th style="width:80px">Flow ID</th>
            <th style="width:220px">Gap Title</th>
            <th style="width:220px">Recommended Action</th>
            <th>Why It Matters</th>
          </tr>
        </thead>
        <tbody>{p_rows}</tbody>
      </table>
    </div>

    <!-- Detailed Area Sections -->
    {area_sections}

  </div>
</div>

<div class="footer">
  LLM-backed analysis using DMR_CBB + NWP Co-Design spec sources &nbsp;|&nbsp; NWP PM Test Plan Repo &nbsp;|&nbsp; 2026-07-15
</div>

</body>
</html>"""

if __name__ == "__main__":
    html = generate_html()
    out = pathlib.Path("tcd_description_output/CCF_PM_HAS_Coverage_Gap_Report.html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Written: {out} ({out.stat().st_size:,} bytes)")
    s = get_stats()
    print(f"Flows: {s['total']} total | {s['covered']} covered | {s['partial']} partial | {s['tcd_no_tc']} TCD/no-TC | {s['gap']} gaps")

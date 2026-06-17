"""
read_pstate_cstate.py — Read P-State and C-State registers from live NWP Simics session.

Register paths extracted from actual test scripts in:
  diamondrapids/pm/Active_PM/Pstate_Stack/

Key namednodes hierarchy (verified on NWP 2026ww23):
  CBB:  sv.socket0.cbb{0,1}.base.tpmi.*
        sv.socket0.cbb{0,1}.compute{0-3}.cpu.module{0-N}.core{0-N}.thread0.msr(addr)
  IMH0: sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*
        sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.*

MSR constants (from hwp.py):
  0x770  MSR_PM_ENABLE           — HWP enable
  0x774  MSR_IA32_HWP_REQUEST    — HWP per-core request (min/max/desired/EPP)
  0x772  MSR_IA32_HWP_REQUEST_PKG — HWP package-level request
  0x775  MSR_IA32_HWP_PECI_REQUEST — HWP PECI request
  0x1A0  MSR_IA32_MISC_ENABLES   — misc enables (turbo, C1E, etc.)
  0xCE   MSR_PLATFORM_INFO       — max/min non-turbo ratio, fused values
  0x1AD  MSR_TURBO_RATIO_LIMIT   — turbo ratio limits per core count
  0x19C  IA32_THERM_STATUS       — per-core thermal status
  0x198  IA32_PERF_STATUS        — current resolved P-state
  0x199  IA32_PERF_CTL           — P-state request (legacy)

PLR high-level clipping reasons (from high_level_PLR.py):
  bit 0  FREQUENCY       bit 1  CURRENT        bit 2  POWER
  bit 3  THERMAL         bit 4  PLATFORM       bit 5  MCP
  bit 6  RAS             bit 7  MISC           bit 8  QOS
  bit 9  DFC/SIMPL

PLR fine-level clipping reasons (from fine_level_PLR.py):
  bit 0-5  CDYN0-5       bit 6  FCT            bit 7  PCS_TRL
  bit 8  MTPMAX          bit 9  RACL           bit 10 FAST_RAPL
  bit 11 PKG_PL1_CSR     bit 12 PKG_PL1_TPMI   bit 13 PKG_PL2_CSR
  bit 14 PKG_PL2_TPMI    bit 19 PER_CORE_THERMAL  bit 21 XXPROCHOT
  bit 22 HOT_VR          bit 23 MCP            bit 24 RAS

Run with:
  python read_pstate_cstate.py
  python read_pstate_cstate.py --refresh

Requires SSH tunnel on port 4444 and simics_connect.py in the same folder.
"""

import sys
from simics_connect import connect, send_cmd, close


# ---------------------------------------------------------------------------
# P-State reads
# ---------------------------------------------------------------------------

def read_platform_info(s):
    """MSR 0xCE — max non-turbo ratio, min ratio (fused)."""
    print("\n[P-State] MSR_PLATFORM_INFO (0xCE) — max/min non-turbo ratio")
    r = send_cmd(s, "@sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0xCE)")
    print(r.strip())


def read_perf_status(s):
    """MSR 0x198 — current resolved P-state."""
    print("\n[P-State] IA32_PERF_STATUS (0x198) — current resolved freq ratio")
    for cbb in ["cbb0", "cbb1"]:
        r = send_cmd(s, f"@sv.socket0.{cbb}.compute0.cpu.module0.core0.thread0.msr(0x198)")
        print(f"  [{cbb} core0]: {r.strip()}")


def read_perf_ctl(s):
    """MSR 0x199 — legacy P-state request."""
    print("\n[P-State] IA32_PERF_CTL (0x199) — legacy P-state request")
    for cbb in ["cbb0", "cbb1"]:
        r = send_cmd(s, f"@sv.socket0.{cbb}.compute0.cpu.module0.core0.thread0.msr(0x199)")
        print(f"  [{cbb} core0]: {r.strip()}")


def read_hwp_enable(s):
    """MSR 0x770 — HWP enable status."""
    print("\n[P-State] MSR_PM_ENABLE (0x770) — HWP enable")
    r = send_cmd(s, "@sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x770)")
    print(r.strip())


def read_hwp_request(s):
    """MSR 0x774 — per-core HWP request (min/max/desired/EPP)."""
    print("\n[P-State] IA32_HWP_REQUEST (0x774) — per-core min/max/desired/EPP")
    for cbb in ["cbb0", "cbb1"]:
        r = send_cmd(s, f"@sv.socket0.{cbb}.compute0.cpu.module0.core0.thread0.msr(0x774)")
        print(f"  [{cbb} core0]: {r.strip()}")


def read_hwp_request_pkg(s):
    """MSR 0x772 — package-level HWP request."""
    print("\n[P-State] IA32_HWP_REQUEST_PKG (0x772) — package HWP request")
    r = send_cmd(s, "@sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x772)")
    print(r.strip())


def read_turbo_ratio_limit(s):
    """MSR 0x1AD — turbo ratio limits per active core count."""
    print("\n[P-State] MSR_TURBO_RATIO_LIMIT (0x1AD)")
    r = send_cmd(s, "@sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x1AD)")
    print(r.strip())


def read_misc_enables(s):
    """MSR 0x1A0 — IDA/turbo disable, C1E enable bits."""
    print("\n[P-State] IA32_MISC_ENABLES (0x1A0) — turbo/C1E enable")
    r = send_cmd(s, "@sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x1A0)")
    print(r.strip())


# ---------------------------------------------------------------------------
# C-State reads
# ---------------------------------------------------------------------------

def read_therm_status(s):
    """MSR 0x19C — per-core thermal/throttle status."""
    print("\n[C-State/Thermal] IA32_THERM_STATUS (0x19C) — thermal status + prochot")
    for cbb in ["cbb0", "cbb1"]:
        r = send_cmd(s, f"@sv.socket0.{cbb}.compute0.cpu.module0.core0.thread0.msr(0x19C)")
        print(f"  [{cbb} core0]: {r.strip()}")


def read_acp_perf_limit(s):
    """ACP performance limit reasons — CBB PMSB and IMH0 PMSB."""
    print("\n[P-State/Throttle] ACP Performance Limit (acp_perf_limit)")
    for cbb in ["cbb0", "cbb1"]:
        r = send_cmd(s, f"@sv.socket0.{cbb}.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()")
        print(f"  [{cbb}]: {r.strip()}")
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.acp_perf_limit.read()")
    print(f"  [imh0]: {r.strip()}")


def read_plr_high_level(s):
    """PLR high-level clipping reasons via mailbox (IMH PMSB + CBB TPMI)."""
    print("\n[P-State/PLR] High-Level Perf Limit Reasons (PLR mailbox)")
    # IMH: write command=0, domain=2, run_busy=1, read result
    cmds_imh = [
        "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.command.write(0)",
        "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.domain.write(2)",
        "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.run_busy.write(1)",
    ]
    for c in cmds_imh:
        send_cmd(s, c, wait=1)
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_data.read()")
    print(f"  [IMH0 PLR mailbox data]: {r.strip()}")

    # CBB0: command=0, domain=2, run_busy=1
    cmds_cbb = [
        "@sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.command.write(0)",
        "@sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.domain.write(2)",
        "@sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.run_busy.write(1)",
    ]
    for c in cmds_cbb:
        send_cmd(s, c, wait=1)
    r = send_cmd(s, "@sv.socket0.cbb0.base.tpmi.plr_mailbox_data.read()")
    print(f"  [CBB0 PLR mailbox data]: {r.strip()}")


def read_core_pm_event(s):
    """IMH0 core PM events (PMSB)."""
    print("\n[C-State] Core PM Event (IMH0)")
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_pm_event.read()")
    print(r.strip())


def read_core_electrical_req(s):
    """IMH0 core electrical request (PMSB)."""
    print("\n[P-State] Core Electrical Request (IMH0)")
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_electrical_req.read()")
    print(r.strip())


def read_uncore_telem(s):
    """IMH0 uncore telemetry (PMSB)."""
    print("\n[Telemetry] Uncore Telemetry (IMH0)")
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_telem.read()")
    print(r.strip())


# ---------------------------------------------------------------------------
# All-in-one
# ---------------------------------------------------------------------------

def read_all_pstate(s):
    read_platform_info(s)
    read_perf_status(s)
    read_perf_ctl(s)
    read_hwp_enable(s)
    read_hwp_request(s)
    read_hwp_request_pkg(s)
    read_turbo_ratio_limit(s)
    read_misc_enables(s)
    read_acp_perf_limit(s)
    read_core_electrical_req(s)


def read_all_cstate(s):
    read_therm_status(s)
    read_core_pm_event(s)
    read_acp_perf_limit(s)
    read_plr_high_level(s)


def read_all(s):
    print("\n" + "=" * 70)
    print("  NWP P-State Registers")
    print("=" * 70)
    read_all_pstate(s)

    print("\n" + "=" * 70)
    print("  NWP C-State / Throttle Registers")
    print("=" * 70)
    read_all_cstate(s)
    read_uncore_telem(s)


if __name__ == "__main__":
    do_refresh = "--refresh" in sys.argv

    s = connect()
    print("Connected to Simics CLI")

    if do_refresh:
        from simics_connect import refresh
        refresh(s)

    read_all(s)
    close(s)

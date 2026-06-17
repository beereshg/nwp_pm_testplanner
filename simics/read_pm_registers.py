"""
read_pm_registers.py — Read NWP Power Management registers from live Simics session.

Verified working paths (discovered 2026-06-10 on nwp-7/2026ww23.6.00_47):

CBB registers:   sv.socket0.cbb{0,1}.base.punit_regs.punit_pmsb.pmsb_pcu.<reg>
IMH0 registers:  sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.<reg>

Available CBB pmsb_pcu PM registers:
  acp_perf_limit        — ACP coarse-grain perf limiter reasons (per FID, read-clears)

Available IMH0 ptpcfsms_pmsb PM registers:
  acp_perf_limit        — ACP perf limit (fid_0 only on IMH)
  core_pm_event         — Core PM events
  uncore_virtual_sig    — Uncore virtual signal
  uncore_telem          — Uncore telemetry
  core_electrical_req   — Core electrical request

Run with:
  python read_pm_registers.py [--refresh]

Requires:
  - SSH tunnel: ssh -L 4444:localhost:4444 -N -o PreferredAuthentications=keyboard-interactive bg3@10.116.33.137
  - Simics running with telnet-frontend port=4444
"""

import sys
import time
from simics_connect import connect, send_cmd, close

def read_acp_perf_limit(s):
    print("=" * 60)
    print("ACP Performance Limit Registers")
    print("=" * 60)

    for cbb in ["cbb0", "cbb1"]:
        r = send_cmd(s, f"@sv.socket0.{cbb}.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()")
        print(f"\n[{cbb.upper()}] acp_perf_limit:")
        print(r.strip())

    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.acp_perf_limit.read()")
    print("\n[IMH0] acp_perf_limit:")
    print(r.strip())


def read_core_pm_events(s):
    print("\n" + "=" * 60)
    print("Core PM Events (IMH0)")
    print("=" * 60)
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_pm_event.read()")
    print(r.strip())


def read_core_electrical_req(s):
    print("\n" + "=" * 60)
    print("Core Electrical Request (IMH0)")
    print("=" * 60)
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_electrical_req.read()")
    print(r.strip())


def read_uncore_telem(s):
    print("\n" + "=" * 60)
    print("Uncore Telemetry (IMH0)")
    print("=" * 60)
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_telem.read()")
    print(r.strip())


def read_uncore_virtual_sig(s):
    print("\n" + "=" * 60)
    print("Uncore Virtual Signal (IMH0)")
    print("=" * 60)
    r = send_cmd(s, "@sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_virtual_sig.read()")
    print(r.strip())


def read_all(s):
    read_acp_perf_limit(s)
    read_core_pm_events(s)
    read_core_electrical_req(s)
    read_uncore_telem(s)
    read_uncore_virtual_sig(s)


if __name__ == "__main__":
    do_refresh = "--refresh" in sys.argv

    s = connect()
    print("Connected to Simics CLI")

    if do_refresh:
        print("Running sv.refresh() ...")
        r = send_cmd(s, "@sv.refresh()", wait=15)
        print(r)

    read_all(s)
    close(s)

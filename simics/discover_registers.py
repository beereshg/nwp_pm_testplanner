"""
discover_registers.py — Discover available registers under any namednodes path in NWP Simics.

Usage:
  python discover_registers.py
  python discover_registers.py --path "sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu"
  python discover_registers.py --search "perf"

Requires SSH tunnel on port 4444.
"""

import sys
from simics_connect import connect, send_cmd, close


def list_registers(s, path, keyword=None):
    """List all register names under a namednodes path, optionally filtered by keyword."""
    if keyword:
        cmd = f'@print([r for r in {path}.registers if "{keyword}" in r.lower()])'
    else:
        cmd = f"@print(list({path}.registers))"
    r = send_cmd(s, cmd, wait=4)
    print(f"\nRegisters under {path}:")
    print(r.strip())


def list_nodenames(s, path):
    """List sub-nodes under a namednodes path."""
    cmd = f"@print({path}.nodenames)"
    r = send_cmd(s, cmd, wait=3)
    print(f"\nSub-nodes under {path}:")
    print(r.strip())


def list_simics_objects(s, substr):
    """List Simics simulation objects matching a substring."""
    cmd = f"list-objects substr = {substr}"
    r = send_cmd(s, cmd, wait=4)
    print(f"\nSimics objects matching '{substr}':")
    print(r.strip())


def discover_all(s):
    """Full discovery of known NWP PM register paths."""
    paths = {
        "CBB0 pmsb_pcu":  "sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu",
        "CBB1 pmsb_pcu":  "sv.socket0.cbb1.base.punit_regs.punit_pmsb.pmsb_pcu",
        "IMH0 ptpcfsms":  "sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb",
    }
    for label, path in paths.items():
        print(f"\n{'='*60}")
        print(f"  {label}  ({path})")
        print(f"{'='*60}")
        list_registers(s, path)
        list_nodenames(s, path)

    print(f"\n{'='*60}")
    print("  Simics object hierarchy (punit objects)")
    print(f"{'='*60}")
    list_simics_objects(s, "punit")


if __name__ == "__main__":
    args = sys.argv[1:]
    s = connect()
    print("Connected to Simics CLI")

    if "--path" in args:
        idx = args.index("--path")
        path = args[idx + 1]
        kw = args[args.index("--search") + 1] if "--search" in args else None
        list_registers(s, path, kw)
        list_nodenames(s, path)
    else:
        discover_all(s)

    close(s)

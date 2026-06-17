"""
simics_cmd.py — One-shot Simics command runner. Send any CLI or @python command.

Usage:
  python simics_cmd.py "pwd"
  python simics_cmd.py "@sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()"
  python simics_cmd.py "@sv.refresh()" --wait 15
  python simics_cmd.py "list-objects substr = punit"
"""

import sys
from simics_connect import connect, send_cmd, close

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    cmd = args[0]
    wait = int(args[args.index("--wait") + 1]) if "--wait" in args else 3

    s = connect()
    r = send_cmd(s, cmd, wait=wait)
    print(r.strip())
    close(s)

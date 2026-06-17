"""
simics_connect.py — NWP Simics CLI connection helper via telnet-frontend tunnel.

Prerequisites:
  1. Simics running on server with telnet-frontend enabled:
       telnet-frontend port=4444         (type at Simics running> prompt)
  2. SSH tunnel active:
       ssh -L 4444:localhost:4444 -N -o PreferredAuthentications=keyboard-interactive bg3@10.116.33.137
  3. After sv.refresh() is done once, register paths are valid.

Server:    10.116.33.137
Project:   /nfs/site/disks/simcloud_bg3_001/projects/nwp-7/2026ww23.6.00_47
Simics:    PID 33355  (verify with: ssh bg3@10.116.33.137 "top -bn1 | grep simics")
"""

import socket
import time

SIMICS_HOST = "localhost"
SIMICS_PORT = 4444
DEFAULT_WAIT = 3  # seconds to wait for command output


def connect(host=SIMICS_HOST, port=SIMICS_PORT, timeout=5):
    """Connect to Simics telnet-frontend and drain the banner."""
    s = socket.create_connection((host, port), timeout)
    time.sleep(1)
    s.recv(4096)  # drain banner / prompt
    return s


def send_cmd(s, cmd, wait=DEFAULT_WAIT, buf=65536):
    """
    Send a CLI or @python command to Simics and return the response text.

    CLI command:    send_cmd(s, "pwd")
    Python command: send_cmd(s, "@sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()")
    """
    s.sendall((cmd + "\n").encode())
    time.sleep(wait)
    out = b""
    s.settimeout(1)
    try:
        while True:
            chunk = s.recv(buf)
            if not chunk:
                break
            out += chunk
    except socket.timeout:
        pass
    finally:
        s.settimeout(None)
    return out.decode(errors="replace").replace("\r\n", "\n")


def refresh(s):
    """Run sv.refresh() to initialize PythonSV namednodes."""
    print("Running sv.refresh() ...")
    r = send_cmd(s, "@sv.refresh()", wait=15)
    print(r)


def close(s):
    s.close()


if __name__ == "__main__":
    s = connect()
    print("Connected to Simics on", SIMICS_HOST, SIMICS_PORT)
    r = send_cmd(s, "pwd")
    print(r)
    close(s)

"""Check PEGA mailbox registers for TC 16030715604."""
import socket, time, re

def simics_cmd(s, cmd, wait=3):
    s.sendall((cmd + "\n").encode())
    time.sleep(wait)
    out = b""
    s.settimeout(1)
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk: break
            out += chunk
    except: pass
    s.settimeout(None)
    txt = out.decode(errors="replace").replace("\r\n", "\n")
    txt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", txt)
    return txt.strip()

def run(label, cmd, wait=3):
    r = simics_cmd(s, cmd, wait)
    lines = [l for l in r.splitlines() if l.strip() and "running>" not in l and not l.startswith(cmd[:15])]
    print(f"\n>>> {label}")
    print("\n".join(lines) if lines else "(empty)")

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

print("=" * 70)
print("TC 16030715604 — PEGA FabricGV Register Discovery")
print("=" * 70)

# Find PEGA-related registers in CBB TPMI
run("CBB TPMI registers with 'pega' in name",
    "@print([r for r in sv.socket0.cbb0.base.tpmi.registers if 'pega' in r.lower()])")
run("CBB TPMI registers with 'power_event' or 'mesh' in name",
    "@print([r for r in sv.socket0.cbb0.base.tpmi.registers if 'power_event' in r.lower() or 'mesh' in r.lower() or 'mbox' in r.lower()])")

# Check OS mailbox (PEGA uses OS mailbox path)
run("OS mailbox interface CBB0 (PEGA injection path)",
    "@sv.socket0.cbb0.base.tpmi.os_mailbox_interface.read()")
run("OS mailbox data CBB0",
    "@sv.socket0.cbb0.base.tpmi.os_mailbox_data.read()")
run("OS mailbox interface CBB1",
    "@sv.socket0.cbb1.base.tpmi.os_mailbox_interface.read()")

# Check aux mailbox (alternate PEGA path)
run("Aux mailbox interface CBB0",
    "@sv.socket0.cbb0.base.tpmi.aux_mailbox_interface.read()")
run("Aux mailbox data CBB0",
    "@sv.socket0.cbb0.base.tpmi.aux_mailbox_data.read()")

# UFS status before/baseline
run("UFS_STATUS CBB0 (current freq — baseline)",
    "@sv.socket0.cbb0.base.tpmi.ufs_status.read()")
run("UFS_STATUS CBB0 current_ratio field",
    "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
run("UFS_STATUS CBB1 current_ratio field",
    "@sv.socket0.cbb1.base.tpmi.ufs_status.current_ratio.read()")

# Check PEGA via IMH FSMS (for PEGA XTor path on IMH)
run("IMH0 FSMS registers with 'pega' or 'event'",
    "@print([r for r in sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.registers if 'pega' in r.lower() or 'event' in r.lower()])")

s.close()

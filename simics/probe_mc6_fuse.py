"""Probe MC6 fuse-related registers via Simics telnet bridge."""
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
    return out.decode(errors="replace").replace("\r\n", "\n").strip()

def read(s, label, cmd, wait=2):
    r = simics_cmd(s, cmd, wait)
    lines = [l for l in r.splitlines() if l.strip() and "running>" not in l and not l.startswith(cmd[:12])]
    val = "\n".join(lines).strip()
    print(f"  {label}: {val[:200]}")
    return val

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

print("=" * 70)
print("MC6 Fuse Probe — NWP CBB")
print("=" * 70)

# Search for mc6-related fuse/config registers on CBB base
read(s, "CBB0 registers with mc6/module/ring_c6",
     "@[r for r in sv.socket0.cbb0.base.registers if any(x in r.lower() for x in ['mc6','ring_c6','module_c6','fused_mc6','module_cstate'])]")

# Check DFX control for module c-state limit
read(s, "dfx_ctrl_unprotected full",
     "@sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.dfx_ctrl_unprotected.show()")

# Check PUNIT fuse registers
read(s, "CBB0 punit fuse registers with cstate/mc6",
     "@[r for r in sv.socket0.cbb0.base.punit_regs.registers if any(x in r.lower() for x in ['mc6','module_c6','cstate_limit','fused_core','ring_c6'])]")

# Specific known fuse paths on CBB
for reg in [
    "sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.dfx_ctrl_unprotected.core_cstate_limit",
    "sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.dfx_ctrl_unprotected.ring_cstate_limit",
    "sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.dfx_ctrl_unprotected.module_cstate_limit",
    "sv.socket0.cbb0.base.punit_regs.fuse_regs.fused_core_c_state_limit",
    "sv.socket0.cbb0.base.punit_regs.fuse_regs.fused_module_c_state_limit",
    "sv.socket0.cbb0.base.punit_regs.fuse_regs.fused_ring_c_state_limit",
]:
    short = reg.split(".")[-1]
    read(s, short,
         f"@getattr({reg.rsplit('.',1)[0]}, '{short}', 'N/A') if hasattr({reg.rsplit('.',1)[0]}, '{short}') else 'not found'")

# MC6 counter MSR
read(s, "CBB0 MC6 residency MSR 0x664",
     "@sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x664)")

# Check if there is an MC6-specific fuse in TPMI
read(s, "CBB0 TPMI registers with mc6/module",
     "@[r for r in sv.socket0.cbb0.base.tpmi.registers if any(x in r.lower() for x in ['mc6','module_c6','ring_c6'])]")

s.close()
print("\nDone.")

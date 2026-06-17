"""Decode UFS_CONTROL fields for TC 16030715600 pass/fail verification."""
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
    print("\n".join(lines))

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

print("=" * 70)
print("TC 16030715600 — UFS_CONTROL Field Decode (NWP CBB only, IMH ZBB)")
print("=" * 70)

# ── Criterion 1: Default MIN_RATIO / MAX_RATIO from fuses ──────────────────
print("\n[Criterion 1] Default MIN_RATIO / MAX_RATIO — should come from fuses")
run("CBB0 ufs_control raw", "@sv.socket0.cbb0.base.tpmi.ufs_control.read()")
run("CBB0 ufs_throttle_mode [1:0]",  "@sv.socket0.cbb0.base.tpmi.ufs_control.ufs_throttle_mode.read()")
run("CBB0 max_ratio [14:8]",         "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
run("CBB0 min_ratio [21:15]",        "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")
run("CBB0 efficiency_latency_ctrl_ratio [28:22]", "@sv.socket0.cbb0.base.tpmi.ufs_control.efficiency_latency_ctrl_ratio.read()")
run("CBB1 ufs_control raw", "@sv.socket0.cbb1.base.tpmi.ufs_control.read()")
run("CBB1 max_ratio [14:8]",         "@sv.socket0.cbb1.base.tpmi.ufs_control.max_ratio.read()")
run("CBB1 min_ratio [21:15]",        "@sv.socket0.cbb1.base.tpmi.ufs_control.min_ratio.read()")

# ── Criterion 2: CBB fabric_1 should be different / not programmed ─────────
print("\n[Criterion 2] CBB fabric_1 — verify different from fabric_0")
run("CBB0 ufs_control_fabric_1 raw",             "@sv.socket0.cbb0.base.tpmi.ufs_control_fabric_1.read()")
run("CBB0 ufs_control_fabric_1 max_ratio",       "@sv.socket0.cbb0.base.tpmi.ufs_control_fabric_1.max_ratio.read()")
run("CBB0 ufs_control_fabric_1 min_ratio",       "@sv.socket0.cbb0.base.tpmi.ufs_control_fabric_1.min_ratio.read()")
run("CBB0 ufs_control_fabric_1 ufs_throttle_mode", "@sv.socket0.cbb0.base.tpmi.ufs_control_fabric_1.ufs_throttle_mode.read()")

# ── Criterion 3: IMH UFS — ZBB, expect 0x0 or inaccessible ───────────────
print("\n[Criterion 3] IMH UFS — ZBB (Memory and IO fabrics)")
run("IMH0 ufs_control raw (Memory fabric)",       "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control.read()")
run("IMH0 ufs_control_fabric_1 raw (IO fabric)",  "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_control_fabric_1.read()")

# ── Criterion 4: TPMI Lock status ─────────────────────────────────────────
print("\n[Criterion 4] TPMI Lock state")
run("CBB0 tpmi_info_header (contains LOCK bit)", "@sv.socket0.cbb0.base.tpmi.tpmi_info_header.read()")
run("CBB1 tpmi_info_header",                    "@sv.socket0.cbb1.base.tpmi.tpmi_info_header.read()")

# ── Criterion 5: Latency Optimized Mode fields ─────────────────────────────
print("\n[Criterion 5] Latency Optimized Mode — efficiency_latency_ctrl fields")
run("CBB0 efficiency_latency_ctrl_low_threshold",            "@sv.socket0.cbb0.base.tpmi.ufs_control.efficiency_latency_ctrl_low_threshold.read()")
run("CBB0 efficiency_latency_ctrl_high_threshold",           "@sv.socket0.cbb0.base.tpmi.ufs_control.efficiency_latency_ctrl_high_threshold.read()")
run("CBB0 efficiency_latency_ctrl_high_threshold_enable",    "@sv.socket0.cbb0.base.tpmi.ufs_control.efficiency_latency_ctrl_high_threshold_enable.read()")

# ── Criterion 6: Uniform CBB Fabric Mode ──────────────────────────────────
print("\n[Criterion 6] Uniform CBB Fabric Frequency Mode")
run("CBB0 uniform_cbb_fabric_mode",  "@sv.socket0.cbb0.base.tpmi.ufs_control.uniform_cbb_fabric_mode.read()")
run("CBB1 uniform_cbb_fabric_mode",  "@sv.socket0.cbb1.base.tpmi.ufs_control.uniform_cbb_fabric_mode.read()")

s.close()

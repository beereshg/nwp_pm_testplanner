"""
TC 16030715609 — Out of Boundary Frequency Check
Verify FW enforces fused limits for MeshGV on CBB (NWP: IMH fabrics are ZBB/static).

Test logic:
  1. Read fused P0 (max) and PM (min) from SST/fuse registers
  2. Write MAX_RATIO > P0 (e.g. 0x7F) → expect firmware clamps to P0
  3. Write MIN_RATIO < PM (e.g. 0x01) → expect firmware clamps to PM
  4. Write both out of bounds → verify current_ratio stays within [PM, P0]
  5. Restore defaults

NWP delta: IMH Memory and IO fabrics are ZBB — static at 0x4 and 0x8 respectively.
"""
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

def read(s, label, cmd, wait=3):
    r = simics_cmd(s, cmd, wait)
    lines = [l for l in r.splitlines() if l.strip() and "running>" not in l
             and not l.startswith(cmd[:12])]
    val = "\n".join(lines).strip()
    print(f"  {label}: {val[:100]}")
    return val

def hex_val(v):
    try:
        return int(v.split("0x")[-1].split("\n")[0], 16) if "0x" in v else int(v)
    except: return None

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

print("=" * 70)
print("TC 16030715609 — Out of Boundary Frequency Check (CBB only, NWP)")
print("=" * 70)

# ── Step 1: Read fused limits from SST_PP_INFO_11 and UFS_CONTROL ──────────
print("\n[Step 1] Read fused P0/PM limits")
p0_raw = read(s, "CBB0 SST_PP_INFO_11 (P0/P1/Pm encoded)", "@sv.socket0.cbb0.base.tpmi.sst_pp_info_11.read()")
p0_field = read(s, "CBB0 SST_PP_INFO_11.p0_core_ratio",   "@sv.socket0.cbb0.base.tpmi.sst_pp_info_11.p0_core_ratio.read()")
p1_field = read(s, "CBB0 SST_PP_INFO_11.p1_core_ratio",   "@sv.socket0.cbb0.base.tpmi.sst_pp_info_11.p1_core_ratio.read()")
pm_field = read(s, "CBB0 SST_PP_INFO_11.pm_core_ratio",   "@sv.socket0.cbb0.base.tpmi.sst_pp_info_11.pm_core_ratio.read()")

max_r = read(s, "CBB0 ufs_control.max_ratio (current)", "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
min_r = read(s, "CBB0 ufs_control.min_ratio (current)", "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")
curr  = read(s, "CBB0 ufs_status.current_ratio (BASELINE)", "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")

ORIG_MAX = hex_val(max_r) or 0x1b
ORIG_MIN = hex_val(min_r) or 0x04
P0 = hex_val(p0_field) or ORIG_MAX
PM = hex_val(pm_field) or ORIG_MIN
print(f"\n  Fused limits: P0={P0:#x} ({P0*100}MHz)  PM={PM:#x} ({PM*100}MHz)")
print(f"  Current MAX={ORIG_MAX:#x}  MIN={ORIG_MIN:#x}  CURRENT_RATIO={hex_val(curr):#x}")

# ── Step 2: IMH baseline (static, should never change) ────────────────────
print("\n[Step 2] IMH baseline — expect static throughout")
imh_mem = read(s, "IMH0 Memory ufs_status.current_ratio", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio.read()")
imh_io  = read(s, "IMH0 IO ufs_status_fabric_1.current_ratio", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio.read()")

# ── Step 3: Write ABOVE P0 (should be clamped to P0) ──────────────────────
ABOVE_P0 = 0x7F
print(f"\n[Step 3] Write MAX=MIN={ABOVE_P0:#x} (ABOVE P0={P0:#x}) — expect clamp to P0")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{ABOVE_P0:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{ABOVE_P0:x})", wait=1)
time.sleep(4)
r_above = read(s, f"CBB0 ufs_status.current_ratio (expected <= P0={P0:#x})",
               "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
r_above_ctrl_max = read(s, "CBB0 ufs_control.max_ratio (register after write)",
                        "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
v = hex_val(r_above)
if v is not None:
    print(f"  --> RESULT: current_ratio=0x{v:x} | P0={P0:#x} | {'CLAMPED OK' if v <= P0 else 'NOT CLAMPED'}")

# ── Step 4: Write BELOW PM (should be clamped to PM) ──────────────────────
BELOW_PM = 0x01
print(f"\n[Step 4] Write MAX=MIN={BELOW_PM:#x} (BELOW PM={PM:#x}) — expect clamp to PM")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{BELOW_PM:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{BELOW_PM:x})", wait=1)
time.sleep(4)
r_below = read(s, f"CBB0 ufs_status.current_ratio (expected >= PM={PM:#x})",
               "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
v2 = hex_val(r_below)
if v2 is not None:
    print(f"  --> RESULT: current_ratio=0x{v2:x} | PM={PM:#x} | {'CLAMPED OK' if v2 >= PM else 'NOT CLAMPED'}")

# ── Step 5: Write inverted (MAX < MIN) ────────────────────────────────────
print(f"\n[Step 5] Write inverted MAX < MIN (invalid): MAX=0x04, MIN=0x20")
simics_cmd(s, "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x4)", wait=1)
simics_cmd(s, "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x20)", wait=1)
time.sleep(4)
r_inv = read(s, "CBB0 ufs_status.current_ratio (inverted MAX<MIN)",
             "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
read(s, "CBB0 ufs_control.max_ratio after inverted write", "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
read(s, "CBB0 ufs_control.min_ratio after inverted write", "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")

# ── Step 6: Restore defaults ───────────────────────────────────────────────
print(f"\n[Step 6] Restore defaults MAX={ORIG_MAX:#x}, MIN={ORIG_MIN:#x}")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{ORIG_MAX:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{ORIG_MIN:x})", wait=1)
time.sleep(3)
read(s, "CBB0 ufs_status.current_ratio (RESTORED)", "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
read(s, "CBB0 ufs_control.max_ratio (RESTORED)", "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
read(s, "CBB0 ufs_control.min_ratio (RESTORED)", "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")

# ── Step 7: Verify IMH static throughout ─────────────────────────────────
print("\n[Step 7] Verify IMH static after all CBB writes (ZBB — should be unchanged)")
imh_mem2 = read(s, "IMH0 Memory current_ratio (should still be same)", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio.read()")
imh_io2  = read(s, "IMH0 IO current_ratio (should still be same)", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio.read()")
mem_ok = (imh_mem == imh_mem2)
io_ok  = (imh_io == imh_io2)
print(f"  IMH Memory unchanged: {'PASS' if mem_ok else 'FAIL'} ({imh_mem} -> {imh_mem2})")
print(f"  IMH IO unchanged: {'PASS' if io_ok else 'FAIL'} ({imh_io} -> {imh_io2})")

s.close()
print("\n=== Done ===")

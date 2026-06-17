"""
TC 16030715604 — PEGA FabricGV injection via correct 3-step ucode-pcode mailbox sequence.

PEGA CBB CLR/Mesh GV injection protocol (from pega_register_classes.py):
  CMD1W (0x24): data register bits[23:16] = ring_ratio (target mesh freq ratio)
  CMD2W (0x26): data register bits[4:0]   = pp_mask = 0x4 (CLR GV domain enabled)
  CMD0W (0x22): data register bit[31]=1 (run_busy), bits[30:28]=0x2 (P-state command)

  Interface register encoding (commandInterface_cbb):
    bit[31]  = run_busy
    bits[7:0] = command opcode

Mailbox registers (per CBB die, FID = compute0.instance * 8 % 256):
  ucode_pcode_mailbox_data["fid_N"]      ← data
  ucode_pcode_mailbox_interface["fid_N"] ← interface/trigger
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

def run(label, cmd, wait=3):
    r = simics_cmd(s, cmd, wait)
    lines = [l for l in r.splitlines() if l.strip() and "running>" not in l
             and not l.startswith(cmd[:12])]
    val = "\n".join(lines)
    print(f"\n  [{label}]\n  {val[:300]}")
    return val

def inject_cbb_clrgv(s, cbb, ratio_hex, wait_busy=2):
    """Inject PEGA P-state CLR/Mesh GV on one CBB using correct 3-step mailbox sequence."""
    base = f"sv.socket0.{cbb}.base.punit_regs.punit_gpsb.gpsb_infvnn_crs"

    # Determine FID dynamically
    fid_code = f"(sv.socket0.{cbb}.compute0.instance * 8) % 256"
    fid_resp = simics_cmd(s, f"@print({fid_code})", wait=2)
    fid_lines = [l for l in fid_resp.splitlines() if l.strip().isdigit()]
    fid = int(fid_lines[0]) if fid_lines else 0
    data_reg  = f'{base}.ucode_pcode_mailbox_data["fid_{fid}"]'
    iface_reg = f'{base}.ucode_pcode_mailbox_interface["fid_{fid}"]'
    print(f"    FID={fid}  data_reg fid_{fid}")

    # ── CMD1W (0x24): ring_ratio at bits[23:16] ──────────────────────────
    cmd1_data = ratio_hex << 16
    simics_cmd(s, f"@{data_reg}.write(0x{cmd1_data:08x})", wait=1)
    # interface: run_busy=bit[31], command=bits[7:0]=0x24
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x24:08x})", wait=wait_busy)

    # ── CMD2W (0x26): pp_mask at bits[4:0] = 0x4 (CLR GV domain) ────────
    simics_cmd(s, f"@{data_reg}.write(0x04)", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x26:08x})", wait=wait_busy)

    # ── CMD0W (0x22): commandType=0x2 (P-state) bits[30:28], run_busy bit[31] ─
    cmd0_data = (1 << 31) | (0x2 << 28)   # = 0xa0000000
    simics_cmd(s, f"@{data_reg}.write(0x{cmd0_data:08x})", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x22:08x})", wait=wait_busy)

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

# Target CLR/Mesh GV ratio — 0x1b = 2.7 GHz, 0x14 = 2.0 GHz, 0x1e = 3.0 GHz
TARGET_RATIO = 0x14   # inject to 2.0 GHz to force a visible change from baseline 0x1b

print("=" * 70)
print(f"TC 16030715604 — PEGA FabricGV Injection (target ratio=0x{TARGET_RATIO:02x})")
print("=" * 70)

# ── Step 0: Try high-level pega library (now fixed) ───────────────────────
print("\n[0] Attempt via newport.pm.pmutils.pega library (high-level API)")
run("import pega",
    "@import newport.pm.pmutils.pega as pega; print('pega imported OK, pegaPstate available:', hasattr(pega,'pegaPstate'))",
    wait=5)
run("pegaPstate clrgv injection",
    f"@import newport.pm.pmutils.pega as pega; pega.pegaPstate(sktNum=0, dieName='cbb0', clrgv=0x{TARGET_RATIO:02x}); print('done')",
    wait=8)
run("CBB0 ufs_status after high-level pega",
    "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")

# ── Step 1: Baselines ─────────────────────────────────────────────────────
print("\n[1] Baselines")
run("CBB0 ufs_status.current_ratio", "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
run("CBB1 ufs_status.current_ratio", "@sv.socket0.cbb1.base.tpmi.ufs_status.current_ratio.read()")
run("CBB0 ufs_control",              "@sv.socket0.cbb0.base.tpmi.ufs_control.read()")

# ── Step 2: CBB0 direct mailbox injection with correct opcodes ───────────
print(f"\n[2] CBB0 CLR/Mesh GV — direct 3-step mailbox injection (ratio=0x{TARGET_RATIO:02x})")
inject_cbb_clrgv(s, "cbb0", TARGET_RATIO)
run("CBB0 ufs_status.current_ratio AFTER", "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
run("CBB0 ufs_status full",                "@sv.socket0.cbb0.base.tpmi.ufs_status.read()")

# ── Step 3: CBB1 direct mailbox injection ────────────────────────────────
print(f"\n[3] CBB1 CLR/Mesh GV — direct 3-step mailbox injection (ratio=0x{TARGET_RATIO:02x})")
inject_cbb_clrgv(s, "cbb1", TARGET_RATIO)
run("CBB1 ufs_status.current_ratio AFTER", "@sv.socket0.cbb1.base.tpmi.ufs_status.current_ratio.read()")

# ── Step 4: IMH ZBB confirmation (expected: no change) ───────────────────
print("\n[4] IMH ZBB confirmation (no injection expected)")
run("IMH0 ufs_status", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.read()")
run("IMH0 ufs_status_fabric_1", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.read()")

s.close()
print("\nDone.")

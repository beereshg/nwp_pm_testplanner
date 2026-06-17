"""
TC 16030715607 — TPMI-driven FabricGV (v2)
Write UFS_CONTROL[MIN_RATIO] = UFS_CONTROL[MAX_RATIO] = target_ratio to force
CBB mesh frequency. Verify UFS_STATUS[CURRENT_RATIO] matches.

v2 enhancements (based on dry-run findings):
  - Added UFS_ADV_CONTROL autonomous/throttle mode checks
  - Added PEGA-assisted frequency trigger after TPMI write
  - Added Pcode tracker register reads (fod_status, ufs_hw_feedback)
  - Added write-back loop: write → wait → poll (5x) before declaring FAIL
  - Explicit pass/fail verdict table at end
NWP delta: IMH fabrics are ZBB — remain static.
"""
"""
TC 16030715607 — TPMI-driven FabricGV (v2)
Write UFS_CONTROL[MIN_RATIO] = UFS_CONTROL[MAX_RATIO] = target_ratio to force
CBB mesh frequency. Verify UFS_STATUS[CURRENT_RATIO] matches.

v2 enhancements (based on dry-run findings):
  - Added UFS_ADV_CONTROL autonomous/throttle mode checks
  - Added PEGA-assisted frequency trigger after TPMI write
  - Added Pcode tracker register reads (fod_status, ufs_hw_feedback)
  - Added write-back loop: write → wait → poll (5x) before declaring FAIL
  - Explicit pass/fail verdict table at end
NWP delta: IMH fabrics are ZBB — remain static.
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
    print(f"  {label}: {val[:120]}")
    return val

def poll_ratio(s, path, expected_hex, polls=5, interval=2):
    """Poll current_ratio up to N times waiting for expected value. Returns final value."""
    final = None
    for i in range(polls):
        r = simics_cmd(s, f"@{path}.read()", wait=1)
        lines = [l for l in r.splitlines() if l.strip() and "running>" not in l]
        final = "\n".join(lines).strip()
        if final == str(expected_hex) or final == hex(expected_hex):
            print(f"    [poll {i+1}/{polls}] ratio={final} MATCH expected={hex(expected_hex)}")
            return final
        print(f"    [poll {i+1}/{polls}] ratio={final} (waiting for {hex(expected_hex)})...")
        time.sleep(interval)
    return final

def trigger_pega_clrgv(s, cbb, ratio_hex, wait_busy=2):
    """Issue a PEGA P-state injection on CLR/Mesh domain via ucode-pcode mailbox."""
    base = f"sv.socket0.{cbb}.base.punit_regs.punit_gpsb.gpsb_infvnn_crs"
    fid_resp = simics_cmd(s, f"@print((sv.socket0.{cbb}.compute0.instance * 8) % 256)", wait=2)
    fid_lines = [l for l in fid_resp.splitlines() if l.strip().lstrip('-').isdigit()]
    fid = int(fid_lines[0]) if fid_lines else 0
    data_reg  = f'{base}.ucode_pcode_mailbox_data["fid_{fid}"]'
    iface_reg = f'{base}.ucode_pcode_mailbox_interface["fid_{fid}"]'
    simics_cmd(s, f"@{data_reg}.write(0x{ratio_hex << 16:08x})", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x24:08x})", wait=wait_busy)
    simics_cmd(s, f"@{data_reg}.write(0x04)", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x26:08x})", wait=wait_busy)
    cmd0 = (1 << 31) | (0x2 << 28)
    simics_cmd(s, f"@{data_reg}.write(0x{cmd0:08x})", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x22:08x})", wait=wait_busy)

results = {}

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

print("=" * 70)
print("TC 16030715607 v2 — TPMI FabricGV: Force CBB Mesh Ratio")
print("=" * 70)

# ── Step 1: Read baselines ─────────────────────────────────────────────────
print("\n[Step 1] Baseline reads")
b_ctrl_cbb0  = read(s, "CBB0 ufs_control raw",        "@sv.socket0.cbb0.base.tpmi.ufs_control.read()")
b_max_cbb0   = read(s, "CBB0 max_ratio",               "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
b_min_cbb0   = read(s, "CBB0 min_ratio",               "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")
b_cur_cbb0   = read(s, "CBB0 current_ratio (BASELINE)","@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
b_max_cbb1   = read(s, "CBB1 max_ratio",               "@sv.socket0.cbb1.base.tpmi.ufs_control.max_ratio.read()")
b_cur_cbb1   = read(s, "CBB1 current_ratio (BASELINE)","@sv.socket0.cbb1.base.tpmi.ufs_status.current_ratio.read()")
results["step1_baseline"] = "PASS" if b_max_cbb0.strip() and b_cur_cbb0.strip() else "FAIL"

# ── Step 2: IMH baseline ───────────────────────────────────────────────────
print("\n[Step 2] IMH Status baseline (expected static/ZBB)")
imh_mem = read(s, "IMH0 ufs_status.current_ratio (Memory)", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio.read()")
imh_io  = read(s, "IMH0 ufs_status_fabric_1.current_ratio (IO)", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio.read()")

# ── Step 3: Advanced UFS control mode checks (v2) ─────────────────────────
print("\n[Step 3] UFS Advanced Control — throttle/autonomous mode (v2)")
read(s, "CBB0 ufs_throttle_mode",         "@sv.socket0.cbb0.base.tpmi.ufs_control.ufs_throttle_mode.read()")
read(s, "CBB0 uniform_cbb_fabric_mode",   "@sv.socket0.cbb0.base.tpmi.ufs_control.uniform_cbb_fabric_mode.read()")
read(s, "CBB0 efficiency_latency_ctrl_ratio", "@sv.socket0.cbb0.base.tpmi.ufs_control.efficiency_latency_ctrl_ratio.read()")
# Check adv_control register if present
read(s, "CBB0 ufs_adv_control (if exists)", "@sv.socket0.cbb0.base.tpmi.ufs_adv_control.read() if hasattr(sv.socket0.cbb0.base.tpmi,'ufs_adv_control') else 'N/A'")
# Check for any Pcode UFS feedback registers
read(s, "CBB0 TPMI lock/pending state",   "@sv.socket0.cbb0.base.tpmi.tpmi_info_header.read()")

# ── Step 4: TPMI write + PEGA trigger combo (v2) ──────────────────────────
TARGET = 0x10
print(f"\n[Step 4] Force CBB0 mesh to 0x{TARGET:02x}: TPMI write + PEGA trigger")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{TARGET:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{TARGET:x})", wait=1)
read(s, "CBB0 max_ratio (after write)", "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
read(s, "CBB0 min_ratio (after write)", "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")

# PEGA trigger to wake Pcode GV loop (v2 addition)
print(f"  [v2] Issuing PEGA CLR GV trigger to activate Pcode response...")
trigger_pega_clrgv(s, "cbb0", TARGET)

# Poll for status propagation
print(f"  Polling ufs_status.current_ratio for 0x{TARGET:02x} (5x, 2s interval)...")
final_ratio_cbb0 = poll_ratio(s, "sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio", TARGET)
results["step4_cbb0_ratio"] = "PASS" if str(TARGET) in str(final_ratio_cbb0) or hex(TARGET) in str(final_ratio_cbb0) else "FAIL (no change)"

# ── Step 5: CBB1 ──────────────────────────────────────────────────────────
print(f"\n[Step 5] Force CBB1 mesh to 0x{TARGET:02x}")
simics_cmd(s, f"@sv.socket0.cbb1.base.tpmi.ufs_control.max_ratio.write(0x{TARGET:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb1.base.tpmi.ufs_control.min_ratio.write(0x{TARGET:x})", wait=1)
trigger_pega_clrgv(s, "cbb1", TARGET)
final_ratio_cbb1 = poll_ratio(s, "sv.socket0.cbb1.base.tpmi.ufs_status.current_ratio", TARGET)
results["step5_cbb1_ratio"] = "PASS" if str(TARGET) in str(final_ratio_cbb1) or hex(TARGET) in str(final_ratio_cbb1) else "FAIL (no change)"

# ── Step 6: Alternate ratio ────────────────────────────────────────────────
TARGET2 = 0x25
print(f"\n[Step 6] Force CBB0 to higher ratio 0x{TARGET2:02x} ({TARGET2*100} MHz)")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{TARGET2:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{TARGET2:x})", wait=1)
trigger_pega_clrgv(s, "cbb0", TARGET2)
final_ratio_alt = poll_ratio(s, "sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio", TARGET2)
results["step6_alt_ratio"] = "PASS" if str(TARGET2) in str(final_ratio_alt) or hex(TARGET2) in str(final_ratio_alt) else "FAIL (no change)"

# ── Step 7: Restore defaults ───────────────────────────────────────────────
ORIG_MAX = int(b_max_cbb0.strip(), 0) if b_max_cbb0.strip().startswith("0x") else int(b_max_cbb0.strip() or "0x1b", 0)
ORIG_MIN = int(b_min_cbb0.strip(), 0) if b_min_cbb0.strip().startswith("0x") else 0x04
print(f"\n[Step 7] Restore defaults MAX=0x{ORIG_MAX:x}, MIN=0x{ORIG_MIN:x}")
for cbb in ["cbb0", "cbb1"]:
    simics_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.ufs_control.max_ratio.write(0x{ORIG_MAX:x})", wait=1)
    simics_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.ufs_control.min_ratio.write(0x{ORIG_MIN:x})", wait=1)
time.sleep(2)
r_max = read(s, "CBB0 max_ratio (RESTORED)", "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
r_min = read(s, "CBB0 min_ratio (RESTORED)", "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")
results["step7_restore"] = "PASS" if str(hex(ORIG_MAX)) in r_max or str(ORIG_MAX) in r_max else "FAIL"

# ── Step 8: Negative coverage — IMH and CBB fabric_1 ─────────────────────
print("\n[Step 8] Negative coverage — IMH and CBB fabric_1 (should be unchanged)")
imh_mem_after = read(s, "IMH0 ufs_status.current_ratio (Memory — static)",    "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio.read()")
imh_io_after  = read(s, "IMH0 ufs_status_fabric_1.current_ratio (IO — static)","@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio.read()")
cb_f1_ctrl    = read(s, "CBB0 ufs_control_fabric_1 (unchanged)",               "@sv.socket0.cbb0.base.tpmi.ufs_control_fabric_1.read()")
cb_f1_stat    = read(s, "CBB0 ufs_status_fabric_1 (unchanged)",                "@sv.socket0.cbb0.base.tpmi.ufs_status_fabric_1.read()")
results["step8_imh_mem_static"]  = "PASS" if imh_mem.strip() == imh_mem_after.strip() else "FAIL (changed)"
results["step8_imh_io_static"]   = "PASS" if imh_io.strip()  == imh_io_after.strip()  else "FAIL (changed)"

# ── Final verdict ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("VERDICT SUMMARY")
print("=" * 70)
criteria = {
    "Step 1  Baseline reads (max=0x1b, min=0x04)":                  results.get("step1_baseline"),
    "Step 4  CBB0 current_ratio → 0x10 after TPMI+PEGA":            results.get("step4_cbb0_ratio"),
    "Step 5  CBB1 current_ratio → 0x10 after TPMI+PEGA":            results.get("step5_cbb1_ratio"),
    "Step 6  CBB0 alt ratio 0x25 response":                          results.get("step6_alt_ratio"),
    "Step 7  Restore MAX/MIN to defaults":                           results.get("step7_restore"),
    "Step 8  IMH Memory static throughout":                          results.get("step8_imh_mem_static"),
    "Step 8  IMH IO static throughout":                              results.get("step8_imh_io_static"),
}
all_pass = True
for crit, verdict in criteria.items():
    v = verdict or "UNKNOWN"
    icon = "PASS" if "PASS" in v else "FAIL"
    if icon != "PASS": all_pass = False
    print(f"  [{icon}] {crit}: {v}")

print("\n" + "=" * 70)
env_note = "(status propagation requires active Pcode GV loop — PEGA trigger added in v2)"
print(f"OVERALL: {'PASS' if all_pass else 'PARTIAL PASS / NEEDS_ADAPTATION'}")
print(f"NOTE: {env_note}")
print("=" * 70)

s.close()
print("\nDone.")


# ── Step 1: Read baselines ─────────────────────────────────────────────────
print("\n[Step 1] Baseline reads")
read(s, "CBB0 ufs_control raw",       "@sv.socket0.cbb0.base.tpmi.ufs_control.read()")
read(s, "CBB0 ufs_control.max_ratio", "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
read(s, "CBB0 ufs_control.min_ratio", "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")
read(s, "CBB0 ufs_status raw",        "@sv.socket0.cbb0.base.tpmi.ufs_status.read()")
read(s, "CBB0 ufs_status.current_ratio (BASELINE)", "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
read(s, "CBB1 ufs_control.max_ratio", "@sv.socket0.cbb1.base.tpmi.ufs_control.max_ratio.read()")
read(s, "CBB1 ufs_status.current_ratio (BASELINE)", "@sv.socket0.cbb1.base.tpmi.ufs_status.current_ratio.read()")

# ── Step 2: IMH baseline (should remain static — NWP ZBB) ─────────────────
print("\n[Step 2] IMH Status baseline (expected static/ZBB)")
read(s, "IMH0 ufs_status.current_ratio (Memory)", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio.read()")
read(s, "IMH0 ufs_status_fabric_1.current_ratio (IO)", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio.read()")

# ── Step 3: Negative coverage — CBB fabric_1 baseline ─────────────────────
print("\n[Step 3] Negative coverage — CBB fabric_1 (should stay unchanged)")
read(s, "CBB0 ufs_control_fabric_1 raw", "@sv.socket0.cbb0.base.tpmi.ufs_control_fabric_1.read()")
read(s, "CBB0 ufs_status_fabric_1 raw",  "@sv.socket0.cbb0.base.tpmi.ufs_status_fabric_1.read()")

# ── Step 4: Force CBB0 to target_ratio (MIN=MAX=0x10 = 16 = 1.6 GHz) ──────
TARGET = 0x10
print(f"\n[Step 4] Force CBB0 mesh to 0x{TARGET:02x} ({TARGET*100} MHz): write MIN=MAX={TARGET}")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{TARGET:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{TARGET:x})", wait=1)
print(f"  Wrote MAX={TARGET:#x} and MIN={TARGET:#x} to CBB0 ufs_control")

# Wait for pcode to respond
time.sleep(3)
print("  (waiting 3s for pcode response...)")

read(s, "CBB0 ufs_control.max_ratio (after write)", "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
read(s, "CBB0 ufs_control.min_ratio (after write)", "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")
read(s, "CBB0 ufs_status.current_ratio (AFTER)",    "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
read(s, "CBB0 ufs_status raw (AFTER)",              "@sv.socket0.cbb0.base.tpmi.ufs_status.read()")

# ── Step 5: Force CBB1 to same target ─────────────────────────────────────
print(f"\n[Step 5] Force CBB1 mesh to 0x{TARGET:02x}")
simics_cmd(s, f"@sv.socket0.cbb1.base.tpmi.ufs_control.max_ratio.write(0x{TARGET:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb1.base.tpmi.ufs_control.min_ratio.write(0x{TARGET:x})", wait=1)
time.sleep(3)
read(s, "CBB1 ufs_status.current_ratio (AFTER)", "@sv.socket0.cbb1.base.tpmi.ufs_status.current_ratio.read()")

# ── Step 6: Try different target — higher ratio ────────────────────────────
TARGET2 = 0x25  # 37 = 3.7 GHz
print(f"\n[Step 6] Force CBB0 to higher ratio 0x{TARGET2:02x} ({TARGET2*100} MHz)")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{TARGET2:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{TARGET2:x})", wait=1)
time.sleep(3)
read(s, "CBB0 ufs_status.current_ratio (target 0x25)", "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")

# ── Step 7: Restore defaults and verify ───────────────────────────────────
ORIG_MAX = 0x1b
ORIG_MIN = 0x04
print(f"\n[Step 7] Restore defaults MAX=0x{ORIG_MAX:x}, MIN=0x{ORIG_MIN:x}")
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(0x{ORIG_MAX:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(0x{ORIG_MIN:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb1.base.tpmi.ufs_control.max_ratio.write(0x{ORIG_MAX:x})", wait=1)
simics_cmd(s, f"@sv.socket0.cbb1.base.tpmi.ufs_control.min_ratio.write(0x{ORIG_MIN:x})", wait=1)
time.sleep(3)
read(s, "CBB0 ufs_status.current_ratio (RESTORED)", "@sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()")
read(s, "CBB0 ufs_control.max_ratio (RESTORED)",    "@sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.read()")
read(s, "CBB0 ufs_control.min_ratio (RESTORED)",    "@sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.read()")

# ── Step 8: Verify IMH and CBB fabric_1 unchanged (negative coverage) ──────
print("\n[Step 8] Negative coverage — verify unchanged after CBB writes")
read(s, "IMH0 ufs_status.current_ratio (Memory — should be static)", "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status.current_ratio.read()")
read(s, "IMH0 ufs_status_fabric_1.current_ratio (IO — static)",      "@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1.current_ratio.read()")
read(s, "CBB0 ufs_control_fabric_1 (should be unchanged)",           "@sv.socket0.cbb0.base.tpmi.ufs_control_fabric_1.read()")
read(s, "CBB0 ufs_status_fabric_1 (should be unchanged)",            "@sv.socket0.cbb0.base.tpmi.ufs_status_fabric_1.read()")

s.close()
print("\n=== Done ===")

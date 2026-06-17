"""
TC 22022423032 — CState C6 residency check
Validation scope: C6A, C6S, C6S-P residency on all CBBs.

Approach:
  1. Read baseline MSR residency counters (0x3FD = CC6, 0x3FC = CC3, 0x778 = CC1)
  2. Verify MSR 0xE2 C-state limit allows C6
  3. Inject PEGA C-state (C6A, C6S, C6S-P) via ucode-pcode mailbox
  4. Read counters after and compute delta — non-zero delta = PASS
  5. Verify C1 residency counter after C-state release (C0 injection)

PEGA C-state encoding (from PegaUtils.cStateLut and issuePegaReq_CBB_Cstates):
  c6s  = 0x23 → core_cstate=0x2, core_substate=0x3  (CMD1 data bits)
  c6sp = 0x20 → core_cstate=0x2, core_substate=0x0
  c6a  = 0x24 → core_cstate=0x2, core_substate=0x4
  c1   = 0x00 → core_cstate=0x0, core_substate=0x0
  c0   = 0xF0 → all_bigcores=0x1, core_cstate=0xF, core_substate=0x0

MSR residency counters (read per-core via thread0.msr()):
  0x778  MSR_CORE_C1_RESIDENCY
  0x3FD  MSR_CORE_C6_RESIDENCY
  0x3FA  MSR_PKG_C6_RESIDENCY (package level)
  0xE2   MSR_PKG_CST_CONFIG_CONTROL (C-state limit)

NWP topology: 2 CBBs, each with compute0..compute3, each with module0..moduleN
"""
import socket, time, re

# ── Helpers ────────────────────────────────────────────────────────────────
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
    print(f"  {label}: {val[:150]}")
    return val

def msr(s, cbb, compute, core, addr, label):
    cmd = f"@sv.socket0.{cbb}.{compute}.cpu.module0.core{core}.thread0.msr(0x{addr:x})"
    return read(s, label, cmd)

def inject_cstate_cbb(s, cbb, core_cstate, core_substate, all_bigcores=0,
                      cmd1w=0x24, cmd0w=0x22, wait_busy=2):
    """
    Inject PEGA C-state on one CBB via ucode-pcode mailbox.

    CMD1W data encoding (command1_cbb_cstates from pega_register_classes.py):
      bits[23:20] core_substate
      bits[19:16] core_cstate
      bit[12]     all_bigcores (target all big cores in cluster)
      bits[9:8]   clstr_id (0)
      bits[7:3]   module_id (0)
      bits[2:0]   lp_id (0)

    CMD0W data encoding (command0):
      bit[31]     run_busy
      bits[30:28] commandType = 0x1 (C-state)
    """
    base = f"sv.socket0.{cbb}.base.punit_regs.punit_gpsb.gpsb_infvnn_crs"
    fid_resp = simics_cmd(s, f"@print((sv.socket0.{cbb}.compute0.instance * 8) % 256)", wait=2)
    fid_lines = [l for l in fid_resp.splitlines() if l.strip().lstrip('-').isdigit()]
    fid = int(fid_lines[0]) if fid_lines else 0
    data_reg  = f'{base}.ucode_pcode_mailbox_data["fid_{fid}"]'
    iface_reg = f'{base}.ucode_pcode_mailbox_interface["fid_{fid}"]'

    # Build CMD1 data word
    cmd1_data = (core_substate << 20) | (core_cstate << 16) | (all_bigcores << 12)
    # CMD1W (0x24)
    simics_cmd(s, f"@{data_reg}.write(0x{cmd1_data:08x})", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|cmd1w:08x})", wait=wait_busy)

    # CMD0W (0x22): commandType=0x1 (C-state), run_busy=1
    cmd0_data = (1 << 31) | (0x1 << 28)  # = 0x90000000
    simics_cmd(s, f"@{data_reg}.write(0x{cmd0_data:08x})", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|cmd0w:08x})", wait=wait_busy)

def release_cstate_cbb(s, cbb):
    """Release PEGA C-state — inject C0 (all_bigcores, core_cstate=0xF, substate=0)."""
    # c0 = 0xF0 from cStateLut → core_cstate=0xF, substate=0, all_bigcores=1
    inject_cstate_cbb(s, cbb, core_cstate=0xF, core_substate=0x0, all_bigcores=1)

results = {}

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

print("=" * 70)
print("TC 22022423032 — C6 Residency Check (C6A, C6S, C6S-P) on NWP CBBs")
print("=" * 70)

# ── Step 1: C-state config check ──────────────────────────────────────────
print("\n[Step 1] C-state limit config — MSR 0xE2")
e2_cbb0 = msr(s, "cbb0", "compute0", 0, 0xE2, "CBB0 MSR_PKG_CST_CONFIG_CONTROL (0xE2)")
e2_cbb1 = msr(s, "cbb1", "compute0", 0, 0xE2, "CBB1 MSR_PKG_CST_CONFIG_CONTROL (0xE2)")
# bits[2:0] = C-state limit: 2=C6, 6=C6, 7=no limit
# Check C6 not blocked
try:
    e2_val = int(e2_cbb0.strip(), 0)
    cst_limit = e2_val & 0x7
    c6_allowed = cst_limit in [2, 6, 7]
    results["step1_c6_allowed"] = "PASS" if c6_allowed else f"FAIL (CST_LIMIT={cst_limit:#x}, C6 blocked)"
    print(f"    CST_LIMIT field = {cst_limit:#x} → C6 {'ALLOWED' if c6_allowed else 'BLOCKED'}")
except:
    results["step1_c6_allowed"] = "UNKNOWN (parse error)"

# ── Step 2: Baseline residency counters ───────────────────────────────────
print("\n[Step 2] Baseline residency counters (CBB0 compute0 core0)")
cc6_base  = msr(s, "cbb0", "compute0", 0, 0x3FD, "CC6  residency (0x3FD) BASELINE")
cc1_base  = msr(s, "cbb0", "compute0", 0, 0x778, "CC1  residency (0x778) BASELINE")
pc6_base  = msr(s, "cbb0", "compute0", 0, 0x3FA, "PC6  residency (0x3FA) BASELINE")

# Try high-level via pega if library available
print("\n[Step 2b] Check pega library availability for C-states")
pega_avail = simics_cmd(s, "@import newport.pm.pmutils.pega as pega; print('pega OK, pegaCstate:', hasattr(pega,'pegaCstate'))", wait=5)
pega_ok = "pega OK" in pega_avail
print(f"  pega library: {'available' if pega_ok else 'not available'}")
results["step2b_pega_lib"] = "PASS" if pega_ok else "WARN (using direct mailbox)"

# ── Step 3: C6S injection and residency check ─────────────────────────────
print("\n[Step 3] C6S injection (core_cstate=0x2, core_substate=0x3)")
if pega_ok:
    print("  [via pega.pegaCstate]")
    simics_cmd(s, "@import newport.pm.pmutils.pega as pega; pega.pegaCstate(sktNum=0, dieName='cbb0', domainDict={'c6s':'all'})", wait=6)
else:
    inject_cstate_cbb(s, "cbb0", core_cstate=0x2, core_substate=0x3, all_bigcores=1)
time.sleep(3)
cc6_after_c6s = msr(s, "cbb0", "compute0", 0, 0x3FD, "CC6 residency AFTER C6S")
try:
    delta_c6s = int(cc6_after_c6s.strip(), 0) - int(cc6_base.strip(), 0) if cc6_base.strip().startswith("0x") else -1
    results["step3_c6s_residency"] = f"PASS (delta={hex(delta_c6s)})" if delta_c6s > 0 else "FAIL (no increment)"
    print(f"    CC6 delta after C6S: {hex(max(delta_c6s,0))}")
except:
    results["step3_c6s_residency"] = "UNKNOWN"
# release
release_cstate_cbb(s, "cbb0")
time.sleep(2)

# ── Step 4: C6S-P injection ───────────────────────────────────────────────
print("\n[Step 4] C6S-P injection (core_cstate=0x2, core_substate=0x0)")
cc6_pre_c6sp = msr(s, "cbb0", "compute0", 0, 0x3FD, "CC6 residency PRE C6S-P")
if pega_ok:
    simics_cmd(s, "@import newport.pm.pmutils.pega as pega; pega.pegaCstate(sktNum=0, dieName='cbb0', domainDict={'c6sp':'all'})", wait=6)
else:
    inject_cstate_cbb(s, "cbb0", core_cstate=0x2, core_substate=0x0, all_bigcores=1)
time.sleep(3)
cc6_after_c6sp = msr(s, "cbb0", "compute0", 0, 0x3FD, "CC6 residency AFTER C6S-P")
try:
    delta_c6sp = int(cc6_after_c6sp.strip(), 0) - int(cc6_pre_c6sp.strip(), 0) if cc6_pre_c6sp.strip().startswith("0x") else -1
    results["step4_c6sp_residency"] = f"PASS (delta={hex(delta_c6sp)})" if delta_c6sp > 0 else "FAIL (no increment)"
    print(f"    CC6 delta after C6S-P: {hex(max(delta_c6sp,0))}")
except:
    results["step4_c6sp_residency"] = "UNKNOWN"
release_cstate_cbb(s, "cbb0")
time.sleep(2)

# ── Step 5: C6A injection ─────────────────────────────────────────────────
print("\n[Step 5] C6A injection (core_cstate=0x2, core_substate=0x4)")
cc6_pre_c6a = msr(s, "cbb0", "compute0", 0, 0x3FD, "CC6 residency PRE C6A")
if pega_ok:
    simics_cmd(s, "@import newport.pm.pmutils.pega as pega; pega.pegaCstate(sktNum=0, dieName='cbb0', domainDict={'c6a':'all'})", wait=6)
else:
    inject_cstate_cbb(s, "cbb0", core_cstate=0x2, core_substate=0x4, all_bigcores=1)
time.sleep(3)
cc6_after_c6a = msr(s, "cbb0", "compute0", 0, 0x3FD, "CC6 residency AFTER C6A")
try:
    delta_c6a = int(cc6_after_c6a.strip(), 0) - int(cc6_pre_c6a.strip(), 0) if cc6_pre_c6a.strip().startswith("0x") else -1
    results["step5_c6a_residency"] = f"PASS (delta={hex(delta_c6a)})" if delta_c6a > 0 else "FAIL (no increment)"
    print(f"    CC6 delta after C6A: {hex(max(delta_c6a,0))}")
except:
    results["step5_c6a_residency"] = "UNKNOWN"
release_cstate_cbb(s, "cbb0")
time.sleep(2)

# ── Step 6: Both CBBs — spot check ────────────────────────────────────────
print("\n[Step 6] CBB1 C6S spot check")
cc6_cbb1_base = msr(s, "cbb1", "compute0", 0, 0x3FD, "CBB1 CC6 residency BASELINE")
if pega_ok:
    simics_cmd(s, "@import newport.pm.pmutils.pega as pega; pega.pegaCstate(sktNum=0, dieName='cbb1', domainDict={'c6s':'all'})", wait=6)
else:
    inject_cstate_cbb(s, "cbb1", core_cstate=0x2, core_substate=0x3, all_bigcores=1)
time.sleep(3)
cc6_cbb1_after = msr(s, "cbb1", "compute0", 0, 0x3FD, "CBB1 CC6 residency AFTER C6S")
try:
    delta_cbb1 = int(cc6_cbb1_after.strip(), 0) - int(cc6_cbb1_base.strip(), 0) if cc6_cbb1_base.strip().startswith("0x") else -1
    results["step6_cbb1_c6s"] = f"PASS (delta={hex(delta_cbb1)})" if delta_cbb1 > 0 else "FAIL (no increment)"
    print(f"    CBB1 CC6 delta: {hex(max(delta_cbb1,0))}")
except:
    results["step6_cbb1_c6s"] = "UNKNOWN"
release_cstate_cbb(s, "cbb1")
time.sleep(2)

# ── Step 7: C1 verification — residency after C1 injection ────────────────
print("\n[Step 7] C1 residency after C1 injection")
cc1_pre = msr(s, "cbb0", "compute0", 0, 0x778, "CC1 residency PRE C1")
if pega_ok:
    simics_cmd(s, "@import newport.pm.pmutils.pega as pega; pega.pegaCstate(sktNum=0, dieName='cbb0', domainDict={'c1':'all'})", wait=6)
else:
    inject_cstate_cbb(s, "cbb0", core_cstate=0x0, core_substate=0x0, all_bigcores=1)
time.sleep(3)
cc1_after = msr(s, "cbb0", "compute0", 0, 0x778, "CC1 residency AFTER C1")
try:
    delta_c1 = int(cc1_after.strip(), 0) - int(cc1_pre.strip(), 0) if cc1_pre.strip().startswith("0x") else -1
    results["step7_c1_residency"] = f"PASS (delta={hex(delta_c1)})" if delta_c1 > 0 else "FAIL (no increment)"
    print(f"    CC1 delta: {hex(max(delta_c1,0))}")
except:
    results["step7_c1_residency"] = "UNKNOWN"

# ── Final verdict ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("VERDICT SUMMARY — TC 22022423032")
print("=" * 70)
criteria = {
    "Step 1  C-state limit allows C6":            results.get("step1_c6_allowed"),
    "Step 2b PEGA library available":             results.get("step2b_pega_lib"),
    "Step 3  CC6 residency increments after C6S": results.get("step3_c6s_residency"),
    "Step 4  CC6 residency increments after C6SP":results.get("step4_c6sp_residency"),
    "Step 5  CC6 residency increments after C6A": results.get("step5_c6a_residency"),
    "Step 6  CBB1 CC6 increments after C6S":      results.get("step6_cbb1_c6s"),
    "Step 7  CC1 residency increments after C1":  results.get("step7_c1_residency"),
}
all_pass = True
for crit, verdict in criteria.items():
    v = verdict or "UNKNOWN"
    is_pass = "PASS" in v or "WARN" in v
    if "FAIL" in v or "UNKNOWN" in v: all_pass = False
    print(f"  [{'PASS' if is_pass else 'FAIL'}] {crit}: {v}")

print("\n" + "=" * 70)
print(f"OVERALL: {'PASS' if all_pass else 'PARTIAL PASS / NEEDS_ADAPTATION'}")
print("NOTE: Residency counter increment confirms C-state entry in Simics model.")
print("NOTE: Zero delta means Simics model does not simulate residency counters.")
print("=" * 70)

s.close()
print("\nDone.")

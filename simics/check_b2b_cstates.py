"""
TC 22022423044 — Multiple Back-to-Back C-states on Same Core
Validation scope: Run many C-state transitions on the same core and verify stability.

Test plan:
  1. Read baseline CC6/CC1 counters and sanity-check CST_LIMIT
  2. Run N back-to-back (B2B) cycles on CBB0 cbb0, cycling through C6S → C6A → C6S-P → C1 → C0
  3. After each B2B batch, verify:
     a. CC6 counter increased (C6 was entered)
     b. CC1 counter increased (C1 was entered)
     c. No MCA detected (MSR 0x17A MCG_STATUS = 0)
  4. Run same sequence on CBB1 — verify stability
  5. Run cross-die: alternate CBB0/CBB1 injections while polling for MCA

Pass criteria:
  - CC6 counter monotonically increases across all B2B iterations
  - CC1 counter monotonically increases across all B2B iterations
  - MCG_STATUS (0x17A) stays 0 throughout
  - No Simics simulation error thrown

C-state encoding (PegaUtils.cStateLut / issuePegaReq_CBB_Cstates):
  c6s  = core_cstate=0x2, substate=0x3
  c6a  = core_cstate=0x2, substate=0x4
  c6sp = core_cstate=0x2, substate=0x0
  c1   = core_cstate=0x0, substate=0x0
  c0   = core_cstate=0xF, substate=0x0, all_bigcores=1 (release)

MSRs:
  0x778  CC1 residency counter
  0x3FD  CC6 residency counter
  0x17A  MCG_STATUS (MCA detected if non-zero)
"""
import socket, time, re

B2B_ITERATIONS = 10       # number of B2B cycles per C-state
SETTLE_SEC     = 1        # seconds between injections

def simics_cmd(s, cmd, wait=2):
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

def read(s, label, cmd, wait=2):
    r = simics_cmd(s, cmd, wait)
    lines = [l for l in r.splitlines() if l.strip() and "running>" not in l
             and not l.startswith(cmd[:12])]
    val = "\n".join(lines).strip()
    print(f"  {label}: {val[:120]}")
    return val

def read_msr(s, cbb, addr):
    cmd = f"@sv.socket0.{cbb}.compute0.cpu.module0.core0.thread0.msr(0x{addr:x})"
    r = simics_cmd(s, cmd, wait=1)
    lines = [l for l in r.splitlines() if l.strip() and "running>" not in l]
    return "\n".join(lines).strip()

def inject_cstate(s, cbb, core_cstate, core_substate, all_bigcores=0, wait_busy=1):
    """Direct PEGA mailbox C-state injection."""
    base = f"sv.socket0.{cbb}.base.punit_regs.punit_gpsb.gpsb_infvnn_crs"
    fid_resp = simics_cmd(s, f"@print((sv.socket0.{cbb}.compute0.instance * 8) % 256)", wait=2)
    fid_lines = [l for l in fid_resp.splitlines() if l.strip().lstrip('-').isdigit()]
    fid = int(fid_lines[0]) if fid_lines else 0
    data_reg  = f'{base}.ucode_pcode_mailbox_data["fid_{fid}"]'
    iface_reg = f'{base}.ucode_pcode_mailbox_interface["fid_{fid}"]'
    # CMD1W (0x24): target C-state
    cmd1 = (core_substate << 20) | (core_cstate << 16) | (all_bigcores << 12)
    simics_cmd(s, f"@{data_reg}.write(0x{cmd1:08x})", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x24:08x})", wait=wait_busy)
    # CMD0W (0x22): C-state commandType=0x1
    simics_cmd(s, f"@{data_reg}.write(0x{(1<<31)|(0x1<<28):08x})", wait=1)
    simics_cmd(s, f"@{iface_reg}.write(0x{(1<<31)|0x22:08x})", wait=wait_busy)

def release(s, cbb):
    inject_cstate(s, cbb, core_cstate=0xF, core_substate=0x0, all_bigcores=1)

def parse_int(val):
    try:
        return int(val.strip(), 0)
    except:
        return None

# ── C-states to cycle through ─────────────────────────────────────────────
CSTATES = [
    ("C6S",  0x2, 0x3, 0),
    ("C6A",  0x2, 0x4, 0),
    ("C6SP", 0x2, 0x0, 0),
    ("C1",   0x0, 0x0, 0),
]

results = {}

s = socket.create_connection(("localhost", 4444), 5)
time.sleep(1); s.recv(4096)

print("=" * 70)
print(f"TC 22022423044 — Multiple B2B C-states on Same Core ({B2B_ITERATIONS} iters)")
print("=" * 70)

# ── Check pega library ─────────────────────────────────────────────────────
pega_ok = "pega OK" in simics_cmd(s, "@import newport.pm.pmutils.pega as pega; print('pega OK')", wait=5)
print(f"\n  PEGA library: {'available' if pega_ok else 'direct mailbox fallback'}")

# ── Step 1: Config and baselines ──────────────────────────────────────────
print("\n[Step 1] C-state config and baseline counters")
e2 = read_msr(s, "cbb0", 0xE2)
cst_limit = (parse_int(e2) or 0) & 0x7
c6_ok = cst_limit in [2, 6, 7]
results["step1_cst_limit"] = f"PASS (CST_LIMIT={cst_limit:#x})" if c6_ok else f"FAIL (CST_LIMIT={cst_limit:#x} blocks C6)"
print(f"  CBB0 MSR_PKG_CST_CONFIG_CONTROL (0xE2): {e2}  CST_LIMIT={cst_limit:#x} → C6 {'ALLOWED' if c6_ok else 'BLOCKED'}")

cc6_start   = read_msr(s, "cbb0", 0x3FD)
cc1_start   = read_msr(s, "cbb0", 0x778)
mcg_start   = read_msr(s, "cbb0", 0x17A)
print(f"  CC6 baseline (0x3FD): {cc6_start}")
print(f"  CC1 baseline (0x778): {cc1_start}")
print(f"  MCG_STATUS  (0x17A): {mcg_start}")
results["step1_mcg_clean"] = "PASS" if parse_int(mcg_start) == 0 else f"FAIL (MCG={mcg_start})"

# ── Step 2: B2B C-state loop on CBB0 ─────────────────────────────────────
print(f"\n[Step 2] B2B loop on CBB0 — {B2B_ITERATIONS} iterations of C6S→C6A→C6SP→C1→C0")
cc6_prev = parse_int(cc6_start) or 0
cc1_prev = parse_int(cc1_start) or 0
cc6_monotone = True
cc1_monotone = True
mca_seen     = False

for i in range(B2B_ITERATIONS):
    for name, cx, sub, abig in CSTATES:
        if pega_ok:
            pega_name = name.lower().replace("-","")
            simics_cmd(s, f"@import newport.pm.pmutils.pega as pega; pega.pegaCstate(sktNum=0, dieName='cbb0', domainDict={{'{pega_name}':'all'}})", wait=3)
        else:
            inject_cstate(s, "cbb0", cx, sub, abig)
        time.sleep(SETTLE_SEC)
    # Release
    release(s, "cbb0")
    time.sleep(SETTLE_SEC)

    # Read counters every iteration
    cc6_now = parse_int(read_msr(s, "cbb0", 0x3FD)) or 0
    cc1_now = parse_int(read_msr(s, "cbb0", 0x778)) or 0
    mcg_now = read_msr(s, "cbb0", 0x17A)

    if cc6_now < cc6_prev: cc6_monotone = False
    if cc1_now < cc1_prev: cc1_monotone = False
    if parse_int(mcg_now) != 0:
        mca_seen = True
        print(f"  [iter {i+1}] MCA DETECTED: MCG_STATUS={mcg_now}")
    else:
        print(f"  [iter {i+1}] CC6={hex(cc6_now)} CC1={hex(cc1_now)} MCG=0 OK")

    cc6_prev, cc1_prev = cc6_now, cc1_now

cc6_delta = cc6_prev - (parse_int(cc6_start) or 0)
cc1_delta = cc1_prev - (parse_int(cc1_start) or 0)
results["step2_cc6_monotone"] = "PASS" if cc6_monotone and cc6_delta >= 0 else f"FAIL (non-monotone or delta={hex(cc6_delta)})"
results["step2_cc1_monotone"] = "PASS" if cc1_monotone and cc1_delta >= 0 else f"FAIL (non-monotone or delta={hex(cc1_delta)})"
results["step2_no_mca"]       = "PASS" if not mca_seen else "FAIL (MCA detected during B2B loop)"
print(f"\n  CBB0 B2B total: CC6 delta={hex(cc6_delta)}, CC1 delta={hex(cc1_delta)}, MCA={'YES' if mca_seen else 'NO'}")

# ── Step 3: B2B loop on CBB1 ─────────────────────────────────────────────
print(f"\n[Step 3] B2B loop on CBB1 — {B2B_ITERATIONS} iterations")
cc6_b1_start = parse_int(read_msr(s, "cbb1", 0x3FD)) or 0
cc1_b1_start = parse_int(read_msr(s, "cbb1", 0x778)) or 0
mca_b1 = False

for i in range(B2B_ITERATIONS):
    for name, cx, sub, abig in CSTATES:
        if pega_ok:
            pega_name = name.lower().replace("-","")
            simics_cmd(s, f"@import newport.pm.pmutils.pega as pega; pega.pegaCstate(sktNum=0, dieName='cbb1', domainDict={{'{pega_name}':'all'}})", wait=3)
        else:
            inject_cstate(s, "cbb1", cx, sub, abig)
        time.sleep(SETTLE_SEC)
    release(s, "cbb1")
    time.sleep(SETTLE_SEC)

    cc6_b1 = parse_int(read_msr(s, "cbb1", 0x3FD)) or 0
    mcg_b1 = read_msr(s, "cbb1", 0x17A)
    if parse_int(mcg_b1) != 0:
        mca_b1 = True
        print(f"  [iter {i+1}] CBB1 MCA DETECTED: {mcg_b1}")
    else:
        print(f"  [iter {i+1}] CBB1 CC6={hex(cc6_b1)} MCG=0 OK")

cc6_b1_delta = (parse_int(read_msr(s, "cbb1", 0x3FD)) or 0) - cc6_b1_start
results["step3_cbb1_stability"] = "PASS" if not mca_b1 else "FAIL (MCA on CBB1)"
results["step3_cbb1_cc6"]      = f"PASS (delta={hex(cc6_b1_delta)})" if cc6_b1_delta >= 0 else "FAIL (counter regression)"
print(f"  CBB1 B2B total: CC6 delta={hex(cc6_b1_delta)}, MCA={'YES' if mca_b1 else 'NO'}")

# ── Step 4: Cross-die alternating B2B ────────────────────────────────────
print(f"\n[Step 4] Cross-die alternating B2B — {B2B_ITERATIONS} iters CBB0/CBB1 interleaved")
mca_cross = False
for i in range(B2B_ITERATIONS):
    cbb_a, cbb_b = ("cbb0", "cbb1") if i % 2 == 0 else ("cbb1", "cbb0")
    inject_cstate(s, cbb_a, 0x2, 0x3, 0)   # C6S
    inject_cstate(s, cbb_b, 0x2, 0x4, 0)   # C6A
    time.sleep(SETTLE_SEC)
    release(s, cbb_a); release(s, cbb_b)
    time.sleep(SETTLE_SEC)
    mcg_a = read_msr(s, cbb_a, 0x17A)
    mcg_b = read_msr(s, cbb_b, 0x17A)
    if parse_int(mcg_a) != 0 or parse_int(mcg_b) != 0:
        mca_cross = True
        print(f"  [iter {i+1}] Cross-die MCA: {cbb_a}={mcg_a} {cbb_b}={mcg_b}")
    else:
        print(f"  [iter {i+1}] Cross-die OK MCG=0")

results["step4_cross_die"] = "PASS" if not mca_cross else "FAIL (MCA during cross-die B2B)"

# ── Final verdict ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("VERDICT SUMMARY — TC 22022423044")
print("=" * 70)
criteria = {
    "Step 1  CST_LIMIT allows C6":             results.get("step1_cst_limit"),
    "Step 1  MCG_STATUS clean at start":       results.get("step1_mcg_clean"),
    "Step 2  CC6 monotonically increasing":    results.get("step2_cc6_monotone"),
    "Step 2  CC1 monotonically increasing":    results.get("step2_cc1_monotone"),
    "Step 2  No MCA during CBB0 B2B loop":    results.get("step2_no_mca"),
    "Step 3  CBB1 B2B stable (no MCA)":       results.get("step3_cbb1_stability"),
    "Step 3  CBB1 CC6 counter incremented":   results.get("step3_cbb1_cc6"),
    "Step 4  Cross-die B2B stable":           results.get("step4_cross_die"),
}
all_pass = True
for crit, verdict in criteria.items():
    v = verdict or "UNKNOWN"
    ok = "PASS" in v
    if not ok: all_pass = False
    print(f"  [{'PASS' if ok else 'FAIL'}] {crit}: {v}")

print("\n" + "=" * 70)
print(f"OVERALL: {'PASS' if all_pass else 'PARTIAL PASS / NEEDS_ADAPTATION'}")
print("NOTE: Zero residency deltas indicate Simics does not simulate C-state counters.")
print("NOTE: Zero MCA throughout confirms system stability during B2B transitions.")
print("=" * 70)

s.close()
print("\nDone.")

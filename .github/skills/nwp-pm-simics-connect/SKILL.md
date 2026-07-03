---
name: nwp-pm-simics-connect
description: >
  Connect to a live NWP Simics session and run PythonSV / namednodes commands
  via the Simics telnet-frontend port. Given a server IP, sets up an SSH tunnel
  (port 4444) and sends @python commands through the socket. Also covers
  deploying TC scripts via SCP and running them with @exec(). Uses helpers in
  simics/simics_connect.py. Load this skill when the user wants to read NWP
  registers in Simics, run a TC script, inject PEGA, or inspect CBB/IMH state.
---

# NWP PM Simics Connect Skill

> Script root: `C:\github\nwp_testplan\simics\`
> Connection helpers: `simics/simics_connect.py`, `simics/simics_cmd.py`

---

## Architecture

```
Windows (this machine)              Linux server (<SERVER_IP>)
      port 4444                           port 4444
   localhost:4444 ←── SSH tunnel ──→ localhost:4444
         ↑                                   ↑
   socket.connect()               Simics telnet-frontend
   send "@python_cmd\n"    ──→    Simics evaluates via PythonSV namednodes
```

The Simics `telnet-frontend` command opens a Python-evaluating CLI socket.
Prefix `@` to run Python; no prefix for Simics CLI commands.

---

## Step 1 — Prerequisites (user does once per Simics session)

### 1a. Open telnet port in Simics

At the Simics `running>` prompt on the server:
```
telnet-frontend port=4444
```

### 1b. Open SSH tunnel (Windows PowerShell — keep this terminal open)

```powershell
$SERVER_IP = "10.116.33.137"   # <-- set to user-provided IP
ssh -L 4444:localhost:4444 -N -o PreferredAuthentications=keyboard-interactive bg3@$SERVER_IP
```
Type password when prompted. Leave the terminal open for the duration of the session.

### 1c. Initialize PythonSV namednodes (first command must be `sv.refresh()`)

```powershell
cd C:\github\nwp_testplan\simics
python simics_cmd.py "@sv.refresh()" --wait 15
```
Wait ~15 seconds for the banner. After this, all namednodes register paths are valid.

---

## Step 2 — Send Commands

### One-shot from PowerShell

```powershell
cd C:\github\nwp_testplan\simics

# Simics CLI command (no @)
python simics_cmd.py "pwd"

# PythonSV command (prefix @)
python simics_cmd.py "@sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()"

# Custom wait (default = 3 s)
python simics_cmd.py "@sv.refresh()" --wait 15
```

### Programmatic (from Python scripts)

```python
import sys
sys.path.insert(0, r"C:\github\nwp_testplan\simics")
from simics_connect import connect, send_cmd, close

s = connect()   # connects to localhost:4444

# Send any @python or Simics CLI command
r = send_cmd(s, "@sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()", wait=3)
print(r)

close(s)
```

### Multi-line Python via @exec()

To run a multi-line Python script, write it to the server then invoke via `@exec()`:

```powershell
# 1. SCP the script to the server
$SERVER_IP = "10.116.33.137"
$REMOTE_DIR = "/nfs/site/disks/simcloud_bg3_001/projects/nwp-7/2026ww23.6.00_47"
scp simics\check_c6_residency.py bg3@${SERVER_IP}:${REMOTE_DIR}/

# 2. Execute via @exec() through simics_cmd.py
python simics_cmd.py "@exec('${REMOTE_DIR}/check_c6_residency.py')" --wait 30
```

---

## Step 3 — Available TC Scripts

All scripts are in `C:\github\nwp_testplan\simics\`. Each self-imports from
`simics_connect.py` and can be deployed + run via `@exec()`.

| Script | TC / Purpose |
|--------|-------------|
| `check_c6_residency.py` | TC 22022423032 — C6A/C6S/C6S-P residency via MSR counters + PEGA injection |
| `check_b2b_cstates.py` | Back-to-back C-state transitions, stress/wake pattern |
| `check_cstate_msr_control.py` | MSR 0xE2 C-state limit control; verify limit propagation |
| `check_mc6_exit_actions.py` | MC6 exit action verification |
| `check_mc6_exit_actions_native.py` | MC6 exit — native Simics Python only (no socket) |
| `check_fast_ring_c3_native.py` | Fast Ring C3 entry/exit — native |
| `check_ring_c3_native.py` | Ring C3 with stress pattern — native |
| `check_cstate_wake_events_native.py` | C-state wake event verification — native |
| `inject_pega_fabricgv.py` | PEGA FabricGV injection via CBB mailbox |
| `verify_tpmi_fabricgv.py` | TPMI FabricGV register verification |
| `verify_ufs_tc.py` | UFS (Uncore Frequency Scaling) verification |
| `verify_out_of_boundary.py` | Out-of-boundary SST-TF/PCT verification |
| `fetch_all_pstate.py` | Dump all P-State related registers |
| `read_pm_registers.py` | Read ACP perf limit + IMH telemetry registers |
| `read_pstate_cstate.py` | Read P-State / C-State MSRs + PMSB registers |
| `discover_all_registers.py` | Discover all available namednodes registers |
| `dump_cbb_pcudata.py` | Dump CBB pcudata (all PMSB registers) |
| `probe_mc6_fuse.py` | Read MC6 fuse state |
| `check_pega_tc.py` | Generic PEGA TC runner |

**"native" scripts** run directly inside Simics Python (no socket needed). They are
deployed via SCP and invoked with `@exec()` from simics_cmd.py.

---

## Step 4 — Key NWP Register Paths (Verified in nwp-7/2026ww23.6.00_47)

### CBB (cbb0 / cbb1)

```python
# ACP perf limit
sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()
sv.socket0.cbb1.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()

# Per-FID ACP perf limit
sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit["fid_0"].read()

# PLR high-level mailbox
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.command.write(0)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.domain.write(2)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.run_busy.write(1)
sv.socket0.cbb0.base.tpmi.plr_mailbox_data.read()

# Core MSRs (per-core)
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x198)   # IA32_PERF_STATUS (current freq)
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x199)   # IA32_PERF_CTL (request)
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x770)   # HWP enable
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x771)   # IA32_HWP_CAPABILITIES
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x774)   # HWP request (min/max/desired/EPP)
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x1AD)   # Turbo ratio limit
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0xCE)    # PLATFORM_INFO
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0xE2)    # PKG_CST_CONFIG_CONTROL
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x778)   # MSR_CORE_C1_RESIDENCY
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x3FD)   # MSR_CORE_C6_RESIDENCY
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x3FA)   # MSR_PKG_C6_RESIDENCY
```

### IMH0 (NIO equivalent)

```python
# ACP perf limit (fid_0 only on IMH)
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.acp_perf_limit.read()

# IMH PMSB registers
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_pm_event.read()
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_virtual_sig.read()
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_telem.read()
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_electrical_req.read()

# PLR mailbox (IMH)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.command.write(0)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.domain.write(2)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.run_busy.write(1)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_data.read()
```

### Iteration Patterns

```python
# All CBBs
for cbb in sv.socket0.cbbs:
    print(cbb.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read())

# All cores in CBB0
for core in sv.socket0.cbb0.computes.cpu.modules.cores:
    print(core.thread0.msr(0x198))

# All dies (CBBs + IMH0)
for die in sv.socket0.dies:
    print(die.target_info['die_type'], die.target_info['die_instance'])
```

---

## Step 5 — PEGA C-State Injection

Used by C-state TCs to force cores into specific C-states via ucode-pcode mailbox:

```python
# PEGA encoding (CMD1 data bits for C-state commandType=0x1)
CSTATE_LUT = {
    "c6s":  0x23,   # core_cstate=0x2, core_substate=0x3
    "c6sp": 0x20,   # core_cstate=0x2, core_substate=0x0
    "c6a":  0x24,   # core_cstate=0x2, core_substate=0x4
    "c1":   0x00,   # core_cstate=0x0, core_substate=0x0
    "c0":   0xF0,   # all_bigcores=0x1, core_cstate=0xF (release)
}

# FID calculation: compute_instance * 8 % 256
# E.g., compute0 → FID = 0*8%256 = 0; compute3 → FID = 3*8%256 = 24

# Mailbox sequence: CMD1W(0x24) → CMD2W(0x26) → CMD0W(0x22)
def inject_cstate(s, cbb, fid, cstate_code):
    # CMD1W: set FID + cstate data
    cmd1_data = (fid << 8) | cstate_code
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.cmd1_data.write({cmd1_data})", wait=1)
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.opcode.write(0x24)", wait=1)
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.run_busy.write(1)", wait=2)
    # CMD2W: commandType = 0x1 (C-state)
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.cmd2_data.write(0x1)", wait=1)
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.opcode.write(0x26)", wait=1)
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.run_busy.write(1)", wait=2)
    # CMD0W: trigger
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.opcode.write(0x22)", wait=1)
    send_cmd(s, f"@sv.socket0.{cbb}.base.tpmi.pega_mailbox.run_busy.write(1)", wait=2)
```

---

## Step 6 — PLR Clipping Reason Decode

### High-level (bits 0–9 of `acp_perf_limit`)

| Bit | Reason |
|-----|--------|
| 0 | FREQUENCY |
| 1 | CURRENT |
| 2 | POWER |
| 3 | THERMAL |
| 4 | PLATFORM |
| 5 | MCP |
| 6 | RAS |
| 7 | MISC |
| 8 | QOS |
| 9 | DFC/SIMPL |

### Fine-level (bits 0–27)

| Bit | Reason |
|-----|--------|
| 0–5 | CDYN0–5 |
| 6 | FCT |
| 7 | PCS_TRL |
| 8 | MTPMAX |
| 9 | RACL |
| 10 | FAST_RAPL |
| 11 | PKG_PL1_CSR |
| 12 | PKG_PL1_TPMI |
| 13 | PKG_PL2_CSR |
| 14 | PKG_PL2_TPMI |
| 19 | PER_CORE_THERMAL |
| 21 | XXPROCHOT |
| 22 | HOT_VR |
| 23 | MCP |
| 24 | RAS |

---

## Known Environment

| Item | Value |
|------|-------|
| Server IP | `10.116.33.137` (may change — always confirm with user) |
| SSH user | `bg3` |
| Simics project | `/nfs/site/disks/simcloud_bg3_001/projects/nwp-7/2026ww23.6.00_47` |
| Simics telnet port | `4444` |
| Scripts dir (local) | `C:\github\nwp_testplan\simics\` |
| NWP CBBs | 2 (cbb0, cbb1); 48 cores each |
| NWP IMH | 1 (imh0) |

> Always ask the user to confirm the server IP — it may differ per Simics allocation.

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Commands return empty / no response | `sv.refresh()` not run yet — run it first with `--wait 15` |
| SSH tunnel drops | Re-run the `ssh -L 4444:...` command; tunnel is stateless — just reconnect |
| `@exec()` path not found | SCP the script first; use the full `/nfs/...` remote path |
| `socket.timeout` on send_cmd | Increase `wait` parameter (default 3 s); some commands need 10–30 s |
| PEGA injection no effect | Check FID calculation: `compute_instance * 8 % 256`; verify cbb mailbox opcode sequence |
| Register path not found | Run `@sv.refresh()` again; or use `discover_all_registers.py` to re-index |

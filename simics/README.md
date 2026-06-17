# NWP Simics Scripts

Reusable PythonSV / Simics CLI scripts for the NWP Simics environment.
Discovered and verified live on: nwp-7/2026ww23.6.00_47 (2026-06-10).

## Setup (one-time per Simics session)

### 1. Simics server: open telnet port

At the Simics `running>` prompt, type:
```
telnet-frontend port=4444
```

### 2. Windows: open SSH tunnel

```powershell
ssh -L 4444:localhost:4444 -N -o PreferredAuthentications=keyboard-interactive bg3@10.116.33.137
```
Type password when prompted. Leave this terminal open.

### 3. First run: initialize PythonSV

```powershell
cd C:\github\nwp_testplan\simics
python simics_cmd.py "@sv.refresh()" --wait 15
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `simics_connect.py` | Connection helper (import by others) |
| `simics_cmd.py` | One-shot command sender |
| `read_pm_registers.py` | Read ACP perf limit + IMH telemetry registers |
| `read_pstate_cstate.py` | Read P-State and C-State MSRs + PMSB registers |
| `discover_registers.py` | Discover available namednodes registers |

---

## Verified NWP Register Paths

### CBB (cbb0 / cbb1)

```python
# ACP perf limit (all FIDs, read-clears)
sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()
sv.socket0.cbb1.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()

# Single FID
sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit["fid_0"].read()

# PLR high-level mailbox (CBB)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.command.write(0)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.domain.write(2)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.run_busy.write(1)
sv.socket0.cbb0.base.tpmi.plr_mailbox_data.read()

# PLR fine-level mailbox (per core)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.command.write(0)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.domain.write(0)
sv.socket0.cbb0.base.tpmi.plr_mailbox_interface.run_busy.write(1)
sv.socket0.cbb0.base.tpmi.plr_mailbox_data.read()

# Core MSR access
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x198)   # IA32_PERF_STATUS (current freq)
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x199)   # IA32_PERF_CTL (request)
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x770)   # HWP enable
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x774)   # HWP request (min/max/desired/EPP)
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x772)   # HWP request PKG
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x1AD)   # Turbo ratio limit
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x1A0)   # IA32_MISC_ENABLES
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0xCE)    # PLATFORM_INFO
sv.socket0.cbb0.compute0.cpu.module0.core0.thread0.msr(0x19C)   # THERM_STATUS
```

### IMH0 (NIO equivalent)

```python
# ACP perf limit (fid_0 only on IMH)
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.acp_perf_limit.read()

# Available PMSB registers on IMH0:
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_pm_event.read()
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_virtual_sig.read()
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.uncore_telem.read()
sv.socket0.imh0.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.core_electrical_req.read()

# PLR high-level mailbox (IMH)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.command.write(0)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.domain.write(2)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_interface.run_busy.write(1)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_mailbox_data.read()
```

### Iteration patterns

```python
# All CBBs
for cbb in sv.socket0.cbbs:
    cbb.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()

# All cores in CBB0
for core in sv.socket0.cbb0.computes.cpu.modules.cores:
    core.thread0.msr(0x198)

# All dies (CBBs + IMH0)
for die in sv.socket0.dies:
    print(die.target_info['die_type'], die.target_info['die_instance'])
```

---

## PLR Clipping Reason Decode

### High-level (bits 0-9)
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

### Fine-level (bits 0-27)
| Bit | Reason |
|-----|--------|
| 0-5 | CDYN0-5 |
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

## Quick Commands

```powershell
# One-shot command
python simics_cmd.py "pwd"
python simics_cmd.py "@sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit.read()"

# Read all P-State / C-State registers
python read_pstate_cstate.py

# Read PM registers only
python read_pm_registers.py

# Discover registers under a path
python discover_registers.py
python discover_registers.py --path "sv.socket0.cbb0.base.punit_regs.punit_pmsb.pmsb_pcu" --search "perf"
```

# PState Stack > HGS

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Hardware-Guided Scheduling (HGS) exposes per-core performance (bit 1) and energy-efficiency (bit 19) rankings via the HW Feedback Interface, enabling the OS scheduler to steer latency-sensitive threads to the best-performing cores. Rankings are dynamically updated by PCode as thermal and power conditions change. **NWP status: ZBB'd (descoped)** — test cases carried as Runnable_On_N-1.

**Topology**:
```
PCode (per-CBB) ──evaluates core ranking (fused speed-bin + thermal state)──>
   HW Feedback table (DRAM, addr in IA32_HW_FEEDBACK_PTR 0x17D0)
     bit 1 = performance rank (higher = better)
     bit 19 = energy-efficiency rank
       └──> OS reads via CPUID leaf 6 HW Feedback capability
            └──> OS scheduler steers threads to higher-ranked cores
LVT Thermal Interrupt (IA32_PACKAGE_THERM_INTERRUPT.HW_FEEDBACK_NOTIFICATION_EN) →
   notifies OS when PCode updates HW Feedback table
```

**Key operational principle**: PCode writes per-core HW Feedback bits when core ranking changes (thermal demotion, workload shift). OS polls on interrupt notification (`HW_FEEDBACK_NOTIFICATION_LOG[26]` in MSR 0x1B1). Bit 1 decreases when core throttles thermally; restores when thermal condition clears.

**Boot activation**: BIOS programs `IA32_HW_FEEDBACK_PTR` (0x17D0) with DRAM buffer pointer and enables `IA32_HW_FEEDBACK_CONFIG` (0x17D1). HGS active from CPL3 if enabled. ZBB'd on NWP — may not be enabled.

Hardware-Guided Scheduling (HGS) is a mechanism whereby PCode ranks each core by its performance capability and exposes this ranking to the OS scheduler. The ranking is derived from per-core characterization data (speed bins, leakage, thermal position) and dynamic factors such as thermal throttling state. The OS uses these hints to steer latency-sensitive threads to the highest-performing cores.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| HW Feedback table | DRAM (per-package) | Memory-mapped structure holding per-core bit 1 (perf) and bit 19 (efficiency) rankings; updated by PCode; read by OS | Physical address from `IA32_HW_FEEDBACK_PTR` | Intel SDM |
| APIC LVT Thermal Interrupt | Per-core | Delivers `HW_FEEDBACK_NOTIFICATION` interrupt to OS when PCode updates HW Feedback table | LVT entry; `IA32_PACKAGE_THERM_INTERRUPT[HW_FEEDBACK_NOTIFICATION_EN]` | Intel SDM |
| CPUID leaf 6 | Per-core | Exposes HGS capability bits; OS discovers HW Feedback support via CPUID.06H | CPUID instruction | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct HGS role; DTS/thermal data provides input for PCode core ranking | SHORT_TELEM thermal data | ACP PM HAS |
| PCode (CBB) | CBB Base Die | Evaluates per-core performance capability from fused speed-bin + current thermal state; writes HW Feedback bit 1/19 when ranking changes; triggers LVT notification; disabled on ZBB'd NWP | `source/pcode/flows/hwpm/`; HW Feedback writer | CBB PEGA HAS |
| PrimeCode (IMH) | IMH die | No direct HGS role; thermal aggregation feeds core ranking via SOCKET_THERMAL HPM | HPM SOCKET_THERMAL | DMR Thermal HAS |
| BIOS / UEFI | Platform | Programs `IA32_HW_FEEDBACK_PTR` with DRAM buffer; enables `IA32_HW_FEEDBACK_CONFIG`; enables `HW_FEEDBACK_NOTIFICATION_EN` in `IA32_PACKAGE_THERM_INTERRUPT` | Boot-time MSR programming | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| CPUID leaf 6 | CPUID.06H | RO | HGS capability: bit 23 = HW Feedback support; OS discovers feature via CPUID | Intel SDM |
| MSR `IA32_HW_FEEDBACK_PTR` | 0x17D0 | RW | Physical pointer to HW Feedback Interface DRAM buffer (4KB aligned) | Intel SDM |
| MSR `IA32_HW_FEEDBACK_CONFIG` | 0x17D1 | RW | [0] HW Feedback Interface enable | Intel SDM |
| HW Feedback table | DRAM buffer | RO | Per-core bit 1 (performance rank) and bit 19 (efficiency rank); updated by PCode on change | Intel SDM |
| MSR `IA32_PACKAGE_THERM_INTERRUPT` | 0x1B2 | RW | `HW_FEEDBACK_NOTIFICATION_ENABLE` — notifies OS when HW Feedback table updated | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| HW Feedback ranking bits | 2 | — | Bit 1 = performance rank; bit 19 = energy-efficiency rank | Legacy Key Registers |
| PCode core ranking update | ~1 | mS | Per slow-loop; triggered when thermal state changes core rank | Legacy Execution Flow |
| HW Feedback buffer size | 4 | KB | DRAM buffer at `IA32_HW_FEEDBACK_PTR`; 4KB aligned | Intel SDM |
| NWP status | ZBB'd | — | Feature descoped; test cases carried as Runnable_On_N-1; may be re-enabled in future stepping | Legacy NWP Delta |
| OS notification latency | LVT | — | PCode → LVT Thermal Interrupt `HW_FEEDBACK_NOTIFICATION` → OS ISR reads HW Feedback | Legacy Execution Flow |

## NWP Delta

**HGS is ZBB'd (descoped) on NWP** — `FUSE_HW_SCHED_INTF_EN = 0`, so `CPUID.6.EAX[19] = 0` and the HW Feedback capability bits in EDX are not advertised.

- PantherCove BigCore does have ITD/HGS infrastructure, but it is not enabled on NWP server SKU
- 2 CBBs present; HGS flows exist in PCode but are gated by fuse
- Test cases carried as **Runnable_On_N-1** — execute on DMR emulation/HSLE, not NWP

### Validation Impact
- TCs `22021970066` (HW Feedback bit 1) and `22021970067` (HW Feedback bit 19) run on **DMR HSLE**, not NWP
- If NWP enablement decision changes, re-check `FUSE_HW_SCHED_INTF_EN` and `CR_CTAP_CR_CORE_CONFIG_0.HW_SCHED_INTF_EN`
- NWP EDX[7:0] expected: `0x00` while ZBB'd (no capabilities advertised)

---

## PSS Test Case Run Procedure — DMR HSLE

> These steps apply to TCs `22021970066` and `22021970067`. Environment: **DMR HSLE MCP SLE**. See [emulation_environment.md](../emulation_environment.md) for general setup.

### Background: HW Feedback Interface (HFI) Table Structure

PCode allocates a 4 KB DRAM buffer (registered via `IA32_HW_FEEDBACK_PTR` MSR 0x17D0) and writes one row per logical processor. BIOS sets the pointer at boot. PCode updates the rows on thermal events.

```
IA32_HW_FEEDBACK_PTR (MSR 0x17D0):
  [63:12] = physical address >> 12  (4KB aligned)
  [0]     = valid (1 = BIOS has programmed the pointer)

IA32_HW_FEEDBACK_CONFIG (MSR 0x17D1):
  [0]     = HFI enable (must = 1 for PCode to write the table)

HFI table row format (4 bytes per logical processor, indexed by x2APIC ID order):
  Byte 0: Performance capability  — 0x00 = lowest, 0xFF = highest
  Byte 1: Energy-efficiency capability — 0x00 = lowest, 0xFF = highest
  Byte 2-3: Reserved

"HW Feedback bit 1"  in TC 22021970066 = the Performance capability byte is non-zero
"HW Feedback bit 19" in TC 22021970067 = the Energy-efficiency capability byte is non-zero
```

> CPUID.6.EAX[19] = 1 is the *discovery* bit (OS asks "is HFI supported?"). The TC titles "bit 1 / bit 19" refer to capabilities as indexed in the SDM's HFI column numbering — **column 0 = performance, column 1 = energy efficiency**. Confirm exact mapping against the source TC description before running.

### Prerequisites

| Requirement | Detail |
|---|---|
| Environment | DMR HSLE (MCP SLE or MCP HSLE model); NOT NWP |
| Recommended pysv_config | `DMR_AP/MCP/HSLE/pysv_config_0.ini` (HSLE) or `DMR_AP2/MCP/SLE/pysv_config_8.ini` (SLE) |
| Full path prefix | `/nfs/site/disks/ive_pysv_dmr_001/pysv_configs/` |
| PythonSV repo | `/nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live` |
| PPR netbatch pool | `fm_zse` |
| HGS fuse | `FUSE_HW_SCHED_INTF_EN = 1` (default on DMR; verify via TAP or fuse model before submitting) |
| BIOS image | HGS-capable (do not disable "HW Feedback Interface" in BIOS Setup → Advanced Power Management) |
| Cycle budget | 1–2B cycles (HGS init happens during BIOS POST, rankings finalize shortly after CPL3) |

#### Pre-Run: Fuse Verification (TAP)

Before submitting the job, confirm HGS is fused ON in your model. In an interactive emulation session:

```python
# TAP is the most reliable for fuse reads in emulation
# Navigate: sv.socket0.cbbs[0].base -> search for FUSE_HW_SCHED_INTF_EN
results = list(sv.socket0.search('hw_sched_intf', getobj=True))
for r in results:
    print(r.path, hex(r.read()))

# If you find it directly:
# fuse_en = sv.socket0.cbb0.base.<path>.fuse_hw_sched_intf_en.read()
# print(f"FUSE_HW_SCHED_INTF_EN = {fuse_en}")  # must be 1

# Also check CR_CTAP_CR_CORE_CONFIG_0 if accessible:
# core_cfg = sv.socket0.cbb0.compute0.module0.core0.CR_CTAP_CR_CORE_CONFIG_0.read()
# print(f"HW_SCHED_INTF_EN bit = {(core_cfg >> <bit>) & 1}")
```

### Step-by-Step: Finding the Correct Namednodes Paths

Before using the scripts below, run these discovery commands in stub mode or an interactive emulation session to confirm paths exist in your model:

```python
# 1. Search for HW Feedback related nodes at socket level
for hit in sv.socket0.search('hw_feedback', getobj=True):
    print(hit.path)

# 2. Search specifically in IMH punit area (most MSRs land here in TPMI layout)
for hit in sv.socket0.imh0.punit.search('hw_feedback', getobj=True):
    print(hit.path)

# 3. If not in punit, try the ptpcioregs and ptpcfsms namespaces (known HWP location)
for hit in sv.socket0.imh0.punit.ptpcfsms.search('feedback', getobj=True):
    print(hit.path)

# 4. List all registers in the known TPMI space to spot candidates
print(sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.registers)
```

### TC 22021970066 — HW Feedback bit 1 (Performance Capability)

**Goal**: Confirm that after BIOS CPL3, `IA32_HW_FEEDBACK_CONFIG[0] = 1`, `IA32_HW_FEEDBACK_PTR[0] = 1`, and the performance capability byte in the HFI table is non-zero for every logical processor.

```python
# hw_feedback_bit1.py — TC 22021970066
# Run on DMR HSLE MCP SLE via PPR / emurun
# Replace <NAMEDNODES_PATH> placeholders with actual paths found via search() above

import namednodes
import svtools.common.baseaccess as access

try:
    import cli
    import conf
except ModuleNotFoundError:
    pass

base = access.getglobalbase()
sv = namednodes.sv.get_manager(['socket'])
sv.get_all(stop_on_error=True)

# ── Wait for model to settle after RESET_PHASE_7 ──────────────────────────────
WAIT_LOOPS    = 20
WAIT_FOR_CYCLE = 1_000_000

wait_time = 0
while wait_time <= WAIT_LOOPS:
    try:
        cli.run_command(f"emu.engine.wait-for-cycle -relative {WAIT_FOR_CYCLE}")
    except Exception:
        pass
    wait_time += 1

# ── Gate: CPL3 must be set ─────────────────────────────────────────────────────
cpl3 = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl3.read()
print(f"PM_INFO :: CPL3 = {cpl3}  (expected 1)")
if cpl3 != 1:
    print("FAIL :: CPL3 not set — BIOS did not complete. HGS result is invalid.")
    raise SystemExit(1)

# ── Step 1: IA32_HW_FEEDBACK_CONFIG (0x17D1) — must be enabled ────────────────
# TODO: Replace with confirmed namednodes path (search 'hw_feedback_config' above)
# hfi_cfg = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.<ia32_hw_feedback_config>.read()
# print(f"PM_INFO :: IA32_HW_FEEDBACK_CONFIG = {hex(hfi_cfg)}")
# if not (hfi_cfg & 0x1):
#     print("FAIL :: HW Feedback Interface not enabled by BIOS (CONFIG[0]=0)")
#     raise SystemExit(1)
# print("PASS :: HW Feedback enabled")

# ── Step 2: IA32_HW_FEEDBACK_PTR (0x17D0) — must be valid ────────────────────
# hfi_ptr_raw = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.<ia32_hw_feedback_ptr>.read()
# print(f"PM_INFO :: IA32_HW_FEEDBACK_PTR raw = {hex(hfi_ptr_raw)}")
# if not (hfi_ptr_raw & 0x1):
#     print("FAIL :: HFI table pointer not valid (PTR[0]=0) — BIOS did not set pointer")
#     raise SystemExit(1)
# hfi_base_addr = (hfi_ptr_raw >> 12) << 12   # strip valid bit, 4KB align
# print(f"PM_INFO :: HFI table base address = {hex(hfi_base_addr)}")

# ── Step 3: Read HFI table — performance capability per logical processor ──────
# HFI row = 4 bytes: [perf_cap(1B)][ee_cap(1B)][reserved(2B)]
# Reading physical memory in Simics emulation:
#   Option A — Simics conf object (if conf.phys_mem exists in model):
#       data = conf.phys_mem[0].memory.read_access(hfi_base_addr + lp_idx * 4, 4)
#       perf_cap = data[0]
#   Option B — Simics CLI read-value command:
#       val = cli.run_command(f"read-value address={hfi_base_addr + lp_idx*4} size=4")
#   Option C — via base access (if Simics base supports memory reads):
#       perf_cap = base.readmem(hfi_base_addr + lp_idx * 4, 1)[0]

# Enumerate logical processors in socket order
fail_count = 0
lp_idx = 0
for cbb in sv.socket0.cbbs:
    for compute in cbb.computes:
        for module in compute.modules:
            for core in module.cores:
                # TODO: uncomment once hfi_base_addr is resolved
                # try:
                #     data = conf.phys_mem[0].memory.read_access(hfi_base_addr + lp_idx * 4, 4)
                #     perf_cap = data[0]   # byte 0 = performance capability
                #     if perf_cap == 0:
                #         print(f"FAIL :: LP {lp_idx} (cbb={cbb.target_info.instance} "
                #               f"compute={compute.target_info.instance} "
                #               f"module={module.target_info.instance} "
                #               f"core={core.target_info.instance}) perf_cap = 0x00")
                #         fail_count += 1
                #     else:
                #         print(f"PASS :: LP {lp_idx} perf_cap = {hex(perf_cap)}")
                # except Exception as e:
                #     print(f"WARN :: LP {lp_idx} memory read failed: {e}")
                #     fail_count += 1
                lp_idx += 1

print(f"\nPM_INFO :: Checked {lp_idx} logical processors")
if fail_count == 0:
    print(f"PASS :: TC 22021970066 — All LPs have non-zero HW Feedback performance capability (bit 1)")
else:
    print(f"FAIL :: TC 22021970066 — {fail_count}/{lp_idx} LPs have perf_cap = 0")
```

### TC 22021970067 — HW Feedback bit 19 (Energy-Efficiency Capability)

**Goal**: Same setup as TC 22021970066. Additionally verify the energy-efficiency capability byte (byte 1 of each HFI row) is non-zero for at least the efficiency-class cores.

```python
# hw_feedback_bit19.py — TC 22021970067
# Same header/imports/wait/CPL3 check as hw_feedback_bit1.py above
# Paste identical preamble (imports, sv.get_all, wait loop, CPL3 gate, hfi_base_addr resolution)

# ── Step 3 (energy-efficiency variant) ─────────────────────────────────────────
fail_count = 0
zero_ee_count = 0
lp_idx = 0
for cbb in sv.socket0.cbbs:
    for compute in cbb.computes:
        for module in compute.modules:
            for core in module.cores:
                # TODO: uncomment once hfi_base_addr is resolved
                # try:
                #     data = conf.phys_mem[0].memory.read_access(hfi_base_addr + lp_idx * 4, 4)
                #     perf_cap = data[0]   # byte 0 = performance capability
                #     ee_cap   = data[1]   # byte 1 = energy-efficiency capability
                #     print(f"LP {lp_idx}: perf_cap={hex(perf_cap)}  ee_cap={hex(ee_cap)}")
                #     if ee_cap == 0:
                #         zero_ee_count += 1
                # except Exception as e:
                #     print(f"WARN :: LP {lp_idx} read failed: {e}")
                #     fail_count += 1
                lp_idx += 1

print(f"\nPM_INFO :: Checked {lp_idx} logical processors")
# Pass condition: at least 1 LP must have non-zero ee_cap
# (not all cores are guaranteed efficiency-class; high-power cores may have ee_cap=0)
if zero_ee_count < lp_idx:
    print(f"PASS :: TC 22021970067 — {lp_idx - zero_ee_count}/{lp_idx} LPs have non-zero energy-efficiency capability")
else:
    print(f"FAIL :: TC 22021970067 — ALL {lp_idx} LPs have ee_cap = 0 (PCode not writing efficiency rank)")
```

> **Note on pass condition for bit 19**: Unlike bit 1 (performance — expected non-zero for all cores), bit 19 (energy efficiency) is only expected to be non-zero for the energy-efficiency class cores. PCode policy determines how many cores receive an ee_cap value. The test passes if at least 1 core has a non-zero ee_cap.

### Running on DMR HSLE via PPR Recipe

**Step 1 — Get a PPR session**

Navigate to the HSLE portal (from ZSC15 within VNC):
- Open browser → `https://pprdmrhub.intel.com` (internal URL; requires VNC on ZSC15)
- Create a new recipe or select an existing MCP SLE FULLSTACK recipe
- Model path: check the emulation model releases at `/nfs/site/disks/dmrhub_emu_mod_000/dmrhub_emu/` for the latest `*-mcp-*-FULLSTACK` folder

**Step 2 — Copy scripts to your user area**

```bash
# From ZSC15 login shell
cp hw_feedback_bit1.py  /nfs/site/disks/ive_users_dmr_001/users/<idsid>/
cp hw_feedback_bit19.py /nfs/site/disks/ive_users_dmr_001/users/<idsid>/
```

**Step 3 — PPR recipe settings**

| Tab | Setting |
|---|---|
| Model | DMR MCP SLE FULLSTACK (latest ww release) |
| Run Commands | `run-script /nfs/site/disks/ive_users_dmr_001/users/<idsid>/hw_feedback_bit1.py` |
| Tracker flags | `-primecode_tracker_en -iosf_sb_tracker_en` (required — PCode writes HFI during boot) |
| Cycles | 1,500,000,000 (1.5B; add buffer for boot) |
| Pool | `fm_zse` / priority qslot |

**Step 4 — emurun command (manual / netbatch)**

```bash
/p/hdk/cad/emurun/1.14.1/bin/emurun \
  -ver /nfs/site/disks/dmrhub_emu_mod_002/dmrhub_emu/<latest-mcp-sle-model>/output/mcp/emu/.../ZSE5_DMR_MCP_1CBB_FULLSTACK \
  -block -debug \
  -enable_pcode_loading -enable_s3m_loading \
  -dump_fuse_memory -enable_fuse_loading \
  -primecode_tracker_en -iosf_sb_tracker_en \
  -fullstack_en \
  -nbqslot /prj/sv/dmr/dfd/priority \
  -cycles 1500000000 \
  -pythonsv.script /nfs/site/disks/ive_users_dmr_001/users/<idsid>/hw_feedback_bit1.py \
  -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live \
  -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR_AP/MCP/HSLE/pysv_config_0.ini \
  -pythonsv.base simics \
  -pythonsv_enable \
  -tap_unlock
```

> Omit `-pythonsv.start_cycle` — the default trigger (`"End of RESET_PHASE_7"`) fires after BIOS CPL3, which is the correct point to read HFI.

**Step 5 — Run TC 22021970067** in the same job using a second script slot:

```bash
  -pythonsv.script2 /nfs/site/disks/ive_users_dmr_001/users/<idsid>/hw_feedback_bit19.py
  # (no separate start_cycle2 needed — both start at RESET_PHASE_7 end)
```

### Pass/Fail Criteria

| Check | Pass | Fail | Triage |
|---|---|---|---|
| CPL3 | `rst_cpl3 = 1` | = 0 | BIOS hang — check PCode tracker for reset sequence failure; unrelated to HGS |
| `IA32_HW_FEEDBACK_CONFIG[0]` | = 1 | = 0 | BIOS did not enable HFI — check BIOS knob "HW Feedback Interface" |
| `IA32_HW_FEEDBACK_PTR[0]` | = 1 | = 0 | BIOS did not set HFI pointer — BIOS bug or DRAM training failure |
| `IA32_HW_FEEDBACK_PTR[63:12]` | Non-zero aligned address | = 0 | Same as above |
| Perf cap byte (all LPs) | Non-zero for all LPs | Any LP = 0x00 | PCode not writing ranking; check `FUSE_HW_SCHED_INTF_EN` via TAP; check PCode tracker for HGS update events |
| EE cap byte (≥1 LP) | ≥ 1 LP non-zero | All LPs = 0x00 | PCode not assigning efficiency class; check core speed-bin characterization data |

### Triage Flowchart

```
Script exits with FAIL
        │
        ├─ CPL3 = 0?
        │     └─ Yes → BIOS hang. Check PCode tracker log for reset handler failure.
        │                Not an HGS issue.
        │
        ├─ HFI_CONFIG[0] = 0?
        │     └─ Yes → BIOS did not enable HFI.
        │                File against BIOS team. Check BIOS Setup → Advanced → Power → HW Feedback.
        │
        ├─ HFI_PTR[0] = 0?
        │     └─ Yes → BIOS did not allocate HFI table.
        │                Confirm BIOS image supports HGS for this model stepping.
        │
        ├─ perf_cap = 0 for ALL LPs?
        │     ├─ Check FUSE_HW_SCHED_INTF_EN via TAP → if 0, fuse gating HGS
        │     ├─ Check PCode primecode_tracker log for "HGS" or "HW_FEEDBACK" events
        │     └─ Check if PCode has a known sighting for HGS ranking on this model drop
        │
        └─ perf_cap = 0 for SOME LPs (but not all)?
              └─ Could be thermal demotion in emulation (DTS injection issue).
                 Check DTS temp values — see emulation_environment.md §5 (DTS Injection).
                 Demoted core will have reduced perf_cap until thermal condition clears.
```

### Open Items / TODOs

- [ ] **Namednodes paths** for `IA32_HW_FEEDBACK_PTR/CONFIG` — run `sv.socket0.imh0.punit.search('hw_feedback', getobj=True)` in an interactive emulation session to confirm
- [ ] **Physical memory read API** — confirm `conf.phys_mem[0].memory.read_access(addr, 4)` works in DMR HSLE (alternative: `cli.run_command("read-value address=0x... size=4")`)
- [ ] **pysv_config selection** — confirm `pysv_config_0.ini` matches the current HSLE model drop (check model's `DOA_README.txt` for the recommended config)
- [ ] **CPUID leaf 6 check** — add `CPUID.6.EAX[19]` discovery check if CPUID is accessible in PythonSV emulation context (may require Patch23 base or core-level TPMI access)
- [ ] **TC pass condition alignment** — re-read DMR source TCs `22021970066` / `22021970067` description field to confirm whether "bit 1 / bit 19" means HFI table byte index or CPUID EAX bit index

---

## Legacy (Human-Curated Reference)

### Architecture Summary

Hardware-Guided Scheduling (HGS) is a mechanism whereby PCode ranks each core by its performance capability and exposes this ranking to the OS scheduler. The ranking is derived from per-core characterization data (speed bins, leakage, thermal position) and dynamic factors such as thermal throttling state. The OS uses these hints to steer latency-sensitive threads to the highest-performing cores.

HGS information is exposed via CPUID leaf 6 (Thermal and Power Management) and the HW Feedback Interface. Bit 1 of the HW Feedback indicates the core's relative performance ranking, while bit 19 indicates the core's energy efficiency ranking. PCode updates these feedback bits dynamically as conditions change (e.g., thermal throttling demotes a core's performance ranking).

On DMR, HGS is fully supported and validated. On NWP, HGS is **ZBB'd** (zero-base-budgeted / descoped) — the feature may not be active, and test cases are carried as Runnable_On_N-1 for future enablement.

### Execution Flow

1. **BIOS Configuration** — BIOS enables HW Feedback Interface via CPUID leaf 6 configuration. HGS-related BIOS knobs control whether core ranking is exposed.
2. **PCode Core Ranking** — During boot and periodically at runtime, PCode evaluates each core's performance capability from fused speed-bin data, silicon characterization, and current thermal state.
3. **HW Feedback Update** — PCode writes per-core performance and efficiency rankings into the HW Feedback structure accessible via CPUID leaf 6.
4. **OS Scheduler Query** — OS reads HW Feedback bits (bit 1 = performance, bit 19 = efficiency) to determine optimal core placement for threads.
5. **Dynamic Re-ranking** — If thermal conditions change (e.g., a core throttles), PCode updates the feedback bits to demote that core's ranking.
6. **Validation** — Test reads HW Feedback bit 1 and bit 19 per core and validates they reflect expected core ranking relative to fused characterization data.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| CPUID leaf 6 | CPUID.06H | Thermal/Power Management — HGS capability bits |
| IA32_HW_FEEDBACK_PTR | MSR 0x17D0 | Pointer to HW Feedback Interface memory structure |
| IA32_HW_FEEDBACK_CONFIG | MSR 0x17D1 | HW Feedback Interface enable/configuration |
| HW Feedback bit 1 | HW Feedback table | Per-core performance ranking |
| HW Feedback bit 19 | HW Feedback table | Per-core energy efficiency ranking |
| IA32_HWP_CAPABILITIES | MSR 0x771 | Per-core highest/guaranteed/efficient/lowest ratios |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | HWP capabilities and HGS context |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Core ranking in turbo context |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP HGS status (ZBB'd) |
| PCode src | `source/pcode/flows/hwpm/` | HWP/HGS flow implementation |

### Related Sightings

No HGS-specific sightings identified. Feature is ZBB'd on NWP — monitor for enablement changes.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| HGS support | Fully supported | ZBB'd (descoped) | May be re-enabled in future steppings |
| HW Feedback bits | Bit 1 + Bit 19 active | TBD | Dependent on NWP enablement decision |
| CPUID leaf 6 | HGS capability advertised | TBD | Test cases carried as Runnable_On_N-1 |
| Core ranking | Dynamic PCode ranking | N/A if ZBB'd | No core ranking if feature disabled |

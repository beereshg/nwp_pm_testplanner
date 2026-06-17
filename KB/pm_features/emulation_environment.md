# Emulation Environment — NWP PM PSS Execution Guide

> **Status**: Compiled from meeting notes, scripts, and wiki references (2026-06-02)
> **Scope**: DMR MCP HSLE / ExpressOS / NWP Simics VP — environment setup, job submission, script execution
> **Audience**: NWP PM PSS team members running TCs on emulation

---

## 1. Environment Overview

| Environment | Platform | Use Case | PythonSV Path |
|---|---|---|---|
| **SLE** (System Level Emulation) | DMR | RTL core validation — bare-metal, uBIOS only, no OS | Inline with model |
| **HSLE** (Hybrid SLE) | DMR MCP | Full BIOS + SVOS boot; Simics cores + RTL uncore; **preferred for PM TC execution** | Embedded in CTH PPR recipe |
| **XOS** (Crossover OS) | DMR | Full boot with Simics cores → jump-start switches to RTL cores | Same CTH path |
| **VP** (Virtual Platform) | DMR / NWP | Simics-only (no RTL); fastest turnaround for FW/SW validation | See Section 6 |
| ExpressOS | DMR MCP | Longer runs; A-code logs only meaningful here | Same CTH path |
| VP / Simics (ZSC2 SimCloud) | NWP | Pre-silicon bring-up; BIOS/register sweep | `/nfs/site/disks/simcloud_sys_cwf_automation/NWP/pythonsv_live_py313` |
| VP / Simics (ZSC24 Emulation) | NWP | Emulation-backed VP | `/nfs/site/disks/ip_stack_models_emu_002/pythonsv/repos/NWP` |
| DMR Simics (Local/SimCloud) | DMR | Training; PCT/RAPL/C-state walkthrough | See Section 6 |

> **Model selection for PM PSS**: Use **HSLE** — it exercises the uncore RTL (where PM logic resides) while using fast Simics cores for boot. SLE is for RTL core debug. VP is for pure FW/SW checks without emulation hardware.

> **Key rule**: PCU data reads are unreliable in DMR emulation due to incomplete support — prefer **tracker data** for validation. Direct register reads via PythonSV are the secondary source.

---

## 2. HSLE / DMR MCP Emulation

### 2.1 First-Time Access

> Full access reference: [Required Access, Queue Slots, Important Links](https://wiki.ith.intel.com/spaces/PPA/pages/4112372000/Required+Access+Queue+Slots+Important+Links) (Jeffrey Scanlon / Marcos Zavala Almanza)

#### 2.1a AGS Access Requests

Navigate to [AGS](https://ags.intel.com/identityiq/home.jsf) → Access → Submit Request For Me. Request all entitlements below. Justification: *"Working on DMR Presilicon validation for DCPS Concurrency team."*

| AGS Entitlement | Grants Access To |
|---|---|
| Simics BB User IC | Simics files in pre-si environment and Simics HSD db |
| SIMICS BB USER ITS | Simics files in pre-si environment and Simics HSD db |
| psc-hsdes-ise-contrib | Simics feature request HSDs; `presi_platforms` tenant |
| DMR IO-Max Die Blue Badge BE Users | DMR project access |
| DMR IP Blue Badge FE Users | DMR project access |
| DMR MCP Blue Badge FE Users | DMR project access |
| DPG Platform Architecture Xeon AP-SP RCS Access | OakStream PSA |
| SICG Blue Badge | Required for MIO model |
| CIGUSER Group Blue Badge | Required for MIO model |
| EC Resources SSDV Read-Write | Access to project space |
| simcld | Running VP using SimCloud |
| simcld_ts | Running VP using SimCloud |
| Artifactory Simics BB Viewer | Running VP |
| System-fw-bios doc read | — |
| PMCPU & Power Management FASD | — |
| DP PM Arch RD | Server Power Management HAS index |
| DMR CBB Power Management HAS index | — |
| PROMARK DATACENTER REPO VIEWERS | — |
| DMR IMH Co-Design | AISG-LLM-CODESIGN-SPEC-CDG-DESIGN-USER |
| DMR CBB Co-Design | AISG-LLM-CODESIGN-SPEC-PCORE-DESIGN-USER |
| DMR Core Co-Design | Co-Design_RTL_Tools |
| DMR RTL Co-Design | — |
| GSS Public Wiki Access | PM/Reset Solar Wiki |
| adl fe engineer role | DMR project access; grants `adl_rtl` group |
| c2dgusers | DMR project access |
| PHG Wiki GNR Contributor | S3M |
| Primecode Documentation Reader | PM/Reset; Primecode FAS |
| Server Firmware Primecode Viewer | PM/Reset; Primecode GitHub |
| PCODE_LNL_GITHUB_READ | PM/Reset; Pcode GitHub |
| PEG BB Current Technology Functional Design | PEG Federated Permissions |
| iVE Emulation Indicators reader | Emulation Solutions Power BI Report Server |
| emulation solutions PBIRS viewer | Emulation Solutions Power BI Report Server |
| SFIP Role release reader | PM/Reset |
| S3M FMOD access | — |
| DevTools-CJE-deg-ive-presipiev-Member | Piper Automation |
| PSC_INTEGRATION - PROJECT DEVELOPER | Piper Automation |
| PIPER - 1Source Developer | Piper Repo |

#### 2.1b Unix Accounts by Site

| Work | Site Needed | Notes |
|---|---|---|
| IMH models | **ZSC15** | Primary site for IMH emulation |
| CBB models | **SC8** | Santa Clara cluster |
| Job submission / post-processing | **FM (Folsom)** | `fm_zse` pool; all emulation NFS disks here |

Request accounts at: `https://autoops.intel.com/domains/Accounts/flows/create_unix_account` — select your home site and username; the tool shows which sites you still need.

#### 2.1c Queue Slot Access

Queue slots are controlled by PDL membership. Contact **CK (Tan, Chee Kwong)** or request PDL access at [PDL Manager](https://pdlmanager.intel.com/SearchPDL):

**PDL name: `iVE DMR Emulation SYSVAL Queue Slots`** — grants access to:

| Queue Slot | Use |
|---|---|
| `/prj/sv/dmr/sysval/bulk` | Low-priority batch |
| `/prj/sv/dmr/sysval/standard` | Regular runs |
| `/prj/sv/dmr/sysval/priority` | Faster turnaround |
| `/prj/sv/dmr/sysval/interactive` | Highest priority; quick debug |

**FFC Farm (S3M HFPGA models only):** Request PDL `PHG_Qslot_manage` → grants `/batch/phg/fpga_farm/dmr/s3m` and `ese` slots.

**Required Unix groups**: Make sure you have **`dmrips`**, **`dmrprj`**, **`dmrmcp`**, and **`cbbb_c2dg_ex`** in your active groups before running any CTH setup or model jobs.

Verify:
```bash
groups
# Expected output includes: intelall soc soc73 hdk10nm hdk7nm dmrips dmrprj cbbb_c2dg_ex dmrmcp
```

> ⚠️ **>15 group limit**: If the number of groups exceeds 15, VNC sessions may not work correctly. Run `xwashmgr` to reset the active group set to the most recent (see Section 5b).

1. Login to FM cluster: `ssh <idsid>@fm-login.fm.intel.com`
2. **Set proxy** in `~/.bashrc` or `~/.cshrc` (required for pip, wget, etc.):
   ```bash
   export http_proxy=http://proxy-dmz.intel.com:911
   export https_proxy=http://proxy-dmz.intel.com:912
   export no_proxy=127.0.0.1,localhost,intel.com
   ```
3. If password prompt appears on SSH / exit code 66 / rsync failure:
   ```bash
   # Step A: Convert keys (required after SLES11→SLES12 migration)
   /usr/intel/pkgs/sshkeygen/1.4/bin/convert_keys
   # Step B: Distribute keys to all Intel sites
   # ⚠️  MUST run from a ZSC15 shell — do NOT run from inside a Cheetah (CTH) shell;
   #     running sshkeydist inside CTH causes ALL sites to FAIL.
   #     Select ALL sites when prompted (puts SC15 as master; works with PDX, FM, SC1).
   /usr/intel/common/pkgs/sshkeydist/5.0/bin/sshkeydist
   # Step C: If still failing, regenerate from scratch
   cd ~; ssh-keygen   # accept defaults
   cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
   /usr/intel/common/pkgs/sshkeydist/5.0/bin/sshkeydist
   ```
   - Re-test: `ssh zsc15-login.zsc15.intel.com`
4. Contact **Prathima Madhu** (`pmadadi`) if key distribution does not resolve the issue.

### 2.2 CTH Environment Setup

Run once per shell session on your FM cluster login node:

```bash
# For PM PSS / MCP Emulation (HSLE — use this one)
/p/hdk/pu_tu/prd/liteinfra/1.11.SP1.p01/commonFlow/bin/cth_psetup \
    -p dmr_fe -cfg dmr_fe_dmrmcp.cth -read_only

# For DMRHUB RTL model (FE/Design — NOT for PM PSS use)
# /p/cth/bin/cth_psetup -p dmr_fe -cfg dmr_fe_dmrhub.cth -read_only
```

> **Important**: Do NOT mix CTH environments in the same shell — `dmr_fe_dmrmcp.cth` is for MCP emulation, `dmr_fe_dmrhub.cth` is for RTL simulation. Do not source both.

> Reference: DMR MCP Build and Run steps wiki — page ID `3207339393`

### 2.3 Run Area

Use the reference template run area:
```
/nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/max_base_template.32.5
```

Key subdirectories:
```
max_base_template.32.5/
  run_archive_dir/
    input_dir/
      simics_scripts/          ← place your .py and .simics scripts here
        uncore_dts_temp.simics ← IMH DTS injection (ships with model)
        hwp_tpmi_hold.py       ← HWP OOB TPMI validation script
```

### 2.3b Emulation Model Releases

Formal emulation model releases are published from the Emulation GK pipe to:
```
/nfs/site/disks/dmrhub_emu_mod_000/dmrhub_emu/
```

> **Naming caveat**: Release folder names reflect the GK pipeline date (ww+day), **not** the actual IMH RTL drop. To find the matching RTL drop, check the `socb_output` pointer inside the release folder. Examples:
> - `ww23a` emulation release → `ww23a` IMH RTL drop
> - `ww24b` emulation release → `ww24a` IMH RTL drop  
> - `ww26a` emulation release → `ww25c` IMH RTL drop

Transactors and Trackers lists (which xtors/trackers are available per model): see DMR SharePoint `IMH_Emul/` library.

### 2.4 Disk Status Check

```bash
CTH-dmr_fe> df -kh .
# Expected: ive_dmr_prednv_009  2.0T  1.6T  393G  81%
```

### 2.5 Netbatch Job Submission

```bash
# Submit a job
nbjob submit --target fm_zse --qslot /prj/sv/dmr/sysval/normal <ppr_script>

# Check your jobs
nbqstat -P fm_zse | grep <idsid>

# Web console (replace <jobid>)
# https://nbconsole.intel.com/job/fm_zse_vp.<jobid>

# Canonical status check (from PSS BKM wiki):
/usr/intel/bin/nbstatus jobs --target fm_zse --sort "JobID" \
    --fields "Status::12,User::8,Qslot::35,Class::40,timeinrunning::20,Workstation::8,includedremoteresources::8,Jobid::20" \
    "qslot=~'prj/sv/dmr/sysval'"

# Shorter form:
nbstatus jobs --target fm_zse --fields status,jobid,class::30,qslot::30,user::15,Submittime::20,TimeOnMachine::15,workstation \
    "qslot=~'/prj/sv/dmr'"

# Cancel a job
nbqrm -p fm_zse -a <jobid>
nbqrm -p zsc15_normal -a <jobid>

# Bump to priority queue for interactive debug
nbjob modify --target fm_zse --qslot /prj/sv/dmr/sysval/priority --remote-pools "FM" <jobid>

# Extend a running job (e.g. add 9h limit, 10h hard cap)
nbjob modify --target fm_zse --no-restart --exec-limit 9h:10h <jobid>

# Extend beyond 180h default max (zsc15_normal target)
nbjob modify --target zsc15_normal --exec-limits "250h:250h" "jobid=='<jobid>'"

# Monitor all feeder jobs in nbflow GUI
nbflow &

# Check queue slot permissions
nbstatus qslots --target fm_zse \
    --fields "Name::50,haspermissions('qata')::30" \
    "Name=~'/prj/sv/dmr/sysval/' && Type=='qslot' && Leaf=='true'"

# Total jobs in queue
nbstatus jobs --target fm_zse \
    --fi status,jobid,qslot::45,user,Workstation,TimeInRunning,priority,schedulingorder,SubmitTime \
    --sort schedulingOrder 'qslot=~"prj/sv/dmr/sysval"'

# Suspend / resume
nbjob suspend --target fm_zse <jobid>
nbjob resume  --target fm_zse <jobid>

# Exclude faulty emulation machines from scheduling
# Add this BEFORE the run command in your emurun .csh script:
setenv NBCLASSAPPEND "(server!='fmez5262') && (server!='fmez5072') && (server!='fmez5306')"
# (replace with actual bad server names from job failure logs)

# Check which queue slots you have permission for:
nbstatus qslots --target fm_zse \
    --fields "Name::40,haspermissions('')::30" \
    "Name=~'/prj/sv/dmr/sysval/' && Type=='qslot' && Leaf=='true'"
# Expected: bulk / interactive / priority / standard all show 'true'
```

> **Tip**: If a CRT-generated emurun has issues, go to a **known working example run** and copy the emurun from there rather than debugging the generated script.

---

## 3. PPR Recipe and Tracker Setup

### 3.1 Reducing Log Size (Critical for GUO Tracker)

1. In the PPR recipe **Run Commands** tab, identify the cycle printed at "PPR test done".
2. Set a start cycle for tracker logs equal to that cycle number.
3. This avoids capturing the entire boot phase (~hours of data for GUO tracker).

> **Rule**: Always use start cycle control for GUO tracker — it is the most resource-intensive.

### 3.2 Tracker Types

| Tracker | Name in Logs | Notes |
|---|---|---|
| IO Reg | IO reg tracker | Register read/write trace |
| Firmware Trace | fw_trace / fw_runtime_tracker | Prime Code flow trace — use for register access debug |
| P Tracker Output | P tracker | Core P-state and frequency output |
| GUO | GUO tracker | Heavy; always use start cycle control |
| PMSS | pmss tracker | Used in both emulation and post-silicon |
| GPSB | gpsb tracker | Used in both emulation and post-silicon |

> **HSLE vs ExpressOS**: A-code logs are only meaningful in ExpressOS. PMSS and GPSB trackers work in both.

### 3.3 Tracker Post-Processing — Full Commands

#### 3.3a Pcode Tracker (fast — minutes)

```bash
# Step 1: Source Cheetah environment (from FM login shell)
/p/hdk/pu_tu/prd/liteinfra/1.11.SP1.p01/commonFlow/bin/cth_psetup \
    -p dmr_fe -cfg dmr_fe_dmrmcp.cth -read_only

# Step 2: Set WORKAREA to your run output directory
# (find the path from your emurun script: cat emurun | grep '\-ver')
CTH-dmr_fe> setenv WORKAREA /nfs/site/disks/ive_dmr_cit_015/users/<idsid>/dmrmcp2-a0-<ww>_rev1_ici

# Step 3: Run pcode tracker post-processing
CTH-dmr_fe> $WORKAREA/verif/emu/scripts/trackergen/postprocess_trackers.tcsh -ptracker
```

#### 3.3b PrimeCode Tracker (slow — 2–3 days)

> ⏰ **Plan ahead**: PrimeCode post-processing takes **2–3 days** to complete. Submit early.
> Use an **ION session with high memory allocation** — standard login nodes will OOM.

```bash
# Step 1: Open an ION session (high memory)
# From VNC: use the ION sessions manager to request a high-memory allocation

# Step 2: Navigate to your test output directory
cd /nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/max_base_template.32.5

# Step 3: Source Cheetah environment
/p/hdk/pu_tu/prd/liteinfra/1.11.SP1.p01/commonFlow/bin/cth_psetup \
    -p dmr_fe -cfg dmr_fe_dmrmcp.cth -read_only

# Step 4: Set WORKAREA
CTH-dmr_fe> setenv WORKAREA /nfs/site/disks/ive_dmr_cit_015/users/<idsid>/dmrmcp2-a0-<ww>_rev1_ici

# Step 5: Disable Netbatch (run locally on ION node instead of submitting to queue)
CTH-dmr_fe> setenv DISABLE_NETBATCH 1

# Step 6: Run primecode tracker post-processing
CTH-dmr_fe> $WORKAREA/verif/emu/scripts/trackergen/postprocess_trackers.tcsh -primecode
```

> **Monitoring**: Use `nbstatus jobs --target fm_zse` to check status while waiting.
> **New decoder path**: The PrimeCode team delivered a new trace decoder that reduces processing to **hours** instead of days. Contact **Jeffrey Scanlon** (`jscanlo1`) for the latest script. Integration into default recipes is pending.

### 3.4 CRT Job Submission (alternative to raw emurun)

CRT (`zapo_crt`) is the standard high-level interface for submitting emulation jobs from a PPR recipe ID. It generates the emurun command automatically.

#### 3.4a Environment Setup

Every CRT run script must start with:

```bash
#!/usr/intel/bin/tcsh
setenv PATH /p/hdk/cad/zapo_crt/latest/bin:${PATH}
setenv NB_WASH_ENABLED 1
setenv NB_WASH_GROUPS intelall,soc,soc73,shdk73,hdk7nm,adl_rtl,adl,gnr74,gnr76,cicg,c2dgusers,dmrips,dmrprj,cbbb_c2dg_ex,dmrmcp
```

#### 3.4b Full CRT Example: HSLE Run with Trackers

PPR release page: [IMH2 MCP ICI HSLE PPRs](https://wiki.ith.intel.com/spaces/PPA/pages/4348052253/IMH2+MCP+ICI+HSLE+PPRs)

```bash
crt -rid 40584 -bf mcp_ici_hsle_svos \
    --er \
    -nbqslot /prj/sv/dmr/sysval/priority \
    -c 4000000000 \
    -netbatch_opts '--log-file-dir /tmp/netbatch' \
    -mail 'S E' \
    -pythonsv_enable \
    -pythonsv.base simics \
    -pythonsv.logging \
    -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live \
    -pythonsv.script /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pstates/hwp_tpmi_hold.py \
    -p_tracker_en \
    -primecode_tracker_en \
    -acode_tracker_en \
    -iosf_sb_tracker_en \
    -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini \
    -pythonsv.start_condition "'@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")'"
```

#### 3.4c CRT Flag Reference

| Flag | Description | Example |
|---|---|---|
| `-rid` | Recipe ID from PPR portal | `40584` |
| `-bf` | Boot flow template | `mcp_ici_hsle_svos` |
| `--er` | Enable emurun generation (required) | — |
| `-nbqslot` | Netbatch queue slot | `/prj/sv/dmr/sysval/priority` |
| `-c` | Cycle count | `4000000000` (4B) |
| `-mail 'S E'` | Email notifications at Start and End | — |
| `-pythonsv_enable` | Enable PythonSV framework | — |
| `-pythonsv.script` | Test script path | `.../hwp_tpmi_hold.py` |
| `-pythonsv.start_condition` | When to trigger test (see below) | `PPR_TEST_DONE` |
| `-p_tracker_en` | Enable pcode tracker | — |
| `-primecode_tracker_en` | Enable primecode tracker | — |
| `-acode_tracker_en` | Enable acode tracker | — |
| `-iosf_sb_tracker_en` | Enable IOSF sideband tracker | — |

#### 3.4d PPR_TEST_DONE Start Condition (SVOS Boot)

For HSLE runs where SVOS boots fully, the preferred start condition is:

```bash
-pythonsv.start_condition "'@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")'"
```

This waits for the string `PPR_TEST_DONE` to appear in the Simics device log (written by the BIOS PPR hook at end of UEFI POST). Use this instead of the raw `RESET_PHASE_7` default when running with a full BIOS stack that has PPR integration.

| Start condition | When to use |
|---|---|
| (default — RESET_PHASE_7) | Simple SLE/bare-metal runs; no BIOS PPR hook |
| `PPR_TEST_DONE` via `wait_for_log` | HSLE/SVOS runs with full BIOS stack (standard PSS runs) |
| `-pythonsv.start_cycle <N>` | Specific cycle synchronization; overrides all conditions |

> **Also note the new ICI pysv_config path format**: `DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini` — the `DMR/AP2/M7/` prefix corresponds to the M7 milestone model series (ICI = Inter-Chiplet Interconnect model). Add to lookup table when you confirm the exact milestone tag for your model.

---

## 4. PythonSV Script Execution on HSLE

### 4.0 Key Paths and Repositories

| Resource | Path |
|---|---|
| Live PythonSV repo (AP + AP2, Python 3.10) | `/nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live` |
| Static repos | `/nfs/site/disks/ive_pysv_dmr_001/pythonsv_static_repos` |
| pysv_config root | `/nfs/site/disks/ive_pysv_dmr_001/pysv_configs/` |
| Plugin (NIO/SC Z24) | `/nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/site-packages/pysvtools/server_wave_5/emulation/pythonsv.pm` |
| User run area | `/nfs/site/disks/ive_users_dmr_001/users/<idsid>` |
| Emulation model releases | `/nfs/site/disks/dmrhub_emu_mod_000/dmrhub_emu/` |

### 4.0b Selecting the Right pysv_config

Pick the `pysv_config_N.ini` matching your model release. Pass it with `-pythonsv.stub <path>`.

**MCP HSLE (most common for PM PSS):**

| Model | pysv_config |
|---|---|
| DMR-MCP SoC ICI Hybrid EPR - V15 (25ww26a RTL) | `DMR_AP/MCP/HSLE/pysv_config_0.ini` |
| DMR-MCP SoC ICI Hybrid EPR - V14 (25ww14b RTL) | `DMR_AP/MCP/HSLE/pysv_config_1.ini` |
| DMR-IMH 1-die Hybrid EPR - Tape-In (25ww13a RTL) | `DMR_AP/IMH/HSLE/pysv_config_0.ini` |
| DMR-IMH2 1-die Hybrid EPR - M4 (25ww22a RTL) | `DMR_AP2/IMH2_A0/HSLE/pysv_config_0.ini` |
| DMR MCP ICI (M7 milestone, from CRT example) | `DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini` |

**MCP SLE (most recent AP2 releases):**

| Model | pysv_config |
|---|---|
| DMR MCP AP2 1CBB M5A FULLSTACK (25ww33b RTL M5A.0, 25ww35.4) | `DMR_AP2/MCP/SLE/pysv_config_8.ini` |
| DMR MCP AP2 1CBB M4 FULLSTACK (25ww23a RTL M4.2, 25ww28.6) | `DMR_AP2/MCP/SLE/pysv_config_1.ini` |
| DMR MCP SoC 1CBB V15 FULLSTACK (MCP ww26a RTL V15.2, 25ww33.1) | `DMR_AP/MCP/SLE/pysv_config_0.ini` |
| DMR MCP SoC 1CBB V14 FULLSTACK (MCP ww14b RTL V14.1, 25ww19.5) | `DMR_AP/MCP/SLE/pysv_config_2.ini` |

> All paths are relative to `/nfs/site/disks/ive_pysv_dmr_001/pysv_configs/`. Use the full path in `-pythonsv.stub`.

### 4.0c pysv_config.ini Key Parameters

```ini
[baseaccess]
access = simics
project = diamondrapids

[diamondrapids]
num_imhs = 2          # number of IMH dies PythonSV will discover
num_sockets = 1
module_count = 8      # modules per CBB
core_count = 2        # cores per module
num_cbbs = 4
emulation = true
stub_subaccess = offline
simics_subaccess = emulation
sleep_cycles_per_second = 1
simics_platform_mb = oakstream.mb    # required for core discovery
new_spark_flow = True                # hybrid (dynamic) discovery

[simicsmailbox_baseaccess]
service = iasm
scratchpad = sideband
sb_spads_die_type = imh
sb_spads_network = gpsb
sb_spads_mode = rtl
sb_xtor_instance_name = socket0_imh0_gpsb
```

> **Note**: Dynamic (`new_spark_flow = True`) discovery may remove devices not present in the model. Static discovery (older configs) may fail if expected devices are missing. Follow the model's PythonSV DOA parameters where possible.

### 4.0d emurun Command Structure (Netbatch)

Full example for PM validation (HSLE, MCP SLE model):

```bash
/p/hdk/cad/emurun/1.14.1/bin/emurun \
  -ver /nfs/site/disks/dmrhub_emu_mod_002/dmrhub_emu/dmrhub_emu-a0-dmrhub-25ww05e/output/imh/emu/zebu_zebu/ZSE5_DMR_IMH_FULL_FULLSTACK \
  -block -debug \
  -enable_pcode_loading -enable_s3m_loading -dump_s3m_memory \
  -dump_fuse_memory -enable_fuse_loading \
  -enable_metro_portal -enable_4cbb_ls \
  -primecode_tracker_en -iosf_sb_tracker_en \
  -pm_collector_tracker_en -fullstack_en \
  -enable_pm_hlm -disable_pm_periodic_hlm \
  -nbqslot /prj/sv/dmr/sysval/priority \
  -cycles 1800000000 \
  -pythonsv.script /nfs/site/disks/ive_pysv_dmr_001/.../your_script.py \
  -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live \
  -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR_AP2/MCP/SLE/pysv_config_8.ini \
  -pythonsv.logging \
  -pythonsv.base simics \
  -pythonsv_enable \
  -tap_unlock \
  -configdb_override .../1imh_1s_4cbb/artifactory_bypass_non_pcie.dut_cfg \
  -test .../verif/emu/runtime/tests/mem_evs_pysv \
  -aced_dis
```

**Interactive mode** (add `-i`, change qslot to `interactive`):
```bash
# Same as above but with:
  -nbqslot /prj/sv/dmr/sysval/interactive -i
# (omit -pythonsv.script for interactive session)
```

**From Simics script** (after model boots, inside `.simics` file):
```simics
script-branch {
    oakstream.serconsole.con.wait-for-string string = "end diamondrapidssetupenv"
    emu.engine.wait-for-cycle 10000 -relative
    @SIM_log_info(1,emu.devices,0,"PPR: Running PythonSV DOA")
    run-python-file /nfs/site/disks/ive_dmr_prednv_009/hmirand/PythonSV_DOA/pythonSV_DOA.py
    exit -f
}
```

**Key emurun PythonSV switches:**

| Switch | Type | Description |
|---|---|---|
| `-pythonsv.script <path>` | String | Python script to run |
| `-pythonsv.script2..5 <path>` | String | Additional scripts (up to 5 in parallel) |
| `-pythonsv.path <path>` | String | Override default PythonSV repo path |
| `-pythonsv.stub <path>` | String | pysv_config.ini to use |
| `-pythonsv.base simics` | String | Base access (`simics`, `simicsmailbox`, `ipc`) |
| `-pythonsv.start_cycle <N>` | Int | Absolute cycle to start script (default: end of RESET_PHASE_7) |
| `-pythonsv.start_cycle2..5 <N>` | Int | Per-script start cycles |
| `-pythonsv.start_condition '<expr>'` | String | Simics condition to trigger start (overridden by start_cycle) |
| `-pythonsv.logging` | Bool | Write per-script log file instead of printing to Simics prompt |
| `-pythonsv_enable` | Bool | Enable PythonSV (implicit if any `-pythonsv.*` used) |

> **Default start**: If neither `start_cycle` nor `start_condition` is given, script starts at `"End of RESET_PHASE_7 for socket 0"`. **Cycles take priority over conditions** — if both are set, condition is ignored.

### 4.0e Base Access Matrix

| Register Type | Simics (Emulation) | Simics (VP) | TAP (Emulation) |
|---|---|---|---|
| mem | ✓ | ✓ | ✓ |
| pcicfg | ✓ | ✓ | ✓ |
| msr | ✓ | ✓ | ✓ |
| patch23 | ✓ | ✓ | ✓ |
| crb | ✗ | ✗ | ✓* |

> *Simics in Emulation has different capabilities compared to Virtual Platform.

**Access methods per register type (Simics base):**

| Register | Simics | TAP |
|---|---|---|
| Sideband Mem | Spark2iosfsb | Tap2iosf |
| PCU | Patch 23 | Pcu Tap |
| Sideband CR | Spark2iosfsb | Tap2iosf |
| Sideband Cfg | Spark2iosfsb | Tap2iosf |
| Fscp (core) | Patch 23 | — |
| Fuses | Spark2iosfsb | TAP ✓ (most reliable) |
| Pcode IO map | Patch 23 | Pcu Tap |

> **Fuse access**: TAP is the most widely tested method in emulation — use TAP for fuse reads. Simics/Fuse controller responds but semaphore behavior is inconsistent (0xffffffff on VP).

### 4.0f Stub Mode (Offline Script Testing)

Test scripts offline without submitting a job — for syntax/hierarchy/register-path checks only. Values will differ from live emulation.

```python
# Setup PYTHONPATH first (from a plain ZSC15 shell, not CTH):
# setenv PYTHONPATH <pythonsv_repo>:<pythonsv_repo>/site-packages
# Run: /usr/intel/pkgs/python3/3.10.8/bin/python3.10

from svtools.common.pysv_config import CFG
CFG.baseaccess.access = 'stub'
import namednodes
sv = namednodes.sv.get_manager(['socket'])
sv.get_all()
# Now access sv.socket0.<node> registers

# Execute a script in stub mode:
exec(open('/nfs/site/disks/ive_pysv_dmr_001/.../your_script.py').read())
```

User run area for stub sessions: `/nfs/site/disks/ive_users_dmr_001/users/<idsid>`

### 4.0g Manual IOSFSB Transactions

```python
import pysvtools.nn_accesses.spark.iosfsb_spark as sc
# Instance ID values:
# socket0_imh0_gpsb  → IMH GPSB
# socket0_imh0_pmsb  → IMH PMSB
# socket0_cbb0_gpsb  → CBB GPSB
# socket0_cbb0_pmsb  → CBB PMSB
sc.iosfsb_spark(args)
```

### 4.0h start_emulation.py Internals

`start_emulation.py` is the Simics-side Python file that runs inside the emulation engine (not your user script). It initializes PythonSV, configures the base access, waits for the correct start condition, then launches your script in a Simics script-branch thread.

**Reading variables from the emurun plugin (`cmd_line_opt`):**

```python
# Safe pattern — check attribute exists before reading:
pysv_script = cmd_line_opt.pythonsv_script if hasattr(cmd_line_opt, 'pythonsv_script') else None
pysv_stub   = cmd_line_opt.pythonsv_stub   if (hasattr(cmd_line_opt, 'pythonsv_stub') and cmd_line_opt.pythonsv_stub) else 'stub_name.ini'
pysv_base   = cmd_line_opt.pythonsv_base   if (hasattr(cmd_line_opt, 'pythonsv_base') and cmd_line_opt.pythonsv_base) else 'simics'
```

> Always use `hasattr` — plugin variables can differ between emurun versions.

**Creating a script branch (Simics threading):**

```python
# PythonSV runs in a free-running script branch inside Simics
sb_create(run_pythonsv_branch)   # spawns your function as a Simics thread
# Up to 5 scripts can run in parallel (each in their own branch)
```

**Start conditions inside the branch function:**

```python
def run_pythonsv_branch():
    if cmd_line_opt.pythonsv_start_cycle != 0:
        # Wait for an absolute cycle count
        cli.sb_wait_for_cycle(conf.emu.engine, cmd_line_opt.pythonsv_start_cycle,
                              reverse=False, always=False, relative=False)
    else:
        # Wait for a Simics expression (e.g. a signal going high)
        cli.run_command("emu.engine.wait-for-expression expression = $test")
    # --- your PythonSV code runs here ---
```

> A common new-project issue is an incorrect signal trigger — verify the signal maps to BIOS starting up.

**Base access initialization:**

| Base | What `start_emulation.py` does |
|---|---|
| `simics` (sideband) | Nothing — socket discovery code handles it |
| `simicsmailbox` | Runs SMBA init: sets `did`, scratchpad paths, timeout parameters |
| `ipc` (OpenIPC) | Launches a shell script: `pythonsv_ipc.sh <ipc_path> <pysv_path> <stub> <script>` |

**CFG and path setup:**

```python
sys.path.insert(0, pysv_path)
from svtools.common.pysv_config import CFG
CFG.project.stub_offline_socket = pysv_stub
CFG.project.segment  = pysv_stub[0:6]
CFG.project.stepping = pysv_stub[7:9]
dies = pysv_stub[10:12]
CFG.project.dies     = "normal" if dies == "4d" else "hvm"
CFG.project.milestone = pysv_stub[13:16]
```

**Logging:** stdout redirect to a per-script log file; disabled by default since it can interfere with tracker outputs. Enabled via `-pythonsv.logging` in emurun.

**Minimal template skeleton:**

```python
import cli, conf, os, sys, subprocess

pysv_path   = os.getenv('PYSV_PATH', None)
pysv_stub   = cmd_line_opt.pythonsv_stub if (hasattr(cmd_line_opt,'pythonsv_stub') and cmd_line_opt.pythonsv_stub) else 'stub.ini'
pysv_script = cmd_line_opt.pythonsv_script if hasattr(cmd_line_opt,'pythonsv_script') else None
pysv_base   = cmd_line_opt.pythonsv_base if (hasattr(cmd_line_opt,'pythonsv_base') and cmd_line_opt.pythonsv_base) else 'simics'

def run_pythonsv_branch():
    if cmd_line_opt.pythonsv_start_cycle != 0:
        cli.sb_wait_for_cycle(conf.emu.engine, cmd_line_opt.pythonsv_start_cycle,
                              reverse=False, always=False, relative=False)
    else:
        cli.run_command("emu.engine.wait-for-expression expression = $test")

    if pysv_script and not cmd_line_opt.interactive:
        if os.path.isfile(pysv_script):
            exec(open(pysv_script).read())
        else:
            print("PythonSv - INFO: No script found. Exiting.")
            run_command("exit")
    elif cmd_line_opt.interactive:
        print("PythonSv - INFO: Interactive mode — attach telnet or xterm.")

if pysv_path:
    sys.path.insert(0, pysv_path)
    sys.path.insert(0, os.path.join(pysv_path, 'lib/python3.10/site-packages'))
    from svtools.common.pysv_config import CFG
    CFG.project.stub_offline_socket = pysv_stub
    sb_create(run_pythonsv_branch)
else:
    print('PythonSv - ERROR: PYSV_PATH not set')
```

> The full upstream template lives on the FV Common wiki under **Emulation Enabling → Emulation files → start_emulation.py**. The skeleton above is adapted for DMR/NWP usage.

### 4.1 Script Invocation (in PPR recipe Run Commands tab)

```simics
run-script /nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/max_base_template.32.5/run_archive_dir/input_dir/simics_scripts/hwp_tpmi_hold.py
```

### 4.2 Emulation Wait Pattern

Scripts must use cycle-waits to allow firmware flows to complete. Use `emu.engine.wait-for-cycle` inside a loop:

```python
import cli

WAIT_LOOPS = 20        # 20 iterations
WAIT_FOR_CYCLE = 1000000  # 1M cycles per iteration = 20M total

wait_time = 0
while wait_time <= WAIT_LOOPS:
    try:
        cli.run_command(f"emu.engine.wait-for-cycle -relative {WAIT_FOR_CYCLE}")
        sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.read()
    except NameError:
        break  # cli not available (VP context)
    wait_time += 1
```

> **Why this matters**: PrimeCode receives TPMI writes immediately, but the OOB state latch downstream takes 5–20M cycles to converge. Without this wait, jobs exit before `oob_enabled` transitions.

### 4.3 Emulation vs VP Behavior

```python
# Guard all CLI calls — emu.engine commands raise CliError in VP
try:
    cli.run_command("emu.engine.wait-for-cycle -relative 1000")
except cli.errors.CliError:
    print("PM_INFO :: VP context — cycle wait skipped")
except NameError:
    pass  # cli not available at all
```

### 4.4 Key PythonSV Namednodes for PM Validation

```python
# CPL status — verify boot completed correctly
sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl1.read()
sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl2.read()
sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl3.read()
sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.bios_reset_cpl_cfg.rst_cpl4.read()

# HWP TPMI capability / controls
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_capability.lowest_performance.read()
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_capability.highest_performance.read()
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.read()
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.min.write(1)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.max.write(1)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.minimum_performance.write(val)
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.maximum_performance.write(val)

# Core ratios
sv.sockets.cbbs.computes.modules.cores.ucode_cr_perf_status.core_ratio_100mhz.read()

# MISC_PWR_MGMT2 — OOB autonomous enable check
# CR register at 0x4a90; check ENABLE_OUT_OF_BAND_AUTONOMOUS field
```

### 4.5 PCU Data Limitation

PCU data reads via direct script are **unreliable** in DMR emulation. Always prefer tracker log data for validation. If PCU data is needed, use ExpressOS environment.

---

## 5. DTS Injection Scripts

Reference thermal injection scripts for thermal TC execution:

| Script | Location | Notes |
|---|---|---|
| CBB DTS inject | `/nfs/site/disks/ive_dmr_prednv_009/aprakas2/SLE/harasser/thermal/pm_mcp_oos_harasser_time0_all_cbb_dts_inject.simics` | Manually created for CBB; use as reference for new scripts |
| IMH DTS inject | `/nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/max_base_template.32.5/run_archive_dir/input_dir/simics_scripts/uncore_dts_temp.simics` | Ships with model; attach directly in recipe |

Contact **Aditya1 Prakash** (`aprakas2`) for additional DTS initialization scripts from DMR thermal validation.

---

## 5b. VNC Session Requirements (ZSC15)

| Requirement | Value |
|---|---|
| Site | Santa Clara Zone 15 (ZSC15) |
| VNC Group | `/xpg/vnc` — do not use this directly; get a `*/lvtool` ION tool session |
| OS | SLES12 machine |
| Min RAM for turnin | 8 GB |
| Max active groups | **128 per VNC session** — manage with `xwashmgr &` or `wash -n` |

> If you hit group errors in ZSC15, run `xwashmgr &` and remove unused groups before retrying the build or job submission.

> If your CTH setup or `grdlbuild` has feeder issues or jobs stuck in WL: open `nbflow`, remove old feeders, exit nbflow, then run `rm -rf $HOME/nbtarget /tmp_proj/nbfeeder_logs_${USER}` and retry.

---

## 6. NWP Simics / VP Setup (SimCloud ZSC2)

### 6.1 One-Time SimCloud Work Area Creation

1. Go to [DesignCAM Allocation Manager](https://designcam.intel.com/index.html#!/create/disk)
2. Site: **PDX**, Business Group: **IJGS** (or your BG)
3. Disk: `/nfs/site/disks/simcloud_<idsid>_001` (ZSC2)
4. Unix group: `simcld_nwp` (request on AGS first)
5. Submit → approval email in ~15 minutes

> **NWP-specific**: Do NOT reuse DMR disk — different access group (`simcld_nwp` vs `simcld_dmr`).
> Reference announcement: Jose Aguilar Bravo, May 5, 2026 Simics Newport channel.

### 6.2 ISPM / SimLauncher Setup (NWP, ZSC2 VNC)

```bash
# Download launcher
wget https://af-simics.devtools.intel.com/artifactory/simics-repos/pub/simics-installer/intel-internal/1.17.0/ispm-internal-cli-1.17.0-linux64.tar.gz
tar -xf ispm-internal-cli-1.17.0-linux64.tar.gz

# Auth
./ispm settings generate-auth-file
# Choose: Use credentials to generate, save to ~/ispm_auth_keys.config

./ispm config default-project-dir $PWD/projects/

# Create NWP project (use latest manifest)
./ispm platforms --auth-file ~/ispm_auth_keys.config \
    --create-project --manifest "nwp-7" \
    --manifest-version 2026ww13.3.07_39 \
    --install-dir nwp-7-2026ww13.3.07_39/ \
    --non-interactive --trust-insecure-packages

cd projects/my-intel-simics-project-1/
xterm -e ./simics newport/1_socket_1_accel-generic --preset presets/cxl_disable_wa &
```

### 6.3 NWP VP with SimCloud (simlauncher)

```bash
# Set Python version for NWP (3.13)
setenv SIMICS_PYTHON /usr/intel/bin/python3.13.2

simlauncher run nwp-7 2026ww14.1.21_16 \
    --cores 4 --memory 64 --disk 64 \
    --mode vnc --image sles15

# On the VNC session that opens:
unsetenv SIMICS_PYTHON
./simics newport/1_socket_1_accel-generic
run-script /nfs/site/disks/simcloud_sys_cwf_automation/NWP/pythonsv_live_py313/newport/startnwp_simics.py
@sv.refresh()
```

### 6.4 DMR Simics (from Windows laptop)

```cmd
C:\Python314> python.exe -m venv venv
C:\Python314> venv\Scripts\activate
set http_proxy=http://proxy-dmz.intel.com:911
set https_proxy=http://proxy-dmz.intel.com:912
pip install https://af02p-or.devtools.intel.com/artifactory/simics-local/incoming/methodology/devtools/stable_launchers/devtools_launchers-2026.4.29.2-py3-none-any.whl
dtconfig setup
# Enter generated token from https://tokenmanagementservice.swiss.intel.com/
# Enter SimCloud workarea path

simlauncher run dmr-7 2026ww22.2.00_03 --cores 16 --memory 256 --disk 256 --mode vnc --sles 12
```

Then on the VNC:
```bash
# Download OS image
wget https://af01p-or.devtools.intel.com/artifactory/linuxbkc-or-local/linux-stack-bkc-dmr/2026ww20/...

# Launch Simics
./simics "oakstream-rio/1_socket_ucc-aunit-cbbpunit-ese-icode-imhpunit-oobmsm-s3m" \
    disk_image="/nfs/site/disks/simcloud_<idsid>_003/projects/dmr-rio-7/os/dmr-bkc-centos-stream-10-coreserver-6.18-8.4-9.craff" \
    'ifwi_build_type=["debug"]'
```

### 6.5 PythonSV Setup (NWP — Linux shell)

```bash
# Download and run setup script (Python 3.10 for DMR, 3.13 for NWP)
wget <setup310.sh_url_from_team>
bash setup310.sh   # clones repo, installs tools, sets env vars

# NWP PythonSV paths
# ZSC2 (SimCloud VP):  /nfs/site/disks/simcloud_sys_cwf_automation/NWP/pythonsv_live_py313
# ZSC24 (Emulation):   /nfs/site/disks/ip_stack_models_emu_002/pythonsv/repos/NWP
```

> **Python version management**: Use separate VNC sessions and run folders for DMR (Python 3.10) and NWP (Python 3.13). Do not mix in a single VNC session.

### 6.6 SSL Certificate Fix (SLES15 / SimCloud)

```bash
export SSL_CERT_FILE=/etc/ssl/ca-bundle.pem
export REQUESTS_CA_BUNDLE=/etc/ssl/ca-bundle.pem
```

### 6.7 PythonSV Startup in VP / Simics

After Simics boots to desired state (BIOS menu or SVOS):

```simics
# From Simics CLI:
run-script /nfs/site/disks/<pythonsv_path>/start_dmr.py
# or for NWP:
run-script /nfs/site/disks/simcloud_sys_cwf_automation/NWP/pythonsv_live_py313/newport/startnwp_simics.py
```

Then switch between Simics CLI (`@`) and PythonSV shell (`quit` from PythonSV drops back to Simics).

---

## 7. BIOS Menu Navigation for VP Test Cases

### 7.1 Access BIOS Menu (no OS boot)

In PPR recipe or Simics launch: remove or set `os_type` to non-SVOS value to halt at BIOS.

```simics
./simics <target> --no-run
# Boot and halt at BIOS menu
```

Then navigate: **EDKII → Socket Configuration → Advanced Power Management → HWP / PCT settings**

### 7.2 PCT-Specific Knobs

| Knob | Path | NWP Note |
|---|---|---|
| PCT Partition Count | Advanced PM → PCT | Negative validation: set invalid count |
| High Priority Module Selection | Advanced PM → Module Config | Sets which modules are HP |
| HWP Mode | Advanced PM → Hardware PM State Control | Native / OOB / Disabled |
| EPP Profile | Advanced PM → Energy Perf Preference | Power / Balanced / Performance |

### 7.3 YAML / Fuse Override Files

YAML files replace legacy `.sh` files for specifying:
- Fuse overrides (e.g., core count, PCT enable)
- BIOS knob settings

Contact **Ishan Saxena** (`isaxena`) for the DMR YAML reference file and PNP team contacts for correct fuse values.

> **Important**: Incorrect fuse values have caused hangs in past runs. Always get values from the architect or team before using in a job.

---

## 8. RAPL Validation Steps (Manual — no script available)

For socket RAPL TCs where scripts are not yet available:

```python
# Step 1: Read current RAPL PL1 limit via TPMI in-band
./pmutil_bin -tR PKG_POWER_LIMIT

# Step 2: Set a low PL1 to induce throttling (via TPMI OOB or PythonSV write)
# OOB path:
python oob_tpmi_access.py --write -r PKG_POWER_LIMIT -s 0 -i 0 --value <low_watts>

# Step 3: Monitor perf status counter (should increment when throttled)
sv.socket0.imh0.punit.perf_status.read()

# Step 4: Check PEM status bits and core/mesh ratios
sv.socket0.imh0.punit.pem_status.read()
sv.sockets.cbbs.computes.modules.cores.ucode_cr_perf_status.core_ratio_100mhz.read()
```

Contact **Aditya Prakash** (`aprakas2`) or **Chetan** for manual steps and existing recipe references.

---

## 9. HWP PCT Core Frequency Validation

For PCT TCs (Priority Core Turbo):

```python
# Step 1: Enable HWP on all cores
for core in sv.sockets.cbbs.computes.modules.cores:
    core.write_msr(0x770, 1)   # IA32_PM_ENABLE

# Step 2: Request maximum frequency
for core in sv.sockets.cbbs.computes.modules.cores:
    core.write_msr(0x774, 0x2525)  # IA32_HWP_REQUEST min=max=tpmi_max

# Step 3: Read back PERF_STATUS and confirm HP cores have higher ratio than LP cores
import cli
cli.run_command("emu.engine.wait-for-cycle -relative 5000000")
sv.sockets.cbbs.computes.modules.cores.ucode_cr_perf_status.core_ratio_100mhz.read()

# Step 4: Check TPMI clause config registers for HP/LP assignments
sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.opc_hwp_controls.read()
```

---

## 10. Known Issues and Workarounds

| Issue | Root Cause | Workaround |
|---|---|---|
| OOB enable bit not seen after TPMI write | Job exits too early — PrimeCode flow takes 5–20M cycles | Add 20M-cycle tail wait loop with register readback (see Section 4.2) |
| PCU data reads return 0 or stale in HSLE | PCU data collection incomplete in DMR emulation model | Use tracker data instead; switch to ExpressOS for PCU data |
| NumPy error launching NWP Simics | Python version mismatch or package incompatibility | Use exact release and command from Anjana's working config; try previous manifest version |
| Exit code 66 / rsync failure on FM cluster | SSH key not distributed across sites | Run `convert_keys` first, then `sshkeydist` with full path `/usr/intel/common/pkgs/sshkeydist/5.0/bin/sshkeydist`; regenerate with `ssh-keygen` if still failing |
| SSH password prompt after SLES12 migration | Key format changed between SLES11 and SLES12 | Run `/usr/intel/pkgs/sshkeygen/1.4/bin/convert_keys` before `sshkeydist` |
| `sshkeydist` makes all remote sites fail | Ran `sshkeydist` inside a Cheetah (CTH) shell | Exit CTH first; run `sshkeydist` from a plain ZSC15 login shell; select ALL sites |
| Artifactory SSL cert error in Simics | Outdated/self-signed cert in package | Switch to previous release; contact Simics team for updated URL |
| TPMI min/max reads return 0 | Model not yet initialized | Script auto-overrides to min=8/max=32; re-read after CPL3 |
| Interactive qslot job not picked up | Using `-I` flag without correct qslot | Use priority qslot explicitly via `nbjob modify`; do not use autorun (deprecated) |
| Autorun deprecated | Misuse in shared cluster | Use `--no-run` and manual Simics CLI instead |

---

## 11. Contacts and Resources

### 11.1 Team Contacts

| Role | Name / Contact | Topic |
|---|---|---|
| PM PSS scripts / VP walkthrough | Ishan Saxena (`isaxena`) | PCT/HWP scripts, TPMI, BIOS knob setup |
| RAPL / thermal / DTS injection | Aditya Prakash (`aprakas2`) | RAPL manual steps, DTS register mapping |
| PythonSV recipes / OOB debug | Jeffrey Scanlon (`jscanlo1`) | Tracker setup, PrimeCode decoder |
| FM cluster / model release | Prathima Madhu (`pmadadi`) | SSH issues, model onboarding |
| NWP SimCloud setup | Jose Aguilar Bravo | SimCloud NWP disk/group |
| DTS/thermal (Chetan) | Chetan (ask team) | CBB DTS, RAPL reference recipes |
| SOC Val / RTL thermal | Shaheen (ask team) | DTS register mapping |
| **PythonSV support (DMRHUB)** | Vasudha Kale (`vasudha.kale@intel.com`) | PythonSV namespace, register access issues |
| **PythonSV support (NWP/DMR-RS)** | Angel Acosta Dominguez, Kavya Laalasa Karanam | NWP PythonSV emulation; file HSD at `goto/pythonsvsupport` |
| **NWP PythonSV dev PDL** | `nwp_pythonsv_dev@intel.com` | Email after filing HSD — no meetings without HSD first |
| **MCP Integration** | Natalya V Kitaryeva | MCP model build / integration questions |
| **IMH Integration (EFFM/Build)** | Anders Berglund, Elisa Rodrigues | EFFM, Palladium, model build |
| **IMH Integration (General)** | Jasveen Kaur, Dhanashree Lonkar | General IMH integration / GK |
| **Queue slot access / netbatch** | CK (Tan, Chee Kwong) | Queue slot PDL approval; `iVE DMR Emulation SYSVAL Queue Slots` PDL |
| **Queue slot access / netbatch** | CK (Tan, Chee Kwong) | Queue slot PDL approval; PDL name: `iVE DMR Emulation SYSVAL Queue Slots` |
| **Cheetah support** | `pesg.ind.fast.ba.pss@intel.com` | CTH setup, environment issues |
| **EFFM / Palladium** | `effm_support_palladium@eclists.intel.com` | Palladium emulation jobs |
| **Palladium HPC fleet** | `hpc_emulation_fleet_support@intel.com` | Palladium hardware/slot issues |
| **NWP access / training** | Priya (ask team) | Newport wiki, SimCloud NWP group (`simcld_nwp`) |

### 11.2 Support PDLs

| PDL | Purpose |
|---|---|
| `dmr.emu.model.support@intel.com` | DMR emulation model issues (primary support) |
| `dmr.emu.snps.support@intel.com` | Synopsys (Zebu) emulation issues |
| `dmr.emu.cadence.support@intel.com` | Cadence (Palladium) emulation issues |

> For Palladium hardware errors, file an HSD first through the [Federation and Emulation Service Requests](https://circuit.intel.com/content/it/it-support/topic-pages/infrastructure-and-information-security/federation-and-emulation/federation-and-emulation-sr-s-and-incs.html) portal, then email `hpc_emulation_fleet_support@intel.com`.

### 11.3 Key Wiki and SharePoint Pages

**Wiki pages** (Intel SSO required):
- DMR MCP Emulation Model Release: `https://wiki.ith.intel.com/spaces/P17X/pages/3448160222/`
- DMR SoC Emulation Getting Started: `https://wiki.ith.intel.com/spaces/P17X/pages/2775367494/`
- DMR MCP Build and Run steps: `https://wiki.ith.intel.com/spaces/P17X/pages/3207339393/`
- DMR MCP HOME PAGE: `https://wiki.ith.intel.com/spaces/P17X/pages/3317630090/`
- DMR CBB env setup (XPG): `https://wiki.ith.intel.com/spaces/XPG/pages/3541991855/`
- DMR Project Permissions (groups): `https://wiki.ith.intel.com/display/P17X/DMR+Project+Permissions`
- DMR IMH Emulation Models Training (video): `https://videoportal.intel.com/media/0_nastb88g`
- **DMR Bootcamp Training (SharePoint)**: `https://intel.sharepoint.com/sites/PDGTraining/SitePages/Diamond-Rapids-Bootcamp.aspx`
- **Required Access, Queue Slots, Important Links**: `https://wiki.ith.intel.com/spaces/PPA/pages/4112372000/`
- **ION EDGE access guide**: `https://intelpedia.intel.com/ION_-_EDGE`
- **GitHub repo access lookup (1Source)**: `https://1source.intel.com/inventory/repositories?organization=intel-restricted`
- **AGS access portal**: `https://ags.intel.com/identityiq/home.jsf`
- **Unix account creation**: `https://autoops.intel.com/domains/Accounts/flows/create_unix_account`
- **PDL manager**: `https://pdlmanager.intel.com/SearchPDL`
- **DMR Bootcamp Training**: `https://intel.sharepoint.com/sites/PDGTraining/SitePages/Diamond-Rapids-Bootcamp.aspx`
- Required Access, Queue Slots, Important Links: `https://wiki.ith.intel.com/spaces/PPA/pages/4112372000/`
- ION EDGE access: `https://intelpedia.intel.com/ION_-_EDGE`
- GitHub repo access (1Source): `https://1source.intel.com/inventory/repositories?organization=intel-restricted`
- AGS access portal: `https://ags.intel.com/identityiq/home.jsf`
- Unix account creation: `https://autoops.intel.com/domains/Accounts/flows/create_unix_account`
- PDL manager: `https://pdlmanager.intel.com/SearchPDL`

**SharePoint**:
- DMR home: `goto/dmr.home`
- DMR SoC Spec: `goto/dmr.socspec`
- Emulation models + FW collaterals table: DMR SharePoint → `IMH_Emul/` → `_DMR_Emul_Model_FW_Collaterals_Table.xlsx`
- Transactors list: DMR SharePoint → `IMH_Emul/` → Xtors_Model_Team_Review tab
- Trackers list: DMR SharePoint → `IMH_Emul/` → Trackers sheet
- Priya's emulation training recordings: SharePoint — go through before first live run

---

## 12. Decision Tree: Which Environment?

```
TC execution needed?
├── Feature is ZBB'd on NWP (e.g., HGS/DCM)?
│   └── Run on DMR HSLE/HSLE (Runnable_On_N-1) — NOT NWP
├── Needs OS-level validation (CPUID, MSR, perf counters)?
│   ├── Full boot required? → HSLE (submit to fm_zse netbatch)
│   └── BIOS menu only? → VP without OS boot (simics --no-run)
├── Needs thermal injection (DTS)?
│   └── HSLE with simics DTS script + PythonSV thermal read
├── Register-only sweep (no OS)?
│   └── VP is sufficient; faster turnaround
└── Debugging / single-step?
    └── HSLE with interactive qslot (priority queue, VNC)
```

# TCD: CBB CCF PM GV Control Interface

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421168](https://hsdes.intel.com/appstore/article-one/#/22022421168) |
| **Title** | CBB CCF[01] PM GV Control Interface |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Feature** | CBB CCF Active States — CCF GV management via BIOS/PEGA/TPMI |
| **Validation Phase** | **Alpha** — Feature enabling / path clearing (interface sanity check) |
| **Child TCs** | [22022422850](https://hsdes.intel.com/appstore/article-one/#/22022422850) — BIOS Configuration<br>[22022422851](https://hsdes.intel.com/appstore/article-one/#/22022422851) — PEGA Injection<br>[22022422859](https://hsdes.intel.com/appstore/article-one/#/22022422859) — TPMI Request<br>[22022422863](https://hsdes.intel.com/appstore/article-one/#/22022422863) — VF Curves Fuses |
| **KB last updated** | 2026-07-18 |

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) §2 Design Details
> for full-stack cross-layer diagram, GV control interface paths, and Interface & Register Matrix.

**CBB CCF GV PM Interface Check** validates the three external interface paths that configure and control the CBB CCF ring frequency GV: (1) **BIOS Configuration** -- TPMI `UFS_CONTROL` written at boot (TPMI_INIT PH1.x) to set MAX/MIN ratio envelope and ELC thresholds; (2) **PEGA Injection** -- B2P mailbox synthetic P-state bypasses the BW-heuristic slow loop for direct ratio control; (3) **TPMI Runtime** -- OS/PythonSV writes `UFS_CONTROL` at runtime (ratio lock: MAX=MIN, or restore autonomous). All three paths converge on the CBB PCode GVFSM, which applies the inputs per slow loop (~1 ms), executes V-first/PLL-first GV transitions, and reports the settled ratio via `UFS_STATUS.CURRENT_RATIO` and `HPM 0x1b`.

### CCF GV Interface Architecture -- All Three Paths

```
+----------------------+   +------------------------+   +-----------------------+
| IF-1: BIOS Config    |   | IF-2: PEGA Injection   |   | IF-3: TPMI Runtime    |
| (boot time, CPL3)    |   | (any time, Ring 0)     |   | (any time, OS/PySV)   |
|                      |   |                        |   |                       |
| TpmiSetUfsControl()  |   | pega_mailbox           |   | sv.sktN.cbbM          |
|   MAX_RATIO = P0     |   | .pega_pstate(          |   | .base.tpmi.ufs_control|
|   MIN_RATIO = Pm     |   |   meshgv = N,          |   |   .max_ratio = N      |
|   ELC thresholds     |   |   iagv=0,rearm=0)      |   |   .min_ratio = N      |
|   THROTTLE_MODE = 0  |   |                        |   | MAX=MIN -> ratio lock |
+--------+-------------+   +----------+-------------+   +----------+------------+
         |                            |                            |
         | TPMI write                 | B2P Mailbox                | TPMI write
         | (TPMI_INIT PH1.x)          | (HWP must = 1)             | (~1 ms latency)
         v                            v                            v
+----------------------------------------------------------------------------+
|               TPMI UFS_CONTROL  (per CBB, per socket)                     |
|  MAX_RATIO [14:8]  MIN_RATIO [21:15]  THROTTLE_MODE [1:0]  ELC fields    |
+-------------------------------------+--------------------------------------+
                                      |
                     PCode reads per slow-loop (~1 ms)
                                      |
                                      v
+----------------------------------------------------------------------------+
|                    CBB PCode GVFSM  (one per CBB die)                     |
|                                                                            |
|  1. Read [MIN_RATIO, MAX_RATIO] from UFS_CONTROL                          |
|  2. Read BW telemetry (CBO/SBO counters) -- drives autonomous freq target |
|  3. Read PEGA B2P request (IF-2) -- overrides BW heuristic when present  |
|  4. Clamp target ratio to [MIN, MAX] -- silent boundary enforcement       |
|  5. Execute GV transition:                                                 |
|       Freq UP   -> V-first  : FIVR voltage UP  --> PLL steps up          |
|       Freq DOWN -> PLL-first: PLL steps down   --> FIVR voltage DOWN     |
+-------------------------------------+--------------------------------------+
                                      |
          +--------------------------++-------------------------+
          |                          |                         |
          v                          v                         v
 UFS_STATUS.CURRENT_RATIO    HPM 0x1b DESIRED_RATIO    PLR_DIE_LEVEL
 (live CCF ring freq)        (-> IMH NIO Primecode)    (= 0x0 expected)
 sv.cbbM.tpmi.ufs_status     UPSTREAM_CCF_DESIRED       sv.cbbM.tpmi
                             _RATIO field               .plr_die_level
```

### PEGA meshgv Encoding for CCF Ring

| meshgv value | CCF Ring Target |
|--------------|----------------|
| 0 | P0 (max freq, 2.2 GHz on NWP = ratio 0x16) |
| 32 | Cap ratio (e.g. 0x20 = 3.2 GHz) |
| rand | Random ratio -- stress GVFSM transitions |
| N (integer) | Ratio floor -- GVFSM selects >= N |

### NWP Architecture Context

NWP has 2 CBBs (cbb0, cbb1), each with an independent GVFSM. PEGA injection to a socket reaches all CBBs in that socket simultaneously. Per-CBB injection is possible by specifying dieName.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422850 — CBB CCF GV BIOS Configuration](https://hsdes.intel.com/appstore/article-one/#/22022422850) | TPMI UFS_CONTROL field accessibility, BIOS override, PCode enforcement of limits | ccf_tpmi_gv_sweep_test() |
| [22022422851 — CBB CCF GV PEGA Injection](https://hsdes.intel.com/appstore/article-one/#/22022422851) | PEGA B2P mailbox, GVFSM ratio change, PLR clean, autonomous recovery | ccf_pegaPstate_test() in ccf_utils.py |
| [22022422859 — CBB CCF GV TPMI Request](https://hsdes.intel.com/appstore/article-one/#/22022422859) | TPMI ratio lock (MAX=MIN), GVFSM pin behavior, boundary clamping, autonomous restore | ccf_tpmi_gv_sweep_test() |
| [22022422863 — CBB CCF VF Curves Fuses](https://hsdes.intel.com/appstore/article-one/#/22022422863) | VF curve fuse readback, voltage/frequency pair validation, CCF VF table accessibility | cbb_ccf_vf_curve_test() |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| B2P Mailbox | pega_mailbox.pega_pstate(meshgv=N) | Inject synthetic P-state into CBB PCode |
| TPMI UFS_STATUS | sv.socketN.cbbM.base.tpmi.ufs_status.current_ratio | Observed CCF ratio after GVFSM convergence |
| TPMI PLR_DIE_LEVEL | sv.socketN.cbbM.base.tpmi.plr_die_level | Perf Limit Reason (must = 0x0 for clean PEGA run) |
| HPM 0x1b | UPSTREAM_CCF_DESIRED_RATIO | CCF desired ratio forwarded to IMH Primecode |
| TPMI UFS_CONTROL | sv.socketN.cbbM.base.tpmi.ufs_control | BIOS-set MAX_RATIO / MIN_RATIO (PEGA result still clamped to these limits) |

**Interface Access Matrix:**

| Interface | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | Mailbox (B2P) |
|-----------|-----|---------|----------|-----|-------|--------------|
| PEGA injection | -- | -- | -- | -- | -- | Yes |
| UFS_STATUS readback | -- | Yes (R/O) | -- | -- | -- | -- |
| PLR readback | -- | Yes (R/O) | -- | -- | -- | -- |

---

## Section 3: Reset, Power, and Clocking

- CCF GV state resets on warm reset; BIOS re-programs UFS_CONTROL limits during TPMI_INIT
- RING PLL and FIVR initialize to boot ratio; PCode GVFSM takes control after PH6
- UFS_STATUS.CURRENT_RATIO reflects live PLL state; stable ~1 ms after PEGA injection
- **V-first** (frequency increase): FIVR voltage raised first, then PLL stepped up -- prevents voltage droop
- **PLL-first** (frequency decrease): PLL stepped down first, then FIVR voltage lowered
- On emulation (HSLE/ZSim): wait >= 5M cycles after injection before reading back UFS_STATUS

---

## Section 4: Programming Model

```python
import diamondrapids.pm.pmutils.pega as pega
from diamondrapids.pm.pss.mailbox import pega_mailbox

# Step 1: Release PEGA (ensure autonomous mode is not overriding)
pega.release(1)

# Step 2: Inject target ratio for CCF ring (meshgv = ring ratio)
pega_mailbox.pega_pstate(iagv=0, meshgv=0, iogv=0, memgv=0, rearmTimems=0)
# meshgv=0 -> P0 max freq (2.2 GHz on NWP)

# Step 3: Wait for GVFSM convergence
# Silicon: time.sleep(0.01) | Emulation: wait 5M cycles

# Step 4: Verify per CBB
import namednodes
for cbb_idx in range(2):
    path = 'cbb' + str(cbb_idx) + '.base.tpmi'
    cur_ratio = namednodes.sv.socket0.getbypath(path + '.ufs_status.current_ratio').read()
    plr = namednodes.sv.socket0.getbypath(path + '.plr_die_level').read()
    assert plr == 0
```

**Prerequisite BIOS knob:** ProcessorHWPMEnable = Enabled

---

## Section 5: Operational Behavior

The CBB CCF GVFSM processes PEGA injections as follows:

1. B2P mailbox delivers meshgv ratio to CBB PCode interrupt handler
2. GVFSM evaluates ratio against [MIN_RATIO, MAX_RATIO] from UFS_CONTROL -- silently clamped if out of range
3. GVFSM executes GV transition (V-first up / PLL-first down)
4. UFS_STATUS.CURRENT_RATIO updated to new settled ratio
5. GVFSM forwards updated ratio to Primecode via HPM 0x1b

After injection, GVFSM returns to autonomous BW-heuristic mode on the next slow loop unless rearmTimems > 0.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| meshgv above P0 fuse cap | Silently clamped to UFS_HEADER.MAX_RATIO_CAP |
| meshgv below Pm fuse floor | Silently clamped to UFS_HEADER.MIN_RATIO_CAP |
| HWP disabled (BIOS knob off) | B2P mailbox rejected; GVFSM ignores injection |
| PLR != 0 after injection | Active power/thermal limit overriding PEGA; check RAPL/Prochot state |
| GVFSM busy (transition in progress) | Subsequent PEGA held until current transition completes |

---

## Section 7: Security / Safety / Policy

- PEGA mailbox access requires Ring 0 privilege (OS kernel or PMX framework)
- PEGA is a validation-only interface; not available in production firmware

---

## Section 8: References

| Reference | Link |
|-----------|------|
| NWP HAS CCF UFS / TPMI | codesign-ask-specs-and-wikis (NWP project) |
| CCF GV merged KB | KB/pm_tcd_kb/22022420512_cbb_ccf_feature_enabling/TCD_merged_ccf_pm_interface_check.md |
| PMX test script | diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py (--test_ccf_pega_pstate) |
| ccf_utils.py function | diamondrapids/pm/pmutils/ccf_utils.py (ccf_pegaPstate_test) |
| TC 22022422851 | https://hsdes.intel.com/appstore/article-one/#/22022422851 |

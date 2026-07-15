# TCD: CBB CCF Ring Freq Telemetry Counters

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421207](https://hsdes.intel.com/appstore/article-one/#/22022421207) |
| **Title** | CBB CCF Ring Scalability Telemetry Counters |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [22022420512 -- CBB CCF Ring Scalability Feature Enabling](https://hsdes.intel.com/appstore/article-one/#/22022420512) |
| **Feature** | CBB CCF Active States -- Ring scalability telemetry counter control |
| **Validation Phase** | **Alpha** — Feature enabling / path clearing (counter infrastructure sanity) |
| **KB last updated** | 2026-07-13 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF Ring Scalability Telemetry Counters** validates the **counter observability and control behavior** of the telemetry counters used by the CBB ring-frequency / ring-scalability logic.

The scope covers **three telemetry counter groups**:

1. **CBO ingress lookup counters** — CBO-side bandwidth / lookup activity used as inputs to the ring-frequency heuristic.
2. **SBO egress snoop counters** — SBO-side snoop traffic used as inputs to the ring-scalability / distress path.
3. **PMON CLR counters** — General-purpose performance monitoring counters (CLR = Counter Logic Reset) that measure ring-scalability events (e.g., `RING_SCALE_EVENTS`), plus the **Fast Ring C3 residency** counter.

This TCD does **not** validate the full ring-frequency policy or workpoint decision itself. Its purpose is to verify that the telemetry counters are:
- accessible and programmable
- individually enable/disable or freeze/unfreeze controllable
- frozen/stable when disabled
- bulk controllable through `ingress_all` where supported
- behaving consistently across CBB instances

For NWP: **one CBB die per CBB instance (CBB0/CBB1), two CBBs per socket**.

---

### Comprehensive Counter Architecture

```
NWP Socket
  ├── CBB0 (cbb0)         ├── CBB1 (cbb1)
  │
  │   +===========================================================+
  │   |         CBB DIE — CCF Telemetry Counter Map               |
  │   |                                                           |
  │   |   ┌─────────────────────────────────────────────────┐    |
  │   |   │  A.  CBO INGRESS LOOKUP COUNTERS                │    |
  │   |   │      (BW heuristic input → ring freq target)    │    |
  │   |   │                                                 │    |
  │   |   │  CBO[0..N]                                      │    |
  │   |   │    i_ccf_envs[k]                                │    |
  │   |   │      ingresss[j]                                │    |
  │   |   │        .enable     R/W  ← disable bit           │    |
  │   |   │        .counter    R    ← frozen when enable=0  │    |
  │   |   │        .ingress_all W   ← BULK: all ingresss[]  │    |
  │   |   │                                                 │    |
  │   |   │  Path: base.i_ccf_envs[k].ingresss[j].counter  │    |
  │   |   │        base.i_ccf_envs[k].ingresss.ingress_all  │    |
  │   |   │                                    ↓            │    |
  │   |   │              PCode BW heuristic                 │    |
  │   |   │              → CCF ring frequency target        │    |
  │   |   └─────────────────────────────────────────────────┘    |
  │   |                                                           |
  │   |   ┌─────────────────────────────────────────────────┐    |
  │   |   │  B.  SBO EGRESS SNOOP COUNTERS                  │    |
  │   |   │      (snoop grade → ia_distress → ring scalab.) │    |
  │   |   │                                                 │    |
  │   |   │  SBO[0..M]                                      │    |
  │   |   │    i_ccf_envs[k]                                │    |
  │   |   │      egresss[j]                                 │    |
  │   |   │        .enable     R/W  ← disable bit           │    |
  │   |   │        .counter    R    ← frozen when enable=0  │    |
  │   |   │        (no bulk egress_all)                     │    |
  │   |   │                                                 │    |
  │   |   │  Path: base.i_ccf_envs[k].egresss[j].counter   │    |
  │   |   │                                    ↓            │    |
  │   |   │              PCode snoop grade                  │    |
  │   |   │              → ia_distress → ring scalability   │    |
  │   |   └─────────────────────────────────────────────────┘    |
  │   |                                                           |
  │   |   ┌─────────────────────────────────────────────────┐    |
  │   |   │  C.  PMON CLR COUNTERS (Performance Monitor)    │    |
  │   |   │      (ring-scalability event counting)          │    |
  │   |   │                                                 │    |
  │   |   │  CCF PMU CLR (egress path)                      │    |
  │   |   │    i_ccf_envs[k]                                │    |
  │   |   │      egresss[j]                                 │    |
  │   |   │        pmoncountercontrol[N]                    │    |
  │   |   │          .ev_sel   ← event select (0x24 = RING  │    |
  │   |   │          .umask    ← unit mask (0x3f)            │    |
  │   |   │          .frz      ← freeze (stop counting)     │    |
  │   |   │          .rst_ctrl ← reset control register     │    |
  │   |   │          .rst_ctrs ← reset counter values       │    |
  │   |   │        pmoncounter[N].event_count ← counter R   │    |
  │   |   │                                                 │    |
  │   |   │  Path: base.i_ccf_envs[k].egresss[j]           │    |
  │   |   │          .pmoncountercontrol[N]                 │    |
  │   |   │          .pmoncounter[N].event_count            │    |
  │   |   │  Bulk: unitcontrol op w/r/c (write/reset/clear) │    |
  │   |   │                                                 │    |
  │   |   │  C2. FAST RING C3 RESIDENCY COUNTER             │    |
  │   |   │      (Fast C3 residency accounting)             │    |
  │   |   │                                                 │    |
  │   |   │  CCF PMA                                        │    |
  │   |   │    ccf_pmc_regs                                 │    |
  │   |   │      fast_c3_residency.counter  R               │    |
  │   |   │                          ↑                      │    |
  │   |   │        increments when Fast Ring C3 occurs      │    |
  │   |   │  Path: base.ccf_pma.ccf_pmc_regs                │    |
  │   |   │          .fast_c3_residency.counter             │    |
  │   |   └─────────────────────────────────────────────────┘    |
  │   +===========================================================+
  │
  └──→ Feeds PCode ring-frequency and ring-scalability decisions
```

---

### Counter Group Summary

| Group | Counter Path | Control Mechanism | Bulk Control | What it feeds |
|-------|-------------|-------------------|--------------|---------------|
| **A. CBO ingress** | `base.i_ccf_envs[k].ingresss[j]` | `.enable` bit (R/W) | `ingress_all` | Ring freq heuristic |
| **B. SBO egress** | `base.i_ccf_envs[k].egresss[j]` | `.enable` bit (R/W) | None (per-counter) | Snoop grade → distress |
| **C. PMON CLR** | `base.i_ccf_envs[k].egresss[j].pmoncounter[N]` | `pmoncountercontrol[N].frz` + reset ops | `unitcontrol` write | Ring-scale event counting |
| **C2. Fast C3** | `base.ccf_pma.ccf_pmc_regs.fast_c3_residency` | Read-only observation | — | Fast Ring C3 residency |

---

### Validation Intent

- **Individual disable behavior** (CBO/SBO) — A disabled counter must stop accumulating and hold a constant value over time.
- **Bulk disable / enable behavior** (CBO ingress only) — `ingress_all` must disable/enable the entire ingress group consistently.
- **PMON CLR freeze behavior** — Frozen CLR PMON counters must remain stable; `unitcontrol` freeze mechanism must work.
- **PMON CLR event counting** — CLR PMON counters must count ring-scalability events (`RING_SCALE_EVENTS`, `ev_sel=0x24`) under real CCF activity (PEGA injection).
- **Fast C3 residency accessibility** — `fast_c3_residency.counter` must be accessible and increment when Fast Ring C3 occurs.
- **Counter accessibility and programmability** — All counter CSRs must be readable/writable through the supported CSR path.

---

### Counter Disable / Freeze Test Flow

For CBO and SBO counters (enable/disable):
1. Read the initial counter value
2. Disable the counter (`enable = 0`)
3. Wait a defined interval (`rtime` million cycles)
4. Read again — **Pass:** `val_before == val_after`
5. Re-enable as cleanup

For PMON CLR counters (freeze):
1. Reset all CLR counters (`unitcontrol: frz=1, rst_ctrl=1, rst_ctrs=1`)
2. Program event select (`ev_sel=0x24, umask=0x3f`)
3. Unfreeze and inject CCF activity (PEGA P-state injection, ~15s)
4. Freeze again and read — **Pass:** at least one `pmoncounter[N].event_count > 0`
5. Verify freeze: re-freeze, wait, verify counters unchanged

### `ingress_all` Bulk Test (CBO only)
Repeat N=10 iterations: `ingress_all=0` → verify all frozen → `ingress_all=1` → verify accumulation resumes

---

### NWP Context
NWP has 2 CBBs (cbb0, cbb1) per socket. All counter tests iterate over CBBs via `cbbs` path and `i_ccf_envs` component group.

---

### TC Coverage Map

| TC | Scope | Script Function |
|----|-------|-----------------|
| [22022422886 -- CBB CCF PMON](https://hsdes.intel.com/appstore/article-one/#/22022422886) | CLR PMON counter program/freeze/event-count + Fast C3 residency counter | `ccf_pmon_clr_disable_test`, `ccf_pmon_clr_unitcontrol_op`, `ccf_pmon_clr_countercontrol_op` |
| [22022422889 -- CBB CCF CBO Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422889) | CBO lookup counter disable/freeze + `ingress_all` bulk disable/enable | `ccf_cbo_telemetry_lookup_cntr_disable_test`, `ccf_cbo_telemetry_lookup_cntr_enable_disable_all_test` |
| [22022422900 -- CBB CCF SBO Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422900) | SBO snoop counter disable/freeze behavior | `ccf_sbo_telemetry_snoop_cntr_disable_test` |

1. **CBO ingress lookup counters** — CBO-side bandwidth / lookup activity used as inputs to the ring-frequency heuristic.
2. **SBO egress snoop counters** — SBO-side snoop traffic used as inputs to the ring-scalability / distress path.

This TCD does **not** validate the full ring-frequency policy or workpoint decision itself. Its purpose is to verify that the telemetry counters are:
- accessible
- individually enable/disable controllable
- frozen when disabled
- bulk controllable through `ingress_all` where supported
- behaving consistently across CBB instances

For NWP: **one CBB die per CBB instance (CBB0/CBB1), two CBBs per socket**.

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| CBO ingress counter | `sv.socketN.cbbM.base.i_ccf_envs[k].ingresss[j]` | Individual CBO telemetry counter control and observation |
| CBO `ingress_all` | `sv.socketN.cbbM.base.i_ccf_envs[k].ingresss.ingress_all` | Bulk enable/disable for all ingress counters |
| SBO egress counter | `sv.socketN.cbbM.base.i_ccf_envs[k].egresss[j]` | Individual SBO snoop counter control and observation |
| PMON CLR unit control | `sv.socketN.cbbM.base.i_ccf_envs[k].egresss[j].pmoncountercontrol[N]` | CLR PMON event select, freeze, reset |
| PMON CLR counter | `sv.socketN.cbbM.base.i_ccf_envs[k].egresss[j].pmoncounter[N].event_count` | CLR PMON event count readback |
| Fast C3 residency | `sv.socketN.cbbM.base.ccf_pma.ccf_pmc_regs.fast_c3_residency.counter` | Fast Ring C3 residency counter |

**Interface Access Matrix:**

| Interface | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | Mailbox |
|-----------|-----|---------|----------|-----|-------|---------|
| CBO ingress counter | -- | -- | -- | Yes (R/W) | -- | -- |
| CBO `ingress_all` | -- | -- | -- | Yes (W) | -- | -- |
| SBO egress counter | -- | -- | -- | Yes (R/W) | -- | -- |
| PMON CLR control | -- | -- | -- | Yes (R/W) | -- | -- |
| PMON CLR counter | -- | -- | -- | Yes (R) | -- | -- |
| Fast C3 residency | -- | -- | -- | Yes (R) | -- | -- |

---

## Section 3: Reset, Power, and Clocking

- Counter registers reset on warm reset; default post-reset state is **enabled**.
- Counters accumulate only when the corresponding CBB logic is active.
- On emulation: wait intervals expressed using `rtime` in million cycles (typically 100M ≈ 1 ms at 100 MHz).

---

## Section 4: Programming Model

```python
# CBO telemetry counter disable test
ccfu.ccf_cbo_telemetry_lookup_cntr_disable_test(
    skt_num, 'cbbs', 'i_ccf_envs', 'ingresss',
    rtime=100,   # million cycles
    Log=log, verbose=None
)

# CBO bulk enable/disable test
ccfu.ccf_cbo_telemetry_lookup_cntr_enable_disable_all_test(
    skt_num, 'cbbs', 'i_ccf_envs',
    iter_num=10,
    Log=log, verbose=None
)

# SBO telemetry counter disable test
ccfu.ccf_sbo_telemetry_snoop_cntr_disable_test(
    skt_num, 'cbbs', 'i_ccf_envs',
    rtime=100,
    Log=log, verbose=None
)

# PMON CLR counter disable (freeze) test
ccfu.ccf_pmon_clr_disable_test(
    skt_num, 'cbbs', 'i_ccf_envs', 'egresss', 'all',
    rtime=100,
    Log=log, verbose=None
)

# PMON CLR unit control (reset + freeze)
ccfu.ccf_pmon_clr_unitcontrol_op(
    skt_num, cbb, 'i_ccf_envs', 'egresss',
    op='w', w_dict={'frz': 1, 'rst_ctrl': 1, 'rst_ctrs': 1}
)

# PMON CLR counter control (event select)
ccfu.ccf_pmon_clr_countercontrol_op(
    skt_num, cbb, 'i_ccf_envs', 'egresss',
    op='w', w_dict={'ev_sel': 0x24, 'umask': 0x3f}  # RING_SCALE_EVENTS
)
```

Script: `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py`
Options: `--test_ccf_cbo_telemetry`, `--test_ccf_sbo_telemetry`, `--test_ccf_pmon`

---

## Section 5: Operational Behavior

For CBO and SBO telemetry counters (enable/disable):
1. Read the current value
2. Disable the counter
3. Wait for the configured interval
4. Read the value again — verify frozen (unchanged)
5. Re-enable the counter

For CBO bulk-control (`ingress_all`):
1. Disable entire ingress group → verify all counters frozen
2. Re-enable group → verify normal counting resumes under activity

For PMON CLR counters:
1. Reset all CLR counters via `unitcontrol` (`frz=1, rst_ctrl=1, rst_ctrs=1`)
2. Program event select via `countercontrol` (`ev_sel=0x24, umask=0x3f`)
3. Unfreeze and inject CCF activity (PEGA P-state) for ~15s
4. Freeze and read — verify at least one `pmoncounter[N].event_count > 0`
5. Verify PMON freeze: frozen counters must not change over `rtime` million cycles

For Fast C3 residency:
1. Read baseline `fast_c3_residency.counter`
2. Inject Fast Ring C3 condition
3. Verify counter incremented

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Counter already disabled at test start | Re-applying disable is allowed; frozen-value check still applies |
| Counter wraps while enabled | Not a failure; only disabled-state freeze behavior is validated |
| `ingress_all` partial effect | Failure — all counters in the group must respond consistently |
| SBO counter under low traffic | Use sufficient wait time so normal traffic would have caused increment if not disabled |
| PMON CLR counter stays 0 after activity | Failure — event select may be wrong or CCF activity insufficient; verify `ev_sel=0x24` |
| Fast C3 residency counter not accessible | Failure — register may not exist if Fast Ring C3 is not supported in this configuration |
| PMON freeze not effective | Failure — `frz` bit not stopping count accumulation; hardware bug |

---

## Section 7: Security / Safety / Policy

- Counter access requires privileged CSR access through the validation framework.
- Counter disable is temporary and must be restored at test completion.
- The test must not leave telemetry counters disabled after exit.

---

## Section 8: References

| Type | Reference | Scope |
|------|-----------|-------|
| HAS | [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) | CCF ring telemetry: CBO BW counters, SBO snoop counters, PMON events |
| HAS | [CBB Telemetry Aggregator HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details) | PUNIT telemetry space — RING_SCALE_EVENTS (ev_sel=0x24), CBO/SBO counter programming |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB CCF ring power management, telemetry counter control |
| HAS | [DMR CCB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) | CBB PM feature index |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP-specific PM delta; counter path applicability |
| KB | KB/pm_features/fabric_dvfs/fabric_dvfs_main.md | CBO BW heuristic inputs → ring GV; `ingresss` counter path to PCode |
| Related TCD | [22022421197 — CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022421197) | Algorithm that consumes these counter values |
| PMX script | `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py` | `ccf_cbo_telemetry_lookup_cntr_disable_test`, `ccf_sbo_telemetry_snoop_cntr_disable_test`, `ccf_pmon_clr_disable_test` |
| TC | [22022422886 — CBB CCF PMON](https://hsdes.intel.com/appstore/article-one/#/22022422886) | PMON CLR counter disable test |
| TC | [22022422889 — CBB CCF CBO Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422889) | CBO lookup counter disable + ingress_all bulk test |
| TC | [22022422900 — CBB CCF SBO Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422900) | SBO snoop counter disable test |

# Deep Analysis: Enable PEGA C-States

| Field | Value |
|-------|-------|
| **HSD ID** | 14021642592 |
| **Title** | Enable PEGA C-States |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | PEGA C-state injection tool — inject all C-state flavors (C6A, C6S, C6S-P, C1) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test uses **PEGA** (a Pcode-level C-state injection/exercise tool) to inject all C-state flavors:
- C6S-P (C6S-Predictive), C6S, C6A, C1

All core-level C-states are functional on NWP. PEGA is used to directly exercise C-state entry without waiting for OS idle. Tags: `DMR_PO`, `NGA_MAIN`, `plc.feature.p1`.

Command: `runPmx.py -x dmr.xml -p pega -H 1 -M 5` → adapt `dmr.xml` → `nwp.xml`.

---

## Section B: NWP-Specific Test Procedure

### PEGA C-State Injection (NWP)

```python
# NWP PEGA invocation
import pm.pmutils.pega as pega
args = 'pega.py --cstate c6s'.split()  # or c6a, c6sp, c1
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot SVOS with C-states enabled | Fuse/BIOS: C6 enabled |
| 2 | Run PEGA via PMx | `python runPmx.py -x nwp.xml -p pega -H 1 -M 5` |
| 3 | Inject C6A via PEGA | `pega.py --cstate c6a` |
| 4 | Inject C6S via PEGA | `pega.py --cstate c6s` |
| 5 | Inject C6S-P via PEGA | `pega.py --cstate c6sp` |
| 6 | Inject C1 via PEGA | `pega.py --cstate c1` |
| 7 | Verify each injection produces correct entry | Per state: FSM, PICLET, SRL, BGF_RUN, PLL_LOCK |

### NWP Notes
- `dmr.xml` → `nwp.xml`
- NWP has no SMT — inject on per-core basis
- PEGA tool needs to be ported/verified for NWP python package hierarchy
- `NGA_MAIN`: runs under NGA automation after manual checkout

### C-State PEGA Pass/Fail (NWP)

| C-State | Entry Check | Exit Check |
|---------|-------------|------------|
| C6A | core_cstate=C6, PICLET_ENABLED, SRL_ACTIVE, BGF_RUN=0, PLL=0 | core_cstate=C0, PICLET_PMA_IDLE, SRL_IDLE, BGF_RUN=1, PLL=1 |
| C6S | Same as C6A + L2/MLC flush | Same |
| C6S-P | Same as C6S + FIVR off | Same + FIVR on |
| C1 | core_cstate=C1, freq reduction | core_cstate=C0 |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify PEGA tool ported for NWP package; inject all 4 C-state flavors**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; PEGA injection is the precise tool for C-state entry verification without OS idle dependency

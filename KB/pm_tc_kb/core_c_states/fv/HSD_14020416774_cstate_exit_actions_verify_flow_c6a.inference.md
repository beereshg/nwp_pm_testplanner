# Deep Analysis: CState Exit Actions: Verify Flow C6A

| Field | Value |
|-------|-------|
| **HSD ID** | 14020416774 |
| **Title** | CState Exit Actions: verify flow C6A |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6A exit flow — core returns from C6 to C0 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **C6A exit flow** — after an interrupt or work arrives, the core transitions from C6A back to C0. All expected signals should return to active/running state. Functional on NWP.

Tags: `DMR_PO`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### C6A Exit Pass/Fail Criteria

| Signal | Expected After C6A Exit |
|--------|--------------------------|
| `core_cstate` | C0 |
| PICLET FSM | `PICLET_PMA_IDLE` |
| SRL | `SRL_IDLE` |
| `BGF_RUN` | 1 (active) |
| `CORE_PWR_GOOD` | 1 (power restored) |
| `PLL_LOCK` | 1 (PLL locked) |
| Execution | Resumed from MWAIT instruction |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Place core in C6A (per entry TC 14020647414) | Core in C6A state |
| 2 | Send interrupt to core | IPI or external interrupt |
| 3 | Verify core exits C6A → C0 | All exit signals match above |
| 4 | Verify PLL restored and locked | `PLL_LOCK = 1` before instruction execution |
| 5 | Verify core resumes execution | Instruction pointer advances past MWAIT |
| 6 | Run PMx to automate | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |

### C6A Exit Automated Test
```python
# NWP C6A exit verification (automated via cstates PMx)
# runPmx.py calls ccx_residency_test.py which manages entry/exit
# Pass: core_cstate == C0 after interrupt; all status registers match exit criteria
```

### Pass Criteria
- All exit signals match expected C0 state (table above)
- No hang on C6A exit (core never returns to execution)
- PLL locked before first instruction execution
- Exit latency within spec (BGF_RUN=1 within timeout)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; C6A exit functional on NWP; pair with entry TC 14020647414**

**Priority**: High — `plc.feature.p1`; C6A exit is critical path for interrupt response latency — hangs on C6 exit are a common bringup failure mode

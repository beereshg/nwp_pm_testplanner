# Deep Analysis: Socket RAPL x PMAX

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422010 |
| **Title** | Socket rapl x Pmax |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL cross-product with PMAX (Platform Maximum Power) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Socket RAPL interaction with PMAX** (Platform Maximum Power enforcement). When both RAPL PL1/PL2 and PMAX are active simultaneously, the more restrictive limit should dominate.

Test steps note "PMX command line: ** To do: Will add here based on Pmax test content" — the RAPL PMx base command applies. Tags: `plc.feature.p2`, `pm.xproducts.pm`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted PMx Command
```
python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3
```
(Extend with PMAX plugin when available: `-p pmax`)

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set RAPL PL1 to TDP (RAPL not limiting) | RAPL permissive |
| 2 | Enable PMAX and set below TDP | PMAX becomes the binding limit |
| 3 | Run workload | Verify PMAX limits observed (not RAPL) |
| 4 | Set RAPL PL1 below PMAX | RAPL becomes the binding limit |
| 5 | Run workload | Verify RAPL limits observed (not PMAX) |
| 6 | Both active simultaneously | Min(RAPL, PMAX) wins; verify correct arbitration |

### NWP PMAX Register
| Register | NWP Path |
|----------|----------|
| PMAX control | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` (PMAX registers) |
| Perf limit reasons | `sv.socket0.cbb[0-1].base.tpmi.plr_mailbox_interface` |

### Pass Criteria
- When PMAX < RAPL: PMAX is the binding limit; power at PMAX
- When RAPL < PMAX: RAPL is the binding limit; power at RAPL
- Arbitration: min(PMAX, RAPL) correctly enforced
- Perf limit reasons show correct limiting agent

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; test PMAX × RAPL arbitration (min limit wins)**

`python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`

**Priority**: Medium — `plc.feature.p2`; RAPL × PMAX arbitration is critical for correct platform power budget management

# Deep Analysis: RAPL Perf Limit Reasons - Fine & Coarse

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422036 |
| **Title** | RAPL Perf limit reasons - Fine & Coarse |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PLR (Perf Limit Reasons) — RAPL bits in fine and coarse PLR registers |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL Perf Limit Reasons (PLR)** — both fine-grained and coarse-grained bits when RAPL is throttling. Reference: DMR PLR HAS.

PLR Registers (from test steps):
- `@sv.socket0.cbb0.base.tpmi.plr_mailbox_interface`
- `@sv.socket0.cbb0.base.tpmi.plr_mailbox_data`

On NWP: 2 CBBs. Verify PLR RAPL bits on both `cbb0` and `cbb1`. Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### PLR RAPL Bits (NWP)

| PLR Bit | Trigger | Level |
|---------|---------|-------|
| RAPL_PL1 | Power > PL1 → RAPL throttling | Coarse |
| RAPL_PL2 | Power > PL2 burst limit | Coarse |
| FAST_RAPL | Fast RAPL algorithm active | Fine |
| RAPL_TAU | Tau window expiry limiting | Fine |

### PLR Access (NWP Mailbox)

```python
# NWP PLR RAPL bits via mailbox (both CBBs)
for cbb_idx in range(2):
    plr_iface = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.plr_mailbox_interface")
    plr_data  = sv.socket0.getbypath(f"cbb{cbb_idx}.base.tpmi.plr_mailbox_data")
    
    # Write mailbox interface to request PLR RAPL bits
    plr_iface.write(<rapl_plr_mailbox_command>)
    plr_bits = plr_data.read()
    print(f"CBB{cbb_idx} PLR RAPL bits: 0x{plr_bits:08x}")
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Trigger PL1 throttle (workload > PL1) | Set low PL1 limit |
| 3 | Read PLR RAPL bits on cbb0 and cbb1 | Via PLR mailbox; RAPL_PL1 bit set |
| 4 | Trigger PL2 throttle | Burst power > PL2 limit |
| 5 | Read PLR RAPL bits | RAPL_PL2 bit set on both CBBs |
| 6 | Trigger Fast RAPL | Large power transient |
| 7 | Read PLR fine bits | FAST_RAPL bit set |
| 8 | Verify bits clear when RAPL not throttling | PLR bits = 0 at idle |

### Pass Criteria
- PLR RAPL_PL1 bit set on both cbb0 and cbb1 when PL1 throttling
- PLR RAPL_PL2 bit set during PL2 excursion
- PLR FAST_RAPL bit set during Fast RAPL
- All RAPL PLR bits clear at idle (no throttle)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; PLR RAPL bits via mailbox on both cbb0 and cbb1**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Trigger each RAPL mode; read PLR mailbox on both `cbb0` and `cbb1`
3. Reference: DMR PLR HAS §RAPL PLR bits

**Priority**: High — `plc.feature.p2`; PLR RAPL bits are the primary diagnostic indicator for RAPL-caused throttle — critical for performance analysis

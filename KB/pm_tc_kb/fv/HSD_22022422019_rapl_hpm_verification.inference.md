# Deep Analysis: RAPL HPM Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422019 |
| **Title** | RAPL HPM verification |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **TCD** | [22022420817 — Socket RAPL HPM Verification](https://hsdes.intel.com/appstore/article-one/#/22022420817) |
| **TPF** | [15019477653 — NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | HPM messaging path — RAPL_PERF_LIMIT (0x14) and LEAF_PERF_STATUS (0x16) |
| **Status** | open (ready_for_content_review) |
| **Val Environment** | emulation.hsle, silicon, virtual_platform |
| **Owner Team** | soc.pm |
| **Automation** | yes |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Test Case Intent

Validates the HPM messaging path for Socket RAPL enforcement on NWP as defined in [TCD 22022420817 — Socket RAPL HPM Verification](https://hsdes.intel.com/appstore/article-one/#/22022420817) §TC Coverage Map. Verifies that HPM 0x14 (RAPL_PERF_LIMIT) is correctly transmitted from NIO PrimeCode to both CBB0 and CBB1, that each CBB PCode enforces the delivered frequency ceiling, and that HPM 0x16 (LEAF_PERF_STATUS) feedback is returned to the NIO root. Covers PL1, PL2, and Fast RAPL source identification bits within the HPM message.

---

## Section A: NWP Disposition

**Disposition: Runnable_On_N-1**

This test verifies **RAPL HPM message transport and bit correctness** from NIO PrimeCode to CBB PCode for each RAPL use case (PL1, PL2, Fast RAPL). On NWP the topology simplifies vs DMR:

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| IMH dies | 2 (IMH-P root + IMH-S leaf) | **1 NIO** (root only) | No inter-IMH HPM relay; NIO sends directly to CBBs |
| CBB count | 4 | **2** | HPM 0x14 to `cbb{0,1}` only; HPM 0x16 from 2 CBBs |
| HPM intermediary | IMH-S forwards to CBBs | **None** | Simpler path; no leaf-relay verification needed |
| RACL | IMH-S runs local RACL PID | **N/A on NWP** | Single NIO manages all RAPL PIDs directly |
| Register prefix | `sv.socket0.imh0/imh1.*` | **`sv.socket0.nio.*`** | Path swap in scripts |

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

**Adaptation**: Change XML config `dmr.xml` → `nwp.xml`; adjust CBB loop `range(4)` → `range(2)`; remove any IMH-S leaf verification steps (NWP has no leaf IMH). Register path prefix: `nio.punit` replaces `imh0.punit`.

---

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Programs CSR PKG_RAPL_LIMIT (PL1, PL2, Tau) + locks | [CSR] |
| 2 | BIOS | Programs TPMI PL1_CONTROL / PL2_CONTROL defaults | [TPMI MMIO] |
| 3 | OS/Test | Writes TPMI PL1 below current power → triggers PL1 throttle | [TPMI MMIO] |
| 4 | PrimeCode (NIO) | RAPL NN-PID computes min freq ceiling (RAPL_PID_FREQ_OUTPUT) | [Internal] |
| 5 | PrimeCode (NIO) | Sends HPM 0x14 RAPL_PERF_LIMIT to CBB0 and CBB1 | [HPM] |
| 6 | PCode (CBB0) | Receives HPM 0x14; enforces freq ceiling on cores | [HPM] |
| 7 | PCode (CBB1) | Receives HPM 0x14; enforces freq ceiling on cores | [HPM] |
| 8 | PCode (CBB0) | Returns HPM 0x16 LEAF_PERF_STATUS to NIO | [HPM] |
| 9 | PCode (CBB1) | Returns HPM 0x16 LEAF_PERF_STATUS to NIO | [HPM] |
| 10 | PrimeCode (NIO) | Receives LEAF_PERF_STATUS; adjusts PID feedback loop | [Internal] |
| 11 | OS/Test | Reads TPMI PERF_STATUS throttle counter; verifies non-zero | [TPMI MMIO] |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | BIOS | NIO PrimeCode | CSR PKG_RAPL_LIMIT programming | [CSR] |
| 2 | OS/Test | NIO PrimeCode | TPMI PL1_CONTROL write (PL1 < current power) | [TPMI MMIO] |
| 3 | NIO PrimeCode | CBB0 PCode | HPM 0x14 RAPL_PERF_LIMIT (RAPL_PID_FREQ_OUTPUT, source bits) | [HPM] |
| 4 | NIO PrimeCode | CBB1 PCode | HPM 0x14 RAPL_PERF_LIMIT (same payload) | [HPM] |
| 5 | CBB0 PCode | CBB0 Cores | freq ceiling enforcement via WP1/fast_throttle | [HW wire] |
| 6 | CBB1 PCode | CBB1 Cores | freq ceiling enforcement via WP1/fast_throttle | [HW wire] |
| 7 | CBB0 PCode | NIO PrimeCode | HPM 0x16 LEAF_PERF_STATUS | [HPM] |
| 8 | CBB1 PCode | NIO PrimeCode | HPM 0x16 LEAF_PERF_STATUS | [HPM] |
| 9 | OS/Test | TPMI | Read PERF_STATUS throttle counter | [TPMI MMIO] |

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon (preferred), HSLE emulation, or VP (Simics) |
| BIOS knobs | Socket RAPL PL1 = Enabled (default); PL2 = Enabled; RAPL Lock = Unlocked for test programmability |
| PythonSV | `sv.socket0.nio.punit.*` accessible; `sv.socket0.cbb{0,1}.punit.*` accessible |
| OS / Tool | SVOS with `runPmx.py` and `cpu_rapl` plugin; workload generator (PTU, stress-ng) |
| Feature state | Socket RAPL active; Fast RAPL supported |
| Starting state | System booted to OS; no prior RAPL lock-out; PL1 > current idle power initially |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Boot system; confirm RAPL enabled. Read TPMI PL1_CONTROL.PWR_LIM_EN (idx=2). | PWR_LIM_EN = 1 on NIO TPMI instance. | PWR_LIM_EN = 0; RAPL not enabled. |
| 2 | Start sustained workload on all 96 cores (PTU or stress-ng). Confirm power > idle. | Socket power rises; cores running at or near turbo. | No power increase; workload not executing. |
| 3 | Set TPMI PL1 below current power (`TPMI PL1_CONTROL.PWR_LIM` < measured power). | PL1 throttle triggers within 3–5× τ (1–5 s). | No throttle observed; power stays above PL1. |
| 4 | Read HPM 0x14 status on CBB0: verify `RAPL_PID_FREQ_OUTPUT` field (bits [63:56]) shows reduced freq ceiling. | RAPL_PID_FREQ_OUTPUT < max turbo ratio. | RAPL_PID_FREQ_OUTPUT = max ratio (no reduction). |
| 5 | Read HPM 0x14 status on CBB1: verify same `RAPL_PID_FREQ_OUTPUT` as CBB0. | CBB1 receives identical freq ceiling as CBB0. | CBB1 freq ceiling differs from CBB0 or = max ratio. |
| 6 | Verify PL1 source bit: check `PKG_PL1_INBAND` (bit 33) or `PKG_PL1_CSR` (bit 34) = 1 in HPM 0x14 payload. | Appropriate PL1 source bit asserted. | No PL1 source bit set despite PL1 throttle active. |
| 7 | Read HPM 0x16 LEAF_PERF_STATUS from CBB0: verify throttle status reflected. | LEAF_PERF_STATUS indicates RAPL-constrained. | Status shows unconstrained despite throttle. |
| 8 | Read HPM 0x16 LEAF_PERF_STATUS from CBB1: verify consistent with CBB0. | Both CBBs report throttle status back to NIO. | CBB1 status missing or inconsistent. |
| 9 | Verify core frequency on both CBBs capped at RAPL_PID_FREQ_OUTPUT level. Read per-core `cpuinfo_cur_freq` or PythonSV frequency registers. | Core freq ≤ RAPL_PID_FREQ_OUTPUT × 100 MHz on all 96 cores. | Any core exceeding the HPM-delivered ceiling. |
| 10 | Set PL2 limit; run burst workload → trigger PL2 throttle. Verify `PKG_PL2_INBAND` (bit 36) or `PKG_PL2_CSR` (bit 37) = 1 in HPM 0x14. | PL2 source bit asserted in HPM payload to both CBBs. | PL2 bit not set during PL2 throttle. |
| 11 | Trigger Fast RAPL (large power transient). Verify `FAST_RAPL` bit (bit 32) = 1 in HPM 0x14 to both CBBs. | FAST_RAPL bit asserted when fast loop engaged. | FAST_RAPL bit = 0 during fast power event. |
| 12 | Remove RAPL limit (set PL1 = max). Verify all source bits cleared (bits [32:44] = 0) in HPM 0x14. | All throttle source bits = 0; RAPL_PID_FREQ_OUTPUT returns to max ratio. | Any source bit stuck asserted after limit removal. |
| 13 | Read TPMI PERF_STATUS (idx=8): verify PWR_LIMIT_THROTTLE_CTR > 0 (accumulated during throttle). | Throttle counter reflects time spent throttled. | Counter = 0 despite observed throttle period. |

### HPM 0x14 Field Reference (RAPL_PERF_LIMIT)

| Bits | Field | Description |
|------|-------|-------------|
| 7:0 | HPM_MSG_OPCODE | 0x14 |
| 14:8 | Agent_Id | Source agent ID |
| 15 | Response_Required | Always 0 |
| 31:16 | FIVR_INPUT_VOLTAGE | Input voltage to FIVR (loadline-adjusted) |
| 32 | FAST_RAPL | Fast RAPL driving the limit |
| 33 | PKG_PL1_INBAND | Inband SW (TPMI) PL1 driving limit |
| 34 | PKG_PL1_CSR | CSR PL1 driving limit |
| 35 | PKG_PL1_OOB | OOB (BMC) PL1 driving limit |
| 36 | PKG_PL2_INBAND | Inband SW (TPMI) PL2 driving limit |
| 37 | PKG_PL2_CSR | CSR PL2 driving limit |
| 38 | PKG_PL2_OOB | OOB PL2 driving limit |
| 39:44 | PLATFORM_* | Platform RAPL source bits |
| 55:48 | RACL_PID_FREQ_OUTPUT | RACL PID resolved frequency |
| 63:56 | RAPL_PID_FREQ_OUTPUT | Min-resolved RAPL PID frequency ceiling (the actual limit) |

### HPM 0x16 Field Reference (LEAF_PERF_STATUS)

| Bits | Field | Description |
|------|-------|-------------|
| 7:0 | HPM_MSG_OPCODE | 0x16 |
| varies | PERF_STATUS | CBB throttle/perf feedback to NIO root |

### NWP HPM Debug Access

```python
# NWP HPM message verification — NIO → CBB0, CBB1
# Read RAPL HPM status on each CBB punit
sv.socket0.cbb0.punit.hpm_rapl_perf_limit.show()
sv.socket0.cbb1.punit.hpm_rapl_perf_limit.show()

# Read LEAF_PERF_STATUS feedback from CBBs
sv.socket0.nio.punit.hpm_leaf_perf_status.show()

# Read TPMI Socket RAPL PL1 control
sv.socket0.nio.tpmi.socket_rapl_pl1_control.read()

# Read TPMI PERF_STATUS throttle counter
sv.socket0.nio.tpmi.perf_status.read()
```

### Pass / Fail Criteria

- **PASS**: HPM 0x14 RAPL_PERF_LIMIT correctly delivered from NIO to both CBB0 and CBB1 with accurate `RAPL_PID_FREQ_OUTPUT` and source bits (`PKG_PL1_*`, `PKG_PL2_*`, `FAST_RAPL`) matching the active throttle scenario. HPM 0x16 LEAF_PERF_STATUS returned from both CBBs to NIO. Core frequencies on both CBBs capped at HPM-delivered ceiling. All bits cleared when RAPL limit removed. TPMI PERF_STATUS counter incremented during throttle.

- **FAIL**: Any of the following:
  - RAPL_PID_FREQ_OUTPUT not reduced during active throttle
  - Source bits (PL1/PL2/Fast RAPL) not matching the active RAPL scenario
  - HPM 0x14 not delivered to one or both CBBs (asymmetric enforcement)
  - HPM 0x16 feedback missing from either CBB
  - Core frequency exceeds HPM-delivered ceiling on any core
  - Source bits stuck asserted after limit removal
  - TPMI PERF_STATUS counter = 0 despite observed throttle

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| TPMI PL1_CONTROL (idx=2) | `sv.socket0.nio.tpmi.socket_rapl_pl1_control.read()` | PWR_LIM_EN = 1 |
| CBB0 HPM RAPL status | `sv.socket0.cbb0.punit.hpm_rapl_perf_limit.show()` | RAPL_PID_FREQ_OUTPUT reflects NIO-sent value |
| CBB1 HPM RAPL status | `sv.socket0.cbb1.punit.hpm_rapl_perf_limit.show()` | Same as CBB0 |
| NIO LEAF_PERF_STATUS | `sv.socket0.nio.punit.hpm_leaf_perf_status.show()` | Both CBBs reporting status |
| TPMI PERF_STATUS (idx=8) | `sv.socket0.nio.tpmi.perf_status.read()` | PWR_LIMIT_THROTTLE_CTR > 0 after throttle |
| dmesg | `dmesg | grep -i rapl` | No RAPL errors |
| MCA banks | `mcelog --client` | No MCA errors |

### Post-Process

N/A — all verification is real-time register/telemetry checks during test execution.

---

## Section C: NWP Delta Impact

| Aspect | DMR | NWP | Validation Impact |
|--------|-----|-----|-------------------|
| IMH count | 2 (IMH-P root + IMH-S leaf) | **1 NIO** (root only) | Remove leaf-IMH relay verification; NIO sends HPM directly to CBBs |
| CBB count | 4 | **2** | HPM delivery loop: `range(4)` → `range(2)` |
| HPM intermediary | IMH-S forwards RAPL_PERF_LIMIT to CBBs | **None** | Simpler path; no inter-IMH HPM verification needed |
| RACL PID | IMH-S runs local RACL PID | **Not applicable** (single NIO) | Skip RACL-specific HPM fields if present |
| Total cores | Up to 256 | **96** | Adjust workload scale; verify per-core cap across 96 cores |
| Register prefix | `sv.socket0.imh0.*` / `sv.socket0.imh1.*` | **`sv.socket0.nio.*`** | Script path swap required |
| CLOS support | SST CLOS_[0-3] in HPM | **SST-TF supported; PCT supported** | Verify CLOS-partitioned RAPL limits if SST-TF active |
| Platform RAPL | Supported | **ZBB** | Skip platform RAPL source bit verification (bits [39:44]) |

---

## Section D: Spec Refs

- [DMR RAPL Simplification HAS — HPM Messaging](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#hpm-messaging-for-rapl-racl)
- [DMR CBB PM HAS §6.4 — PCode RAPL enforcement](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)
- [DMR IMH PM HAS §7.3 — PrimeCode RAPL distribution](https://docs.intel.com/documents/primecode/primecode_one/firmware%20architecture/ip%20drivers%20and%20libraries/rapl_dmr.html)
- [TCD 22022420817 — Socket RAPL HPM Verification](https://hsdes.intel.com/appstore/article-one/#/22022420817)
- [TCD 22022420798 — Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798)
- [TC 22022421955 — Fast RAPL HPM Message Verification](https://hsdes.intel.com/appstore/article-one/#/22022421955) (related — Fast RAPL-specific)

---

## Section E: Risk Assessment

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| 1 | HPM register paths (`hpm_rapl_perf_limit`, `hpm_leaf_perf_status`) may differ on NWP vs DMR — exact namednodes path not yet confirmed on NWP silicon | High | Validate register paths on first NWP silicon access via `sv.socket0.cbb0.search("hpm", "c")` and `sv.socket0.nio.search("rapl", "c")` |
| 2 | Platform RAPL source bits (39:44) are ZBB on NWP — test must not assert on these bits | Medium | Test steps explicitly skip platform RAPL verification; add negative check that platform bits = 0 |
| 3 | Fast RAPL triggering may require specific power transient profile not achievable in VP | Medium | Mark VP/Simics as reduced-scope environment; full coverage on silicon only |
| 4 | RACL fields in HPM 0x14 (RACL_PID_FREQ_OUTPUT, bits 55:48) may be unpopulated on NWP (single NIO, no RACL) | Low | Do not assert on RACL field; observe only |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify RAPL HPM 0x14/0x16 to both CBBs from single NIO**

1. **Automation**: `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. **Key verification sequence**: Trigger PL1, PL2, Fast RAPL independently; for each scenario verify:
   - HPM 0x14 `RAPL_PID_FREQ_OUTPUT` reduced on both CBB0 and CBB1
   - Correct source bit asserted (PKG_PL1_*, PKG_PL2_*, FAST_RAPL)
   - HPM 0x16 LEAF_PERF_STATUS returned from both CBBs
   - Core frequency capped at delivered ceiling on all 96 cores
3. **NWP simplification**: No IMH-S leaf relay → direct NIO-to-CBB verification only. Remove any DMR-specific inter-IMH steps.
4. **Priority**: High — `plc.feature.p2`; HPM message correctness is the communication path between NIO and CBBs for RAPL enforcement — critical for CBB frequency decisions

### References

- [TCD 22022420817 — Socket RAPL HPM Verification](https://hsdes.intel.com/appstore/article-one/#/22022420817)
- [DMR RAPL HAS — HPM Messaging](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#hpm-messaging-for-rapl-racl)
- [Socket RAPL KB](../../../KB/pm_features/power_rapl/socket_rapl.md)

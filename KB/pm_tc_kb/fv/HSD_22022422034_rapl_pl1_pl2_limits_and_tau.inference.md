# TC Description: RAPL PL1/PL2 Limits and Tau Verification

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422034](https://hsdes.intel.com/appstore/article-one/#/22022422034) |
| **Title** | RAPL PL1/PL2 limits and Tau Verification |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PL1/PL2 control register programming — U11.3 encoding, tau, lock |
| **Parent TCD** | [22022420821 -- Socket RAPL Registers Verification - CSR and TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **PL Control Encoding** scenario defined in [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) §5-B: "PL1_CONTROL / PL2_CONTROL: programmed PWR_LIM readback matches written value (U11.3 encoding); TIME_WINDOW: programmed tau encoding readback matches (exponent-mantissa); LOCK: when set, subsequent writes rejected; readback unchanged." This TC verifies the register encoding, programming, and readback correctness of PL1_CONTROL and PL2_CONTROL via both TPMI and CSR paths. Tau decoding uses the HAS formula: tau = (2^Y) * (1 + X/4) * time_unit, where Y = bits [4:0], X = bits [6:5].

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment |
| BIOS | PL1/PL2 LOCK bit = 0 (unlocked); default PL1/PL2 values |
| Starting state | System booted; RAPL active; registers writable (not locked) |
| TPMI PL1 path | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control |
| TPMI PL2 path | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control |
| CSR path | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg |
| Power encoding | U11.3: 1 LSB = 0.125 W; PWR_LIM [17:0] |
| Tau encoding | TIME_WINDOW [24:18]: Y = [4:0], X = [6:5]; tau = (2^Y) * (1 + X/4) * time_unit |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read TPMI PL1_CONTROL defaults. Record PWR_LIM, TIME_WINDOW, LOCK, PL1_EN fields. | PWR_LIM = fused TDP (U11.3). TIME_WINDOW = default tau encoding. LOCK = 0 (unlocked). PL1_EN = 1 (always enabled on DMR/NWP per RAPL HAS). | Defaults wrong or register unreadable. |
| 2 | Read TPMI PL2_CONTROL defaults. Record PWR_LIM, TIME_WINDOW fields. | PL2 PWR_LIM = 1.2 x TDP (U11.3). TIME_WINDOW = default PL2 tau encoding. | PL2 defaults wrong. |
| 3 | Program PL1_CONTROL.PWR_LIM to a custom value (e.g., 250W = 0x7D0 in U11.3). Read back. | Readback matches written value exactly. | Readback mismatch — encoding error or write failed. |
| 4 | Program PL1_CONTROL.TIME_WINDOW to encode tau = 2 seconds. Compute Y, X per HAS formula. Write. Read back. Decode and verify tau = 2s. | Readback TIME_WINDOW matches written encoding. Decoded tau = 2.0 seconds (within clipped range [1s, 5s]). | Readback mismatch or decoded tau wrong. |
| 5 | Program PL1_CONTROL.TIME_WINDOW to encode tau outside valid range (e.g., 0.5s, below 1s minimum). Read back. | PrimeCode clips to minimum valid tau (1s). Readback reflects clipped value, not written value. | Unclamped value accepted — PrimeCode not clipping. |
| 6 | Program PL2_CONTROL.PWR_LIM to custom value (e.g., 400W). Read back. Program PL2_CONTROL.TIME_WINDOW to valid PL2 tau. Read back and decode. | PL2 PWR_LIM readback matches. PL2 tau decoded correctly and within [11.7ms, 39ms]. | Readback mismatch or PL2 tau out of valid range. |
| 7 | Verify CSR/TPMI consistency: read CSR package_rapl_limit_cfg PL1 and PL2 fields. Compare to TPMI. | CSR PL1/PL2 power and tau fields match TPMI values (within 1 LSB). | CSR/TPMI mismatch. |
| 8 | Lock test: set PL1_CONTROL.LOCK = 1. Read back LOCK field. | LOCK = 1 on readback. | LOCK bit not sticky. |
| 9 | Attempt to write PL1_CONTROL.PWR_LIM with a new value while LOCK = 1. Read back. | PWR_LIM unchanged from pre-write value. Write rejected due to LOCK. | PWR_LIM changed despite LOCK = 1 (lock bypass). |
| 10 | Attempt to write PL1_CONTROL.TIME_WINDOW while LOCK = 1. Read back. | TIME_WINDOW unchanged. Write rejected. | TIME_WINDOW changed despite LOCK. |
| 11 | Attempt to clear LOCK bit (write LOCK = 0) while LOCK = 1. Read back. | LOCK remains 1. LOCK bit cannot be cleared by software — only cold reset. | LOCK cleared to 0 by software write. |
| 12 | Restore original PL1/PL2 values (will require cold reset if locked in this test). Verify no MCA or hang. | Test completes cleanly. | System instability. |

### Pass / Fail Criteria

- **PASS**: Per TCD 22022420821 §5-B — PL1/PL2 PWR_LIM readback matches written value (U11.3 encoding). TIME_WINDOW readback matches written encoding; decoded tau within valid range; out-of-range values clipped by PrimeCode. LOCK bit sticky — once set, writes rejected until cold reset. CSR and TPMI values consistent. No MCA or hang.
- **FAIL**: PWR_LIM readback mismatch. Tau not clipped when out of range. LOCK bit not enforced or clearable by software. CSR/TPMI mismatch. System instability.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| TPMI PL1_CONTROL | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control | PWR_LIM, TIME_WINDOW, LOCK fields correct |
| TPMI PL2_CONTROL | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control | PWR_LIM, TIME_WINDOW fields correct |
| CSR package_rapl_limit_cfg | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg | Matches TPMI PL1/PL2 values |
| TPMI PL_INFO | sv.socket0.nio.punit.tpmi.socket_rapl.pl_info | MAX_PL1, MAX_PL2 bounds for validation |

### Post-Process

N/A

### References

- [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821)
- [Wave 3 Common HAS -- Socket RAPL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)

---

## Section A: NWP Delta

NIO replaces IMH. PL1/PL2 encoding, tau formula, and LOCK behavior unchanged from DMR.

| Aspect | DMR | NWP |
|--------|-----|-----|
| TPMI PL1_CONTROL | sv.socket0.imh0.punit.ptpcfsms... | sv.socket0.nio.punit.ptpcfsms... |
| CSR path | sv.socket0.imh0.punit.ptpcioregs... | sv.socket0.nio.punit.ptpcioregs... |

## Section F: Recommendations

Recommendation: ADOPT — imh0 -> nio paths; verify U11.3 encoding, tau clipping, and LOCK enforcement. Priority: High — PL1/PL2 register interface is the primary power management control surface.

---

## Section F: Recommendation

**Recommendation: ADOPT — NWP register paths already in `imh0` space; test all 4 aspects: lock, tau, clamp, programming**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Verify via TPMI (`ptpcfsms`) and CSR (`ptpcioregs`) paths
3. Test all 4 aspects: lock bit, tau programming, clamp bit, PL1/PL2 custom values

**Priority**: High — `plc.feature.p2`; PL1/PL2 register programming is the fundamental RAPL control interface; lock/clamp validation critical for system security and stability

# TC 16031185456 — ITD-SCENARIO-002 / FV / disabled-D2D-ack-skip

## Test Case Intent

Validates that when D2D stacks are disabled (via HWRS), the Resource Adapter correctly skips ack collection from disabled Phys during VCCUCIEA ITD handshakes. Verifies that ITD voltage changes complete without hang or timeout when disabled D2Ds are present, and that enabled D2Ds still receive req and return ack normally.

### Pre-Conditions

1. NWP silicon platform with reduced D2D topology — at least one D2D stack disabled via HWRS/fuse
2. Remaining D2D links trained and operational
3. ITD enabled with valid fuse coefficients (ITD-FUSE-001 passed)
4. VCCUCIEA steady-state ITD active on enabled stacks (ITD-CONTRACT-003 passed)
5. DVFS handshake working on enabled stacks (ITD-CONTRACT-005 passed)
6. PythonSV access to RA status, HWRS mask, and FIVR VID registers
7. Platform config: at least one of VCCUCIE_SW or VCCUCIE_SE has a partial-disable (shared FIVR with one stack disabled)

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read HWRS D2D enable mask — identify which D2D stacks are disabled | Mask shows ≥1 disabled stack; document which VCCUCIE FIVRs are affected | All stacks enabled (test not applicable — need reduced topology) |
| 2 | Verify RA collection set matches HWRS mask (only enabled D2Ds in collection) | RA programmed to collect ack from enabled stacks only | RA collection set includes disabled D2D (misconfiguration) |
| 3 | Inject temperature change to trigger VCCUCIEA ITD voltage update | ITD recalculation triggered | No ITD trigger |
| 4 | Monitor RA voltage change_req — verify NOT asserted to disabled D2D Phy | No req observed on disabled D2D path | Req sent to disabled/powered-down Phy |
| 5 | Monitor RA voltage change_req — verify asserted to enabled D2D Phy(s) | Enabled Phys receive req normally | Req missing for enabled Phy |
| 6 | Verify ITD request completes without timeout | FIVR voltage transition completes within normal latency (no hang) | RA hangs waiting for ack from disabled D2D |
| 7 | Verify enabled D2D Phys returned change_ack | Ack received from all enabled Phys | Missing ack from enabled Phy |
| 8 | Verify VCCUCIEA FIVR at new correct ITD voltage | Voltage = base + computed ITD within 26 mV | Incorrect voltage or stuck at old value |
| 9 | (Shared FIVR case) For VCCUCIE_SW or SE with one of two stacks disabled: verify ITD completes using only the enabled stack's ack | Completion with single ack from enabled stack | Hang or incorrect behavior on shared FIVR |
| 10 | Repeat for multiple consecutive ITD triggers — verify no cumulative timeout or drift | All triggers complete cleanly | Progressive degradation or eventual hang |

### Pass / Fail Criteria

**PASS:**
- ITD voltage change completes within normal latency (≤2 ms) despite disabled D2D present
- No req assertion to disabled D2D Phy (not queried)
- All enabled D2D Phys receive req and return ack
- Shared FIVR (SW/SE) completes correctly with partial-disable topology
- Final VCCUCIEA voltage correct within 26 mV guardband

**FAIL:**
- RA hangs or times out waiting for ack from disabled D2D
- req asserted to disabled/powered-down Phy (wasted signal to dead path)
- Enabled Phy does not receive req (masking too aggressive)
- FIVR voltage incorrect after handshake with reduced topology
- Shared FIVR deadlocks when one of two stacks is disabled

### Post-Process

N/A — FV automated comparison.

## References

- [TCD 16031185179 — ITD-SCENARIO-002](https://hsdes.intel.com/appstore/article-one/#/16031185179)
- [SOC HSD 22016961651 — VCCUCIEA ITD runtime handshake](https://hsdes.intel.com/appstore/article/#/22016961651)
- [RA MAS §master-slave-voltage-workpoint-change-flow](https://docs.intel.com/documents/arch_datacenter/DMR_MAS/RCF/RA/Resource_Adapter_MAS.html#master-slave-voltage-workpoint-change-flow)

## Section E: Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Platform with disabled D2Ds may not be available in early silicon | high | Use fuse-based D2D disable or HWRS override for test configuration |
| Observing "no req to disabled Phy" is negative validation — harder to confirm | medium | Verify via RA debug counters (req count per D2D should be 0 for disabled) |
| Shared FIVR topology (SW/SE) not guaranteed in all platform configs | medium | Confirm VCCUCIE_SW/SE mapping before test; skip if single-stack per FIVR |

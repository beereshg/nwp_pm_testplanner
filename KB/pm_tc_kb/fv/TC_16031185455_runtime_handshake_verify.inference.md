# TC 16031185455 — ITD-CONTRACT-005 / FV / runtime-handshake-verify

## Test Case Intent

Validates that the VCCUCIEA ITD runtime DVFS handshake protocol executes correctly: before every ITD-triggered voltage change on VCCUCIEA, a change_req is asserted to the UCIe Phy via the Resource Adapter, the Phy returns change_ack, and only then does the FIVR transition to the new voltage. Verifies protocol compliance during normal runtime temperature drift.

### Pre-Conditions

1. NWP silicon platform with UCIe D2D links trained (mainband operational)
2. ITD enabled with valid fuse coefficients (ITD-FUSE-001 passed)
3. VCCUCIEA steady-state ITD compensation active (ITD-CONTRACT-003 passed — offset within 26 mV)
4. SB Phy out of reset (Phy can honor handshake)
5. At least one enabled D2D stack per VCCUCIEA FIVR
6. PythonSV access to `sv.socket0.imh0.punit.*` and RA status registers
7. Test command: `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3 --dvfs_handshake`

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read current VCCUCIEA voltage and temperature for all 4 sub-domains (NW, NE, SW, SE) | Baseline voltage and temp captured | Unable to read voltage/temp registers |
| 2 | Inject temperature change of ≥5°C on UCIe DTS (via thermal injection or workload) to trigger ITD recalculation | Temperature change detected by Primecode ITD kernel | DTS injection not reflected in readback |
| 3 | Monitor RA voltage change_req assertion for VCCUCIEA domain | change_req asserted within one FW update cycle (~1ms) of temp change | No change_req observed after temperature change |
| 4 | Verify VCCUCIEA FIVR VID has NOT changed before change_ack is received | VID remains at pre-change value while awaiting ack | VID changes before ack — protocol violation |
| 5 | Monitor Phy change_ack return | change_ack received within expected latency (≤480 ns from req) | Ack timeout or no ack observed |
| 6 | After ack: verify VCCUCIEA FIVR transitions to new ITD target voltage | New VID = base + computed ITD offset for new temperature | VID does not update after ack, or incorrect voltage |
| 7 | Verify final voltage matches ITD dual-slope algorithm output within 26 mV guardband | Actual voltage within ±26 mV of computed expected | Voltage outside guardband |
| 8 | Repeat steps 2-7 for a cooling temperature change (opposite direction) | Same protocol observed for voltage decrease | Protocol skipped for downward voltage change |

### Pass / Fail Criteria

**PASS:**
- change_req observed BEFORE every FIVR VID transition (both increase and decrease)
- change_ack received BEFORE FIVR VID reaches new target
- Ack latency ≤480 ns from req assertion
- No premature voltage change observed between req and ack
- Final voltage matches ITD algorithm output within 26 mV

**FAIL:**
- FIVR VID changes without preceding change_req (protocol bypass)
- FIVR VID changes before change_ack received (premature transition)
- Ack latency exceeds 480 ns (timeout)
- No handshake observed despite ITD voltage change occurring
- Voltage outside 26 mV guardband after handshake completes

### Post-Process

N/A — FV automated comparison.

## References

- [TCD 16031185178 — ITD-CONTRACT-005](https://hsdes.intel.com/appstore/article-one/#/16031185178)
- [SOC HSD 22016961651 — VCCUCIEA ITD runtime handshake](https://hsdes.intel.com/appstore/article/#/22016961651)
- [RA MAS §master-slave-voltage-workpoint-change-flow](https://docs.intel.com/documents/arch_datacenter/DMR_MAS/RCF/RA/Resource_Adapter_MAS.html#master-slave-voltage-workpoint-change-flow)
- [D2D PM HAS §VCCIO ITD](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D_PM/auto/f7.D2D_VCCIO_ITD.8fd81f.zoom.html)

## Section E: Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| RA req/ack signals may not be directly observable via PythonSV | high | Verify RA status register exposes req/ack state; alternative: use ITH VISA trace on RA sideband |
| Temperature injection magnitude may not trigger ITD in all domains | medium | Use DTS override register for deterministic injection |
| Handshake timing (240-480 ns) difficult to capture without cycle-accurate observation | medium | Use HSLE XOS for timing verification; FV validates protocol ordering only |

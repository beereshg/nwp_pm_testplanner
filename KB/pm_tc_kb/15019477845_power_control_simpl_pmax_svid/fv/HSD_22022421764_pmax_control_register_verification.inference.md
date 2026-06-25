# Deep Analysis: PMAX CONTROL Register Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421764 |
| **Title** | PMAX CONTROL Register Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX control register — Vtrip offset, trigger programming, verified via `pmax_control` register |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **PMAX_CONTROL** is correctly programmed after boot on NWP, and verify PMAX is not spuriously active at idle. Key assertions: `pmax_control` fields are readable and match BIOS/fuse policy; `PMAX_STATUS.VALID = 1` after firmware init; PMAX perf-limit indication is 0 at idle. `PMAX_VTRIP_0_OFFSET` is signed 7-bit (bit 6 = sign, bits[5:0] at 2 mV/LSB). `PMAX_DISABLE_MASK`: 00=MT enabled, 01=disable hard throttle, 10=disable soft throttle, 11=disable both. `LOCK` makes register read-only after BIOS boot. NWP: single NIO root die; `sv.socket0.nio.punit.ptpcfsms.ptpcfsms` is the PMAX register owner.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.nio` reachable without timeout |
| Imports | `import time` |
| Namespace | `nio = sv.socket0.nio` alias set |
| Platform S0 | Fully booted; no pending MCA |
| PMAX owner | NWP PMAX owner is NIO; use `nio.punit.ptpcfsms.ptpcfsms` |
| BIOS lock | Know whether BIOS is expected to lock PMAX_CONTROL before runtime |
| Idle condition | No PMAX / PL4 / stress stimulus running during test steps |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read PMAX_CONTROL and decode main fields. `import time; nio = sv.socket0.nio; ptp = nio.punit.ptpcfsms.ptpcfsms; pmax_ctrl = ptp.pmax_control; def rd(o,n,d='N/A'): return getattr(o,n).get_value() if hasattr(o,n) else d; vtrip_off=rd(pmax_ctrl,'pmax_vtrip_0_offset'); lock=rd(pmax_ctrl,'lock'); gpio_tx=rd(pmax_ctrl,'pmax_gpio_transmitter_enable'); trig_dis=rd(pmax_ctrl,'pmax_trigger_disable'); disable_mask=rd(pmax_ctrl,'pmax_disable_mask'); pmax_en=rd(pmax_ctrl,'pmax_en'); print(f'pmax_en={pmax_en} lock={lock} vtrip_offset={vtrip_off} gpio_tx={gpio_tx} trig_dis={trig_dis} disable_mask={disable_mask}'); assert isinstance(vtrip_off,int),'PMAX_VTRIP_0_OFFSET must be readable'` | PMAX_CONTROL readable; PMAX_VTRIP_0_OFFSET is integer; lock/GPIO/disable-mask fields decode cleanly | pmax_control unreadable or vtrip_offset invalid — PMAX TPMI path mismatch or PMAX owner not initialized |
| 2 | Check PMAX_STATUS if implemented. `if hasattr(ptp,'pmax_status'): ps=ptp.pmax_status; valid=rd(ps,'valid'); cfg=rd(ps,'pmax_config_status'); print(f'pmax_status.valid={valid} config_status={cfg}'); assert valid==1,'PMAX_STATUS.VALID must be 1 after boot'` | PMAX_STATUS.VALID = 1; config_status readable | VALID=0 long after boot — firmware did not copy PMAX calibration/config status |
| 3 | Validate trigger mode and BIOS policy consistency. `print(f'disable_mask={disable_mask} [00=MT,01=no-hard,10=no-soft,11=disabled]'); print(f'gpio_tx={gpio_tx} trig_dis={trig_dis} lock={lock}'); assert disable_mask in (0,1,2,3),'Unexpected disable_mask value'` | Field combination self-consistent with BIOS PMAX mode; lock=1 if BIOS-locked | disable_mask contradicts BIOS intent; unexpected lock state — collect BIOS PMAX knob state |
| 4 | Verify PMAX perf-limit indication clear at idle. `plr=ptp.perf_limit_reasons.read(); PMAX_BIT=8; pmax_active=bool(plr&(1<<PMAX_BIT)); print(f'PLR=0x{plr:08X} PMAX bit[{PMAX_BIT}]={pmax_active}'); assert not pmax_active,'PMAX throttle active at idle'` | PMAX perf-limit bit clear at idle — no spurious PMAX events | PMAX PLR bit asserted at idle — spurious trigger or stale status; collect pmax_control + pmax_status + NLOG |

---

### Pass / Fail Criteria

- **PASS**: All 4 steps complete without assertion failure; pmax_control fields decode correctly matching BIOS configuration; PMAX PLR bit = 0 at idle.
- **FAIL**: Any assertion fails, pmax_control unreadable, PMAX_STATUS.VALID = 0 after boot, or PMAX PLR active at idle.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_control | nio.punit.ptpcfsms.ptpcfsms.pmax_control | Read succeeds; fields decode cleanly; lock/disable_mask match BIOS policy |
| pmax_status | nio.punit.ptpcfsms.ptpcfsms.pmax_status | VALID=1 after boot if implemented |
| perf_limit_reasons | nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | PMAX/MT-PMAX bit clear at idle |
| PMAX_TRIGGER_IO | NIO GPIO TPMI view | TX/RX mode matches BIOS PMAX trigger configuration |
| NLOG PMAX | peg_client --nlog --filter PMAX | No unexpected PMAX-trigger events at idle |

---

### Post-Process

Leave PMAX configuration unchanged (test is read-only). If PMAX-active indication unexpectedly set: capture pmax_control, pmax_status, perf_limit_reasons, NLOG; verify system was truly idle. If BIOS lock unexpected: collect BIOS knob state and platform boot log.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX_CONTROL fields; PMAX_VTRIP_0_OFFSET signed encoding; LOCK; DISABLE_MASK semantics
- [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/pmax/dmr/dmr_pmax_detector_has/dmr_pmax_detector_has.html) — PMAX firmware copy behavior; TPMI to internal PMAX control
- [MT PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/gnr/features/multi-threshold_pmax_detector/mt_pmax.html) — Multi-threshold detector; PLR bit definitions
- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) — PMAX_TRIGGER_IO NIO routing; TX/RX mode
- [Punit Registers](https://docs.intel.com/documents/sysip_pm/punit/assets/punit_registers.html) — PMAX_CONTROL / PMAX_STATUS field definitions
- [OakStream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) — BIOS PMAX offset / trigger setup knobs

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PMAX (Power Maximum) is functional on NWP (not on ZBB list). This test verifies `pmax_control` register fields including Vtrip offset and trigger configuration. BIOS locks this register at boot, so it is read-only at runtime.

**NWP key difference**: DMR has `imh0` and `imh1` → NWP has **single `imh0` only**. Remove all `imhX (X=0/1)` double-check iterations; only check `imh0`.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax -tM 60
```

### NWP Register Path
```python
# NWP: single imh0 (no imh1)
pmax_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control
pmax_ctrl.show()  # Read all pmax_control fields

# Verify:
# - Vtrip offset programmed correctly
# - Trigger configuration matches BIOS
# - Register is locked (BIOS-locked after boot)
```

### Pass Criteria
- `pmax_control` fields match BIOS-programmed values
- Register locked after boot (cannot be modified at runtime)
- Vtrip offset and trigger fields non-zero / match spec
- `pmax` PMx plugin passes for NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; remove imh1 references (NWP single imh0); PMAX control register architecture same**

**Priority**: Medium — `plc.feature.p2`; PMAX control register baseline is prerequisite for all PMAX functional tests

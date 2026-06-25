# TCD: PL4 Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420691](https://hsdes.intel.com/appstore/article-one/#/22022420691) |
| **Title** | PL4 Verification |
| **Parent TPF** | [15019477947](https://hsdes.intel.com/appstore/article-one/#/15019477947) |
| **Feature** | PMAX |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**PL4 (Power Limit 4)** is the hard instantaneous power cap — it is the maximum power the platform permits the SoC to consume at any instant, distinct from RAPL PL1/PL2 which are running-average limits. PrimeCode converts the PL4 power value into voltage offsets for PMax Vtrip thresholds, effectively shifting them earlier to prevent PL4 exceedance before hardware PMax fires.

**Key architectural facts (DMR PMax HAS + Punit Registers):**
- `SOCKET_PL4_POWER_DEFAULT` fuse = non-zero; propagated to `socket_rapl_pl4_control.pwr_lim`
- Default state: `pwr_lim_en = 0` (PL4 not enforced by default); `pwr_lim` = 1.5-3× TDP; `lock = 0`
- PL4 Vtrip offset formula: `PL4_Vccin0 = (PL4 - P_nonVccin) × FUSED_PL4_SCALE_FACTOR_IMH0`
- MT offsets (mt0_offset, mt1_offset, mt2_offset) in `pmax_config` adjusted by PL4 computation
- NWP: single IMH0; single VCCIN; single scale factor (no split IMH0/IMH1)

### Block Diagram

```
SOCKET_PL4_POWER_DEFAULT fuse
       |
       v
PrimeCode (NIO) — PL4 initialization at PH6
Compute: PL4_Voffset = (PL4 - P_nonVccin) x FUSED_PL4_SCALE_FACTOR
       |
       v
socket_rapl_pl4_control.pwr_lim (TPMI)
pmax_config.mt0/mt1/mt2_offset (adjusted Vtrip thresholds)
       |
       v
MT-PMax Detector: Vtrip thresholds shifted earlier
Prevents PL4 exceedance before hardware hard-throttle fires
```

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421777](https://hsdes.intel.com/appstore/article-one/#/22022421777) | PL4 Fuses Verification | Runnable_On_N-1 |
| [22022421778](https://hsdes.intel.com/appstore/article-one/#/22022421778) | PL4 Perf Limit Verification | Runnable_On_N-1 |
| [22022421782](https://hsdes.intel.com/appstore/article-one/#/22022421782) | PL4 Power Limit Register Verification | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| socket_rapl_pl4_control | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control | pwr_lim_en (default 0); pwr_lim (1.5-3x TDP); lock |
| SOCKET_PL4_POWER_DEFAULT | sv.socket0.imh0.fuses.punit.pcode_socket_pl4_power_default | PL4 fuse; non-zero; must match TPMI pwr_lim |
| pmax_config MT offsets | sv.socket0.imh0.pmax.pmax0.pmax_config | mt0_offset, mt1_offset, mt2_offset (signed 7-bit) |
| socket_rapl_power_unit | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_power_unit | power = 3 (1/8 W/LSB) for PL4 encoding |

---

## Section 3: Reset, Power, and Clocking

- PL4 fuse read at PH6; pwr_lim programmed to TPMI; MT offsets computed and written
- pwr_lim_en = 0 by default (PL4 not enforcing at runtime)
- lock = 0 (BIOS may lock before OS for security)

---

## Section 4: Programming Model

- PL4 power in U15.3 fixed-point (divide by 8 for Watts); same encoding as PL1/PL2
- MT offsets: signed 7-bit (bit 6 = sign, bits[5:0] at 2 mV/LSB)
- Ratio check: PL4 should be 1.5-3× TDP to protect against transient overcurrent

---

## Section 5: Operational Behavior

1. PH6: PrimeCode reads SOCKET_PL4_POWER_DEFAULT fuse
2. Computes Vtrip offsets from PL4 target power and FUSED_PL4_SCALE_FACTOR
3. Writes mt0/mt1/mt2_offset to pmax_config; writes pwr_lim to socket_rapl_pl4_control
4. At runtime: if pwr_lim_en=1, PMax Vtrip thresholds adjusted so PMax fires at PL4 boundary
5. Default (pwr_lim_en=0): Vtrip thresholds use fuse defaults; PL4 not runtime-enforced

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| PL4 fuse = 0 | PrimeCode cannot set MT offsets; PMAX uses default thresholds |
| PL4 > 3x TDP | Vtrip thresholds may not shift; PL4 has no effective enforcement |
| PL4 < 1.5x TDP | Excessively aggressive thresholds; may cause spurious PMAX triggers |
| lock=1 (BIOS locked) | pwr_lim and lock cannot be modified at runtime |

---

## Section 7: Security / Safety / Policy

- PL4 limits are customer-facing; must be BIOS-lockable before OS access
- PL4 fuse is a physical OTP value; cannot be changed post-manufacturing
- Validation that forces PL4 enforcement (pwr_lim_en=1) must be done in controlled environment

---

## Section 8: References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PL4 to Vtrip offset formula; pwr_lim_en; FUSED_PL4_SCALE_FACTOR
- [Punit Registers](https://docs.intel.com/documents/sysip_pm/punit/assets/punit_registers.html) — socket_rapl_pl4_control; pmax_config MT offset fields
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — PL4 power unit encoding; NWP single IMH topology

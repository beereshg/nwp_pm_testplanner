# TCD: PMAX Fuses Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420708](https://hsdes.intel.com/appstore/article-one/#/22022420708) |
| **Title** | PMAX fuses Verification |
| **Parent TPF** | [15019477947](https://hsdes.intel.com/appstore/article-one/#/15019477947) |
| **Feature** | PMAX |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**PMAX Fuses** are one-time-programmable values that configure the PMAX protection hardware at manufacturing time. PrimeCode reads these fuses at PH6 and propagates them to runtime registers. All fuse operations are on **IMH0 only** for NWP.

**Key fuses verified (DMR PMax HAS + Detector HAS):**

| Fuse | Expected Value | Purpose |
|------|---------------|---------|
| `punit_supervises_pmax` | = 1 | Enables Punit management of PMAX response |
| `punit_root_supervisor` | = 1 | Enables root supervisor mode (soft throttle path) |
| `pmax_mt_en` | = 1 | Enables multi-threshold PMax (MT-PMax) |
| `pmax_l1_en` | = 1 | Enables Soft L1 throttle path |
| `SOCKET_PL4_POWER_DEFAULT` | > 0 | PL4 power fuse; propagated to `socket_rapl_pl4_control.pwr_lim` |

**Fuse-to-register propagation:** `pmax_mt_en` fuse value must match `pmax_control2.pmax_mt_en` register. Mismatch indicates PrimeCode initialization failure.

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421799](https://hsdes.intel.com/appstore/article-one/#/22022421799) | PMAX Related fuses Verification | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| punit_supervises_pmax fuse | sv.socket0.imh0.fuses.punit.pmsrvr_throttle_pmax_service_punit_supervises_pmax_fuse | Must = 1 |
| punit_root_supervisor fuse | sv.socket0.imh0.fuses.punit.pmsrvr_throttle_pmax_service_punit_root_supervisor_fuse | Must = 1 |
| pmax_mt_en fuse | sv.socket0.imh0.fuses.pmax_top.pmax_control2_pmax_mt_en | Must = 1; must match register |
| pmax_l1_en fuse | sv.socket0.imh0.fuses.pmax_top.pmax_control2_pmax_l1_en | Must = 1 (Soft L1 enabled) |
| pmax_control2.pmax_mt_en | sv.socket0.imh0.pmax.pmax0.pmax_control2.pmax_mt_en | Must match fuse value |
| SOCKET_PL4_POWER_DEFAULT | sv.socket0.imh0.fuses.punit.pcode_socket_pl4_power_default | Must be non-zero |

---

## Section 3: Reset, Power, and Clocking

- Fuses are read at PH0/PH1 and propagated to runtime registers at PH6 by PrimeCode
- Fuse values are immutable after manufacturing; cannot be changed at runtime
- Warm reset preserves fuse values; cold reset re-reads fuses (same values)

---

## Section 4: Programming Model

- Read-only test: no register writes
- Fuse reads via `sv.socket0.imh0.fuses.*` namednodes path
- Register propagation check: compare fuse value to corresponding runtime register
- Test tool: `python flexconPM.py` (NWPSV.ini) automates NWP fuse verification

---

## Section 5: Operational Behavior

1. PH0: Fuse download to per-die fuse registers
2. PH6: PrimeCode reads PMAX fuses; initializes pmax_service, pmax_control2, pmax_config
3. Runtime: fuse-derived configuration active; punit_supervises_pmax enables soft throttle management

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| pmax_mt_en fuse = 0 | MT-PMax disabled; only basic PMax without multi-threshold; check SKU |
| pmax_mt_en fuse != pmax_control2 register | PrimeCode initialization failure at PH6 |
| punit_supervises_pmax fuse = 0 | PMAX events not managed by Punit; harder to recover from hard throttle |
| SOCKET_PL4_POWER_DEFAULT = 0 | PL4 not programmed; MT offsets cannot be computed |

---

## Section 7: Security / Safety / Policy

- Fuse values are OTP (one-time programmable); errors require wafer re-spin
- Fuse mismatch with register is a firmware initialization bug; report as P1 defect
- fuses.* namednodes path requires privileged PythonSV access

---

## Section 8: References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX fuse structure; punit_supervises_pmax; pmax_mt_en; pmax_l1_en
- [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/pmax/dmr/dmr_pmax_detector_has/dmr_pmax_detector_has.html) — Fuse-to-register propagation; pmax_control2
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PMAX fuse topology; single IMH0

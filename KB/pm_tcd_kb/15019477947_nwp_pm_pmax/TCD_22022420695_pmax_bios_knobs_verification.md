# TCD: PMAX BIOS Knobs Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420695](https://hsdes.intel.com/appstore/article-one/#/22022420695) |
| **Title** | PMAX Bios Knobs Verification |
| **Parent TPF** | [15019477947](https://hsdes.intel.com/appstore/article-one/#/15019477947) |
| **Feature** | PMAX |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**PMAX BIOS Knobs** control the runtime PMAX behavior via EFI Shell configuration. BIOS programs `pmax_control` fields before OS handoff and locks the register. NWP has **VccIn 0 only** (single NIO, no IMH1 / VccIn 1 like DMR-AP).

**Key BIOS knobs (OakStream CPUPM FAS + DMR PMax HAS):**
- **VccIn 0 Adjustment (Vtrip Offset)**: BIOS configures `pmax_vtrip_0_offset` — signed value shifts Vtrip threshold (2 mV/LSB)
- **PMAX Trigger Setup**: BIOS configures `pmax_gpio_trigger_enable` — enables/disables PMAX_TRIGGER_IO GPIO input mode
- Both knobs propagate to `pmax_control` register; LOCK=1 set by BIOS after programming

**NWP delta:** VccIn 0 only (no VccIn 1); GPIO trigger routed through NIO.

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421787](https://hsdes.intel.com/appstore/article-one/#/22022421787) | PMAX Offset and Offset Sign BIOS Knob Verification | Runnable_On_N-1 |
| [22022421788](https://hsdes.intel.com/appstore/article-one/#/22022421788) | PMAX TRIGGER IO BIOS Knobs Verification | Runnable_On_N-1 |
| [16030715664](https://hsdes.intel.com/appstore/article-one/#/16030715664) | [PSS] BIOS configuration | PSS |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| pmax_control.pmax_vtrip_0_offset | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control.pmax_vtrip_0_offset | Signed 7-bit Vtrip offset (2mV/LSB); from BIOS VccIn 0 Adjustment |
| pmax_control.pmax_gpio_trigger_enable | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control.pmax_gpio_trigger_enable | BIOS Trigger Setup knob; 0=disabled (default) |
| pmax_control.lock | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control.lock | =1 after BIOS locks; register read-only |

---

## Section 3: Reset, Power, and Clocking

- BIOS programs pmax_control during CPL3; sets LOCK=1 before OS handoff
- BIOS must be in EFI Shell to change PMAX knobs; changes take effect on next boot
- Default values: Vtrip offset=0; Trigger Setup=0 (GPIO trigger disabled)

---

## Section 4: Programming Model

- VccIn 0 Adjustment: BIOS EFI Shell → Advanced → Power Management → PMAX Detector Config → VccIn 0 Adjustment
- PMAX Trigger Setup: same menu path → Trigger Setup value (0=disabled, 1=enabled)
- Post-boot: read pmax_control via sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control to verify

---

## Section 5: Operational Behavior

1. BIOS reads PMAX knob settings from NVRAM during CPL3
2. Programs pmax_control.pmax_vtrip_0_offset per VccIn 0 Adjustment value
3. Programs pmax_control.pmax_gpio_trigger_enable per Trigger Setup value
4. Sets LOCK=1; pmax_control is now read-only for OS
5. Test verifies register reflects BIOS knob settings; PMx pmax_bios plugin validates end-to-end

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| VccIn 1 option shown in BIOS | NWP BIOS error — must show VccIn 0 only |
| Vtrip offset not propagating | BIOS not writing to TPMI; collect BIOS log |
| LOCK=0 after boot | BIOS did not lock pmax_control; security gap |
| Default trigger=0 changed | Verify register reflects new value on next boot |

---

## Section 7: Security / Safety / Policy

- pmax_control.lock must be 1 before OS handoff to prevent OS tampering
- PMAX TRIGGER IO enabled by BIOS allows platform to inject external PMAX events
- EFI Shell PMAX knobs are platform-configuration; restricted to BIOS admin access

---

## Section 8: References

- [OakStream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) — BIOS PMAX offset / trigger setup knob definitions
- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — pmax_vtrip_0_offset encoding; LOCK semantics
- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) — PMAX_TRIGGER_IO routing; NWP VccIn 0 only

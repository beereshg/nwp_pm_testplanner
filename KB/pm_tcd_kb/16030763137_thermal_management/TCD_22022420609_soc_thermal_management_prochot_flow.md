# TCD: [SoC Thermal Management] Prochot Flow

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420609](https://hsdes.intel.com/appstore/article-one/#/22022420609) |
| **Title** | [SoC Thermal Management] Prochot Flow |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | PROCHOT entry/exit for CBB — frequency drops to Pm, restores on removal |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**PROCHOT Flow** covers the SoC response to the `PROCHOT_N` GPIO signal — a platform power/thermal control input that causes the SoC to throttle to a programmed **PROCHOT Response Power** limit. On NWP, `PROCHOT_N` is **input-only** (output mode removed); external assertion activates TCC and triggers fast throttle + response-power frequency limits on both IMH and CBB dies.

**Key architectural facts (from Newport GPIO HAS + DMR PROCHOT HAS + Primecode Prochot flow):**
- `PROCHOT_N` is active-low GPIO input; assertion sets `EXTERNAL_PROCHOT` + activates TCC
- Punit generates **fastpath to Primecode** on both assertion and deassertion
- Punit asserts **fast throttle wire to cores** on PROCHOT assertion
- IMH Primecode clips `PROCHOT_RESPONSE_POWER` to range [PKG_MIN_POWER, TDP]; converts to frequency limits
- IMH sends `PROCHOT_POWER_LIMITED_FREQ_LIMIT` to secondary IMH and leaf CBBs via HPM
- CBB entry: CBB asserts fast throttle → pCode applies HPM-delivered PROCHOT freq limit → deasserts fast throttle
- CBB exit: D2D signal deasserts → CBB removes core/ring PROCHOT ceiling
- VR Hot escalation path: if VR doesn't cool → asserts `xxPROCHOT` → same PROCHOT flow

### Block Diagram

```
  DTS / VR Hot / Platform Thermal Sources
  (direct platform assertion or VR Hot escalation)
         |  external / escalated trigger
         v
  PROCHOT_N GPIO Input (input-only on NWP)
  Asynchronous assertion / deassertion
         |
         v
  PCode / Primecode / Punit PROCHOT Handling
    Fastpath on assertion + deassertion
    Clips PROCHOT_RESPONSE_POWER to [PKG_MIN_POWER, TDP]
    Converts to frequency limits
         |
         v
  TCC / PROCHOT Response Power Policy
  HPM: PROCHOT_POWER_LIMITED_FREQ_LIMIT -> CBBs + secondary IMH
         |                              |
         v                              v
  IMH Thermal Actions             CBB Thermal Actions
  (TC 22022421553)                (TC 22022421548)
  Entry: reduce IMH fabric freq   Entry: fast throttle -> pCode WP
  Exit: remove IMH fabric ceiling Exit: remove core/ring ceiling
         |                              |
         +-------------------------------+
         |
         v
  TPMI / MSR / PMSB (status + telemetry)
  + IMH root-die / CBB0 / CBB1 coordination
```

### Per-TC Behavior

| TC | Validates | Flow Path |
|----|-----------|----------|
| 22022421548 | CBB Entry/Exit | Fast throttle → HPM freq limit → WP applied; exit removes ceiling |
| 22022421553 | IMH Entry/Exit | Fabric freq reduction on entry; ceiling removed on exit |
| 22022421557 | Prochot Response Power | PROCHOT_RESPONSE_POWER clipping to TDP/PKG_MIN_POWER; correct freq limit |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421548](https://hsdes.intel.com/appstore/article-one/#/22022421548) | [Prochot Flow] Verify Prochot CBB Entry and Exit Flow | Runnable_On_N-1 |
| [22022421553](https://hsdes.intel.com/appstore/article-one/#/22022421553) | [Prochot Flow] Verify Prochot IMH Entry and Exit Flow | Runnable_On_N-1 |
| [22022421557](https://hsdes.intel.com/appstore/article-one/#/22022421557) | [Prochot Flow] Verify operation of Prochot Response Power | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **`PROCHOT_N` GPIO** | IMH package pin (input only on NWP) | Platform asserts → EXTERNAL_PROCHOT set; TCC activates |
| **`PROCHOT_RESPONSE_POWER`** | Firmware policy register | Power limit for PROCHOT throttling; clipped to [PKG_MIN_POWER, TDP] |
| **HPM `PROCHOT_POWER_LIMITED_FREQ_LIMIT`** | IMH → CBBs HPM message | Delivers PROCHOT-derived freq limit to CBB pCode |
| **`IO_INTERDIE_THROTTLE_SIGNALS_STATUS.PROCHOT`** | CBB Punit DFX CSR | PROCHOT status visible on CBB; DFX mask/force hooks |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and throttle registers |
| MSR | `MSR_POWER_CTL` (0x1FC), 0x19C, 0x1A2 | Prochot enable, thermal status bits |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| HPM | CBB ↔ IMH HPM messages | Cross-die thermal limit propagation |
| GPIO | IMH GPIO bumps | External VR Hot / Prochot input signals |

---

## Section 3: Reset, Power, and Clocking

- Thermal DTS sensors initialize during PH1 (BIOS TPMI init); readings valid after PH6
- TCC threshold programmed by BIOS; runtime update via TPMI
- VR Hot and Prochot signals are asynchronous; PCode responds within 1 slow-loop (~1 ms)
- Thermal state persists across warm reset; cold reset re-initializes all thresholds

---

## Section 4: Programming Model

- BIOS programs TCC thresholds and thermal knobs during CPL3
- PCode slow-loop (~1 ms) polls thermal telemetry and applies throttle decisions
- OS reads thermal data via MSRs and TPMI; writes to override registers require privilege
- Test methodology: PMx `prochot_thermal` / `thermal_mgt` plugin or direct register injection

---

## Section 5: Operational Behavior

**PROCHOT Entry flow (both CBB and IMH):**
1. Platform asserts `PROCHOT_N` GPIO low
2. Primary IMH Punit fastpath triggers PROCHOT handling; TCC activates
3. Primecode clips `PROCHOT_RESPONSE_POWER` to [PKG_MIN_POWER, TDP]
4. Primecode converts response power → frequency limit; sends HPM `PROCHOT_POWER_LIMITED_FREQ_LIMIT` to CBBs + secondary IMH
5. **IMH:** reduces local fabric frequencies to PROCHOT-derived ceiling
6. **CBB:** asserts fast throttle wire to cores; pCode applies HPM-delivered PROCHOT freq limit as WP; deasserts fast throttle

**PROCHOT Exit flow:**
1. Platform deasserts `PROCHOT_N`
2. Punit fastpath triggers exit handling; primary IMH deasserts D2D PROCHOT to CBBs
3. **IMH:** removes fabric frequency ceiling
4. **CBB:** pCode removes PROCHOT core/ring frequency ceiling

**Response Power clipping (TC 22022421557):** `PROCHOT_RESPONSE_POWER` must be verified clipped to TDP or PKG_MIN_POWER boundaries; freq limit delivered via HPM must match expected value.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| `PROCHOT_RESPONSE_POWER` above TDP | Primecode clips to TDP; verify clipped value used for freq limit |
| `PROCHOT_RESPONSE_POWER` below PKG_MIN_POWER | Primecode clips to minimum; verify minimum value enforced |
| Short PROCHOT pulse | Fast throttle fires; freq limits applied; exit removes ceilings cleanly |
| PROCHOT asserted while already thermally limited | Most restrictive effective limit wins; PROCHOT limit does not relax existing throttle |
| VR Hot escalates to PROCHOT | PROCHOT flow activates with VR-origin trigger; same entry/exit behavior |
| DFX mask disables PROCHOT handling | Input visible via `IO_INTERDIE_THROTTLE_SIGNALS_STATUS` but action path blocked |
| PROCHOT deasserts before CBB WP fully applied | Exit flow still removes ceiling once handling completes |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) -- PROCHOT_N input-only; TCC activation; asynchronous behavior
- [DMR Thermal HAS -- PROCHOT](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- PROCHOT entry/exit flow; response power clipping; HPM freq limit delivery
- [Primecode PROCHOT Flow](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/flows_pm_features/prochot.html) -- Fastpath; PROCHOT_RESPONSE_POWER; CBB fast throttle; deassertion exit
- [CBB Punit DFX MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/MAS/Punit_DFX/PUNIT_DFX_MAS.html) -- IO_INTERDIE_THROTTLE_SIGNALS_STATUS.PROCHOT; DFX mask/force hooks
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SoC Thermal; PROCHOT scope

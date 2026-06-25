# TCD: [SoC Thermal Management] VR Hot

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420628](https://hsdes.intel.com/appstore/article-one/#/22022420628) |
| **Title** | [SoC Thermal Management] VR Hot |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | VR Hot — CBB MBVR SVID Therm Alert detection and throttle response |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**VR Hot** is a **VR-originated thermal protection flow**, distinct from DTS-based die thermals. When a VR temperature reaches ~97% of its maximum, it asserts a **SVID Thermal Alert** (`STATUS1[ThermAlert]`); this triggers a managed throttle response on IMH and all CBB dies. If the VR continues to heat and reaches maximum temperature, it can escalate by asserting `xxPROCHOT` for a faster, stronger response.

**Key architectural facts (from DMR Thermal HAS + Primecode HotVR flow + CBB Slow Limits FAS):**
- IMH Primecode periodically polls `SVID_VR_STATUS` (~1 ms) on both IMH instances
- On VR Hot detection, IMH Primecode sends **`DNS_EVENT_DELIVERY[VR_THERM_ALERT=1]`** to leaf CBB dies and peer IMH die
- **IMH action:** reduces fabric frequency to P1; updates perf-limit reason
- **CBB action:** reduces core and ring/fabric frequency to P1; updates core/ring perf-limit reasons with `VR_THERMALERT`
- **`MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]`:** when set, Primecode ignores VR Hot; no throttle action; no `DNS_EVENT_DELIVERY` sent
- On clear: `DNS_EVENT_DELIVERY[VR_THERM_ALERT=0]` sent; CBB/IMH remove P1 ceilings and clear perf-limit status
- Escalation path: if Thermal Alert throttling is insufficient → VR asserts `xxPROCHOT` → PROCHOT flow executes

### Block Diagram

```
  VR / MBVR
  STATUS1[ThermAlert] at ~97% of VR Tmax
         |
         v
  IMH Primecode / Punit
  Periodic SVID_VR_STATUS poll (~1 ms)
  VR_THERM_ALERT_DISABLE check (MSR_POWER_CTL)
         |  disabled: no action
         |  enabled:
         v
  DNS_EVENT_DELIVERY[VR_THERM_ALERT=1]
  (to CBB0, CBB1, peer IMH)
         |                    |
         v                    v
  IMH Actions            CBB Actions
  Fabric freq -> P1      Core + Ring freq -> P1
  Perf-limit reason      Perf-limit reason
  update (IMH)           update (VR_THERMALERT)

  On clear: DNS_EVENT_DELIVERY[VR_THERM_ALERT=0]
            -> Remove P1 ceilings on all dies

  Escalation: VR too hot -> asserts xxPROCHOT
              -> PROCHOT flow (stronger response)

  TPMI / MSR / PMSB: perf-limit observability
```

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421673](https://hsdes.intel.com/appstore/article-one/#/22022421673) | [VR Hot] Verify CBB VR Hot Actions | Runnable_On_N-1 |
| [22022421674](https://hsdes.intel.com/appstore/article-one/#/22022421674) | [VR Hot] Verify IMH VR Hot Actions | Runnable_On_N-1 |
| [22022421676](https://hsdes.intel.com/appstore/article-one/#/22022421676) | [VR Hot] Verify VR_THERM_ALERT_DISABLE | Runnable_On_N-1 |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421673](https://hsdes.intel.com/appstore/article-one/#/22022421673) | [VR Hot] Verify CBB VR Hot Actions | Runnable_On_N-1 |
| [22022421674](https://hsdes.intel.com/appstore/article-one/#/22022421674) | [VR Hot] Verify IMH VR Hot Actions | Runnable_On_N-1 |
| [22022421676](https://hsdes.intel.com/appstore/article-one/#/22022421676) | [VR Hot] Verify VR_THERM_ALERT_DISABLE | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **`SVID_VR_STATUS`** | SVID bus polling by IMH Primecode | `STATUS1[ThermAlert]` — VR Hot assertion/deassertion source |
| **`DNS_EVENT_DELIVERY[VR_THERM_ALERT]`** | IMH → CBB0 / CBB1 / peer IMH HPM | Carries VR Hot assert (=1) and deassert (=0) to all dies |
| **`MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]`** | Per-socket MSR | Disables Primecode VR Hot response; no throttle, no HPM distribution |
| **Perf-limit reason registers** | TPMI + MSR perf-limit paths | VR_THERMALERT visible as throttle cause on IA/core and ring domains |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and throttle observability |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| HPM | CBB ↔ IMH HPM messages | Cross-die VR Hot event distribution |

---

## Section 3: Reset, Power, and Clocking

- VR Hot handling is a **runtime PM/thermal control flow** — becomes valid after PM firmware and SVID access are operational
- Detection is **not** DTS-based; IMH Primecode periodically polls `SVID_VR_STATUS` (~1 ms)
- VR thermal thresholds (`TEMP_MAX`, `TEMPERATURE_ZONE`) are configured by the **platform/BIOS**, not by OS software
- Thermal state persists across warm reset; cold reset re-initializes firmware state; VR registers retain platform-programmed values
- If VR Hot is insufficient to cool the VR, the VR can escalate to `xxPROCHOT` for asynchronous aggressive response

---

## Section 4: Programming Model

- **Platform/BIOS** configures VR thermal thresholds (`TEMP_MAX`, `TEMPERATURE_ZONE`) on the VR side via SVID; CPU does not configure those VR registers directly
- **`MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]`** — set to mask VR Hot action; Primecode ignores `SVID_VR_STATUS[ThermAlert]` and does not send `DNS_EVENT_DELIVERY`; supports TC 22022421676
- IMH Primecode polling of `SVID_VR_STATUS` is the primary detection mechanism; no interrupt-driven path — period ~1 ms
- When enabled and alert asserted: IMH applies P1 fabric ceiling; distributes `DNS_EVENT_DELIVERY[VR_THERM_ALERT=1]`; CBBs apply P1 core/ring ceiling
- Test methodology: force `STATUS1[ThermAlert]` via SVID injection or BIOS/PMx `prochot_thermal` / `thermal_mgt` plugin

---

## Section 5: Operational Behavior

**VR Hot entry flow:**
1. VR temperature reaches ~97% of `TEMP_MAX`; VR asserts **SVID Thermal Alert** (`STATUS1[ThermAlert]`)
2. IMH Primecode detects condition by polling `SVID_VR_STATUS` (~1 ms period)
3. If `VR_THERM_ALERT_DISABLE=1`: Primecode ignores the condition — no further action
4. If enabled: IMH Primecode sends **`DNS_EVENT_DELIVERY[VR_THERM_ALERT=1]`** to CBB0, CBB1, and peer IMH die
5. **IMH:** reduces fabric frequency to P1; updates perf-limit reason
6. **CBB (each):** reduces core and ring/fabric frequency to P1; updates perf-limit reasons with `VR_THERMALERT`

**VR Hot exit flow:**
1. VR cools; clears `STATUS1[ThermAlert]`
2. IMH Primecode detects clear on next `SVID_VR_STATUS` poll
3. Sends **`DNS_EVENT_DELIVERY[VR_THERM_ALERT=0]`** to CBB0, CBB1, peer IMH
4. All dies remove P1 frequency ceilings and clear `VR_THERMALERT` perf-limit status

**Escalation path:** if P1 throttling is insufficient → VR asserts `xxPROCHOT` → PROCHOT flow engages with stronger response

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| `VR_THERM_ALERT_DISABLE=1` | Primecode ignores VR Hot; no throttle applied; no `DNS_EVENT_DELIVERY` sent |
| VR Hot clears quickly (before next poll) | Condition may not be seen; no spurious P1 ceiling applied |
| VR Hot remains asserted | P1 frequency ceiling maintained until explicit clear polling cycle |
| Multiple VRs hot simultaneously | Socket-wide P1 ceiling applied; all affected dies throttled |
| VR Hot on one IMH only | `DNS_EVENT_DELIVERY` still propagates to all dies including peer IMH and both CBBs |
| P1 throttling insufficient | VR escalates to `xxPROCHOT`; PROCHOT flow engages on assertion |
| CBB and IMH perf-limit reasons mismatch | Both IMH and CBB perf-limit paths should show `VR_THERMALERT` as cause when active |

---

## Section 7: Security / Safety / Policy

- VR Hot response is firmware- and platform-managed; VR thermal thresholds are configured on the VR/platform side, not by OS software
- Forcing SVID Thermal Alert or masking VR Hot handling requires privileged access (BIOS/JTAG level)
- `VR_THERM_ALERT_DISABLE` is a debug/validation control; must not be left enabled in production environments
- VR Hot escalation to PROCHOT is a safety-critical path; test injection requires controlled power/thermal environment

---

## Section 8: References

- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- VR layered thermal protection; Thermal Alert at 97%; VR_HOT escalation to PROCHOT
- [Primecode HotVR Flow](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/flows_pm_features/hotvr_flow.html) -- DNS_EVENT_DELIVERY[VR_THERM_ALERT]; IMH/CBB action; VR_THERM_ALERT_DISABLE
- [DMR CBB Slow Limits FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Slow_Limits/cbb_slow_limits_FAS.html) -- CBB core/ring P1 ceiling on VR_THERMALERT; perf-limit reason bits
- [Wave3 Socket Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) -- SVID_VR_STATUS polling; VR Hot socket-wide propagation
- [Primecode FHAS SERVERPMFW-1021](https://docs.intel.com/documents/primecode/fhas/DMR/SERVERPMFW-1021.html) -- VR_THERM_ALERT_DISABLE behavior; Primecode validation context
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SoC Thermal; VR Hot scope

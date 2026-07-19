# TPF 15019477949 — [NWP PM] SVID (Serial Voltage ID)

| Field | Value |
|-------|-------|
| **TPF ID** | [15019477949](https://hsdes.intel.com/appstore/article-one/#/15019477949) |
| **Title** | [NWP PM] SVID (Serial Voltage ID) |
| **Parent TP** | [15019477845 — [NWP PM] Power Control (SIMPL/PMAX/SVID)](https://hsdes.intel.com/appstore/article-one/#/15019477845) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**SVID (Serial Voltage ID)** is a **hardware interface with firmware sequencing**. SVID is a 3-wire, open-drain, synchronous serial bus (SVID 2.0/3.0 compatible) used by PCode/PrimeCode to communicate with external motherboard voltage regulators (MBVRs). The CPU acts as the SVID master, issuing SetVID, GetReg, SetReg, and other commands to control voltage rails, read VR telemetry, and handle VR error conditions. SVID is critical-path for boot, reset, and all dynamic voltage transitions.

**Feature gating:** SVID is always enabled on NWP production parts. BIOS configures VR addresses, bus speed, and error handling policy. SVID interface is implemented through GPIO pins with staging flops to hide Punit-to-GPIO delay.

**NWP delta from DMR:** Single VCCIN domain on NIO (imh0) — DMR-AP has dual VCCIN domains, each with its own SVID bus and MBVR. NWP typically implements two SVID buses (SVID0, SVID1); rail-to-bus mapping is platform-specific.

### Feature-Specific Constants

| Parameter | Value | Source |
|-----------|-------|--------|
| SVID protocol | SVID 2.0/3.0 compatible | NWP PM HAS |
| Physical interface | 3-wire: SVIDCLK, SVIDDATA, SVIDALERT_N | NWP PM HAS |
| SVID buses | 2 (SVID0, SVID1) | NWP PM HAS |
| Max VRs per bus | 8 (4-bit addressing, 1 reserved broadcast) | SVID spec |
| Max VRs total | 16 | SVID spec |
| Clock frequency | 16.67–25 MHz | SVID spec |
| Data rate | 12.5–25 MT/s | SVID spec |
| VCCIN domains | 1 (single VCCIN on NIO) | NWP topology |
| Primary MBVR | VCCIN MBVR managed via SVID | NWP PM HAS |
| Additional FIVR rails | VCCCAB, VCCC2CDIG (platform-specific) | NWP PM HAS |
| Error retry mechanism | 3-strike error detection per VR | NWP PM HAS |
| Register root | sv.socket0.nio.punit.svid_* | NWP register map |

---

## Section 2: Design Details

### SVID — Full Stack (CPU Master to Platform VR)

<!-- raw-html -->
<div style="max-width:680px;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;margin:16px 0;">

  <!-- OS / Tool Layer -->
  <div style="background:#e8f4fd;border:2px solid #2196f3;border-radius:8px 8px 0 0;padding:12px 18px;">
    <div style="font-weight:700;color:#1565c0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 6: OS / Tool (indirect)</div>
    <div style="color:#1a237e;line-height:1.7;font-size:11.5px;">
      OS observes voltage behavior via <code style="background:#fff;border:1px solid #90caf9;border-radius:3px;padding:1px 5px;">cpufreq / intel_pstate</code> &nbsp;·&nbsp;
      Voltage transitions driven by PCode; OS sees frequency/voltage result
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- BIOS Configuration Layer -->
  <div style="background:#fce4ec;border:2px solid #e91e63;padding:12px 18px;">
    <div style="font-weight:700;color:#880e4f;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 5: BIOS Configuration</div>
    <div style="color:#880e4f;line-height:1.8;font-size:11.5px;">
      VR address + bus mapping &nbsp;·&nbsp; Bus speed + pull-up strength &nbsp;·&nbsp;
      IccMax / OVP / UVP configuration via SetReg at boot &nbsp;·&nbsp;
      SVIDALERT_N handling policy (mask/unmask, error response)
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Firmware Sequencing Layer -->
  <div style="background:#fff3e0;border:2px solid #ff9800;padding:12px 18px;">
    <div style="font-weight:700;color:#e65100;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 4: Firmware Sequencing &nbsp;<span style="font-weight:400;font-size:10px;color:#bf360c;">(PCode / PrimeCode)</span></div>
    <div style="color:#bf360c;line-height:1.8;font-size:11.5px;">
      Boot: enumerate VRs → configure initial voltages/power states → SetVID ramp-up<br>
      Runtime: SetVID-fast (C6 exit) / SetVID-slow (normal) / SetVID-decay (C6 entry) / SetPS (efficiency)<br>
      Error handling: 3-strike retry, SVIDALERT_N monitoring, AllCall error logging
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- SVID Interface Layer -->
  <div style="background:#f3e5f5;border:2px solid #9c27b0;padding:12px 18px;">
    <div style="font-weight:700;color:#6a1b9a;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 3: SVID Bus Interface &nbsp;<span style="font-weight:400;font-size:10px;color:#4a148c;">(GPIO + arbiter)</span></div>
    <div style="color:#4a148c;line-height:1.8;font-size:11.5px;">
      <code style="background:#fff;border:1px solid #ce93d8;border-radius:3px;padding:1px 5px;">SVID_COMMAND</code> register → drives transactions on SVIDCLK/SVIDDATA<br>
      Staging flops hide Punit-to-GPIO delay &nbsp;·&nbsp;
      Arbiter FSM manages bus contention and transaction ordering<br>
      SVIDALERT_N input monitored for VR-initiated status/error
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- Physical Bus Layer -->
  <div style="background:#e8f5e9;border:2px solid #4caf50;padding:12px 18px;">
    <div style="font-weight:700;color:#2e7d32;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 2: Physical Bus &nbsp;<span style="font-weight:400;font-size:10px;color:#1b5e20;">(3-wire open-drain)</span></div>
    <div style="color:#1b5e20;line-height:1.8;font-size:11.5px;">
      SVIDCLK (source-synchronous, CPU-driven) &nbsp;·&nbsp;
      SVIDDATA (bi-directional, open-drain) &nbsp;·&nbsp;
      SVIDALERT_N (VR-driven, open-drain) &nbsp;·&nbsp;
      Pull-ups at farthest VR
    </div>
  </div>

  <!-- Arrow -->
  <div style="text-align:center;font-size:18px;color:#555;line-height:1.2;">&#11015;</div>

  <!-- VR / Platform Layer -->
  <div style="background:#ffebee;border:2px solid #f44336;border-radius:0 0 8px 8px;padding:12px 18px;">
    <div style="font-weight:700;color:#c62828;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;">Layer 1: VR / Platform Hardware</div>
    <div style="color:#b71c1c;line-height:1.8;font-size:11.5px;">
      MBVR (VCCIN) &nbsp;·&nbsp; Optional additional VRs (VCCCAB, VCCC2CDIG) &nbsp;·&nbsp;
      VR responds to SetVID/GetReg/SetReg &nbsp;·&nbsp;
      Asserts SVIDALERT_N on error/status change
    </div>
  </div>

</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer (from full-stack diagram) | PSS (VP) | PSS (HSLE) | FV | PV | Notes |
|---|---|---|---|---|---|
| OS / Tool (indirect) | ❌ | ❌ | ❌ | ✅ | OS observes voltage behavior indirectly |
| BIOS Configuration | ✅ | ❌ | ✅ | ✅ | VP safe for VR config testing |
| Firmware Sequencing | ✅ | ✅ | ✅ | indirect | All tiers validate PCode SVID commands |
| SVID Bus Interface | ⚠️ | ✅ | ✅ | ❌ | VP has simplified SVID model |
| Physical Bus | ❌ | ❌ | ✅ | ✅ | Real bus required |
| VR / Platform Hardware | ❌ | ❌ | ✅ | ✅ | Real VR required |

### SVID Command Protocol

| Command | Code | Description | Timing |
|---------|------|-------------|--------|
| SetVID-fast | 0x01 | Set VID with maximum slope (quick transitions, e.g. C6 exit) | Fast ramp |
| SetVID-slow | 0x02 | Set VID with slow slope (normal transitions) | Controlled ramp |
| SetVID-decay | 0x03 | Output voltage decays with load current (C6 entry, energy saving) | Load-dependent |
| SetPS | 0x04 | Set power state for VR efficiency at light load | Immediate |
| SetRegADR | 0x05 | Set register address pointer in VR | Immediate |
| SetRegDAT | 0x06 | Write data to VR register | Immediate |
| GetReg | 0x07 | Read data from VR register | 1 transaction |
| TestMode | 0x08 | Vendor-specific test mode | Vendor-defined |
| SetWP | 0x09 | Execute workpoint from VR table (voltage + power state) | VR-defined |

### SVID Boot and Reset Sequence

```
Power-on / Reset:
    PCode initializes SVID bus hardware (GPIO, arbiter)
    │
    ├── VR Enumeration
    │      └── Scan all VR addresses on SVID0/SVID1
    │      └── Identify present VRs via GetReg(STATUS1)
    │
    ├── VR Configuration
    │      └── SetRegADR + SetRegDAT: program IccMax, OVP/UVP thresholds
    │      └── SetRegADR + SetRegDAT: configure switching frequency
    │      └── SetPS: set initial power state
    │
    ├── Voltage Ramp-up
    │      └── SetVID-slow: ramp VCCIN to initial operating voltage
    │      └── Monitor SVIDALERT_N for VR errors during ramp
    │
    └── Runtime Ready
           └── SVID bus available for dynamic SetVID-fast/slow/decay
           └── SVIDALERT_N monitoring active
           └── 3-strike error detection enabled

C6 Entry:
    SetVID-decay → VCCIN decays with load (energy saving)
    SetPS → VR enters low-power state

C6 Exit:
    SetVID-fast → rapid VCCIN ramp to operating voltage
    SetPS → VR returns to active state
```

### NWP vs DMR SVID Topology

| Aspect | NWP Newport (NIO) | DMR-AP |
|--------|-------------------|--------|
| VCCIN domains | Single (imh0) | Dual (IMH0, IMH1) |
| SVID buses | 2 (SVID0, SVID1) | 2+ (per-IMH) |
| VCCIN MBVR | 1 on imh0 SVID bus | 1 per IMH die |
| Additional rails | VCCCAB, VCCC2CDIG (platform-specific) | Additional per-domain |
| FIVR master interface | imh0 acts as SVID master | Each IMH is SVID master |
| Cross-die coordination | Not needed (single VCCIN) | Required between IMH0/IMH1 |

### Interface & Register Matrix

| Register / MSR | Field | Default | Feature effect | Tier validated |
|---|---|---|---|---|
| SVID_COMMAND | RUN_BUSY | 0 | Set to 1 to issue transaction; clears on completion | FV, PSS |
| SVID_COMMAND | ERROR | 0 | Set by HW on transaction error (NAK, timeout) | FV |
| SVID_COMMAND | ADDRESS[3:0] | 0 | Target VR address (0–15, 15=broadcast) | FV, PSS |
| SVID_COMMAND | COMMAND[3:0] | 0 | SVID command type (SetVID, GetReg, etc.) | FV, PSS |
| SVID_COMMAND | PAYLOAD | 0 | Data payload for SetVID/SetReg commands | FV, PSS |
| SVID_COMMAND | IFC_SELECT | 0 | SVID bus select (0=SVID0, 1=SVID1) | FV |
| svid_vr_status[15:0] | STATUS1 | 0 | Latest STATUS1 from each VR | FV |
| svid_vr_error_status | error_vector | 0 | Bit vector: VRs with 3-strike errors | FV |
| svid_datain | data[7:0] | 0 | Data read from VR by GetReg | FV |

### Observability

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| SVID_COMMAND register | Register | PythonSV: `sv.socket0.nio.punit.svid_command.show()` | Current/last SVID transaction details |
| svid_vr_status | Register | PythonSV: `sv.socket0.nio.punit.svid_vr_status.read()` | VR STATUS1 per-VR status |
| svid_vr_error_status | Register | PythonSV: `sv.socket0.nio.punit.svid_vr_error_status.read()` | 3-strike error vector |
| svid_datain | Register | PythonSV: `sv.socket0.nio.punit.svid_datain.read()` | Last GetReg response data |
| SVIDALERT_N pin | GPIO pin | Scope / logic analyzer | VR error/status assertion |
| SVIDCLK / SVIDDATA | GPIO pin | Scope / protocol analyzer | Bus traffic waveform |
| Arbiter FSM state | Register | PythonSV: arbiter status register | Bus arbitration state for debug |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| Platform VR type (analog/digital) | Different VR response characteristics | All SVID TCDs |
| SVIDALERT_N handling policy | Masked vs unmasked error response | Error handling TCD |
| Number of VRs on bus | More VRs = more complex enumeration | Enumeration TCD |
| Platform rail mapping | SVID0 vs SVID1 bus assignment | Bus config TCD |
| Overclocking platform | May use higher VCCIN; different VR config | Voltage control TCD |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| BIOS configuration | BIOS knobs: VR address mapping, bus speed, error policy |
| PCode / PrimeCode | `src/ip/svid/` — SVID command sequencing, boot/reset init, error handling |
| SVID interface HW | GPIO pins (SVIDCLK, SVIDDATA, SVIDALERT_N), staging flops, arbiter FSM |
| VR firmware | External VR firmware — responds to SVID commands, drives SVIDALERT_N |

---

## Section 3: Validation Strategy

Three-tier validation is required because SVID spans firmware command sequencing (modelable in PSS), physical bus protocol (requires real hardware), and VR interaction (requires real platform).

> **Layer coverage:** See §2 — Validation-Tier Layer Claim table for which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → SVID model | Firmware command sequencing, boot flow, error handling logic |
| PSS — HSLE | Single-die RTL (imh0) | PythonSV → SVID RTL | SVID bus interface behavior, arbiter FSM, GPIO timing |
| FV | Post-silicon NWP | PythonSV → namednodes | Real VR communication, bus protocol, voltage transitions |
| PV | Post-silicon NWP + OS | OS tools, scope | Platform-level voltage behavior, VR response |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | FV | PV |
|---|---|---|---|---|
| Firmware SVID command sequencing error | ✅ | ✅ | ✅ | indirect |
| Boot VR enumeration failure | ✅ | ✅ | ✅ | indirect |
| SetVID voltage ramp timing error | ❌ | ⚠️ | ✅ | indirect |
| SVIDALERT_N handling logic bug | ✅ | ✅ | ✅ | ❌ |
| 3-strike error detection failure | ✅ | ✅ | ✅ | ❌ |
| VR address misconfiguration | ✅ safe | ❌ | ✅ | ❌ |
| Bus contention / open-drain failure | ❌ | ❌ | ✅ | ✅ |
| STATUS1 read while voltage pending (hang) | ⚠️ | ✅ | ✅ | ❌ |
| AllCall broadcast error attribution | ✅ | ✅ | ✅ | ❌ |
| Platform rail mapping error | ❌ | ❌ | ✅ | ✅ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| Boot VR enumeration and configuration | ✅ | ✅ | ❌ | Verify full boot sequence |
| SetVID-fast (C6 exit ramp) | ⚠️ | ✅ | ❌ | Real voltage transition timing |
| SetVID-slow (normal transition) | ⚠️ | ✅ | ❌ | Controlled ramp verification |
| SetVID-decay (C6 entry) | ⚠️ | ✅ | ❌ | Load-dependent decay behavior |
| GetReg / SetReg VR register access | ✅ | ✅ | ❌ | VR register read/write |
| SVIDALERT_N error injection | ✅ | ✅ | ❌ | Error handling flow |
| 3-strike error escalation | ✅ | ✅ | ❌ | Retry exhaustion behavior |
| Multi-VR bus arbitration | ❌ | ✅ | ❌ | Real bus contention |
| Platform VR response characteristics | ❌ | ❌ | ✅ | Real VR timing |

---

## Section 5: Risks & Dependencies

### Active Risks

- **VR compatibility:** SVID protocol compliance varies across VR vendors — platform-specific validation required.
- **SVIDALERT_N flooding:** Repeated VR errors can stall PCode SVID sequencing if error handling is not bounded.
- **STATUS1 read deadlock:** If STATUS1 is read while a voltage request is pending, VR may never indicate "settled" — firmware must implement timeout.
- **Bus signal integrity:** Open-drain bus with long traces and multiple VRs is susceptible to reflections and noise.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Real VR hardware response timing | FV + PV only | Silicon bus + real VR required |
| **G-2** | Platform-specific rail mapping validation | FV + PV only | Requires real platform topology |
| **G-3** | Bus signal integrity (reflections, noise) | PV only | Requires scope measurement on real platform |
| **G-4** | VR vendor-specific behavior | PV only | Vendor VR firmware required |

---

## Section 6: DFX Considerations

- **SVID_COMMAND register:** Full transaction status and error reporting for each SVID command — inspectable via PythonSV.
- **svid_vr_status / svid_vr_error_status:** Per-VR status and 3-strike error tracking available for validation and debug.
- **GPIO probing:** SVIDCLK, SVIDDATA, SVIDALERT_N pins can be probed with scope or protocol analyzer for bus-level debug.
- **Arbiter FSM state:** Internal arbiter state visible for bus contention debugging.
- **AllCall error log:** Broadcast command errors logged for post-mortem analysis.
- **Firmware trace:** fw_runtime_tracker log captures SVID command sequences and error events.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| VR not responding on enumeration | Boot sequence TCD | PCode marks VR absent; continues with remaining VRs |
| SVIDALERT_N asserted during SetVID ramp | Voltage transition TCD | PCode aborts ramp, logs error, retries |
| 3-strike error on critical VR (VCCIN MBVR) | Error handling TCD | Fatal: PCode triggers MCA / warm reset |
| AllCall broadcast to multiple VRs with one NAK | AllCall TCD | Error logged; PCode retries individually to isolate failing VR |
| STATUS1 read during pending SetVID-fast | STATUS1 race TCD | Firmware timeout required; VR may not indicate settled |
| Bus pull-up too weak (slow rise time) | Signal integrity TCD | Transaction errors / NAKs; BIOS adjust pull-up strength |
| VR address conflict (two VRs same address) | Enumeration TCD | Bus collision; PCode detects via error and logs |
| SVID bus speed too fast for platform | Bus config TCD | Transaction errors; BIOS reduce bus speed |
| C6 exit with VR in low-power state and SVIDALERT_N active | C-state transition TCD | PCode must clear alert before SetVID-fast |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

*No TCDs currently defined under this TPF. TCD creation is pending.*

### References

- [NWP PM HAS — SVID section](https://hsdes.intel.com/appstore/article-one/#/15019477949) — feature specification
- [NWP PM MAS — Power Control chapter](https://hsdes.intel.com/appstore/article-one/#/15019477845) — parent TP
- [SVID 2.0/3.0 Protocol Specification](https://hsdes.intel.com/appstore/article-one/#/) — industry protocol reference
- [DMR PM HAS — SVID (baseline reference)](https://hsdes.intel.com/appstore/article-one/#/) — DMR baseline for SVID

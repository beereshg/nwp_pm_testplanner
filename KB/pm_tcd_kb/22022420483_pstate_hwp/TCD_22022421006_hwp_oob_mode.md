# TCD 22022421006 -- HWP OOB Mode

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421006](https://hsdes.intel.com/appstore/article-one/#/22022421006) |
| **Title** | HWP OOB Mode |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [22022420483 -- Pstate-HWP](https://hsdes.intel.com/appstore/article-one/#/22022420483) |
| **Child TCs** | [22022422318](https://hsdes.intel.com/appstore/article-one/#/22022422318) -- HWP OOB Mode BIOS configuration<br>[22022422326](https://hsdes.intel.com/appstore/article-one/#/22022422326) -- HWP OOB Mode EPP resolution<br>[22022422332](https://hsdes.intel.com/appstore/article-one/#/22022422332) -- HWP OOB Mode HWP Autonomous P-state Selection (APS)<br>[22022422337](https://hsdes.intel.com/appstore/article-one/#/22022422337) -- HWP OOB Mode Turbo Disabled Request Resolution |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**HWP OOB (Out-of-Band) Mode** allows the BMC/platform to manage P-state policy without OS cooperation. In OOB mode, **PCode ignores OS writes to MSR 0x774** and instead honors HWP requests from **TPMI registers** written by the BMC through **OOBMSM**. On **NWP/DMR**, PECI-based OOB is zero-bug-bounced / removed, so **TPMI is the sole OOB path**.

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.3px;">HWP OOB Mode -- End-to-End Data Flow</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <div style="display:flex;gap:0;align-items:flex-start;margin-bottom:12px;flex-wrap:wrap;">
      <div style="background:#e8eaf6;border:2px solid #3949ab;border-radius:6px;padding:8px 12px;min-width:110px;text-align:center;">
        <div style="font-weight:700;color:#3949ab;font-size:11px;">BIOS (CPL3)</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">ProcessorHWPMEnable=2<br>MISC_PWR_MGMT[8]=1<br>HWP hidden from OS</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">boot</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e8f5e9;border:2px solid #2e7d32;border-radius:6px;padding:8px 12px;min-width:110px;text-align:center;">
        <div style="font-weight:700;color:#2e7d32;font-size:11px;">BMC / OOBMSM</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">TPMI HWP registers<br>Index 53, Param 0x1<br>Min/Max/EPP</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">TPMI</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;min-width:130px;text-align:center;">
        <div style="font-weight:700;color:#e65100;font-size:11px;">Acode APS/UBPS</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;"><b>Uses OOB EPP</b><br>OS MSR 0x774 ignored<br>Package-level policy</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">~1ms</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#fce4ec;border:2px solid #c62828;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;">
        <div style="font-weight:700;color:#c62828;font-size:11px;">PCode (PUnit)</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">Global constraints:<br>ICCP · PL1/PL2 · Thermal<br>Guardrail (Pn)</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 6px 0;">
        <div style="font-size:9px;color:#555;">WP</div>
        <div style="border-top:2px solid #555;width:30px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e1f5fe;border:2px solid #0277bd;border-radius:6px;padding:8px 12px;min-width:100px;text-align:center;">
        <div style="font-weight:700;color:#0277bd;font-size:11px;">Core FIVR+PLL</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">GV transition<br>~few μS<br>PERF_STATUS</div>
      </div>
    </div>
    <div style="background:#ffebee;border:1px solid #ef5350;border-radius:5px;padding:8px 12px;font-size:11px;margin-bottom:8px;">
      <strong>Key Difference from Native:</strong> OS MSR 0x774 writes are <b>ignored</b> by PCode. HWP policy comes exclusively from <b>BMC via TPMI</b>. All cores/threads share the <b>same package-level</b> HWP policy.
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Validation targets:</strong> (1) BIOS OOB mode knob activates correctly &nbsp;&#8212;&nbsp; (2) OS HWP_REQUEST writes ignored &nbsp;&#8212;&nbsp; (3) TPMI HWP_REQUEST honored &nbsp;&#8212;&nbsp; (4) EPP from OOB path takes effect
    </div>
  </div>
</div>
<!-- /raw-html -->

### Native vs OOB Mode Comparison

| Aspect | Native Mode (OS) | OOB Mode (BMC) |
|--------|------------------|----------------|
| **Control Path** | OS via MSR 0x774 | BMC via TPMI (Index 53) |
| **Granularity** | Per-thread | Package-level (all cores) |
| **HWP MSRs visible to OS** | Yes | No (CPUID hides HWP) |
| **BIOS knob** | ProcessorHWPMEnable=1 (MISC_PWR_MGMT[6]=1) | ProcessorHWPMEnable=2 (MISC_PWR_MGMT[8]=1) |
| **EPP source** | OS HWP_REQUEST[31:24] | TPMI OOB_HWP_REQUEST |
| **Use case** | General-purpose OS | Bare-metal, OEM platform control, SmartNIC offload |

### Key Concepts

| Concept | Description |
|---------|-------------|
| **OOB Mode** | Out-of-Band — BMC controls HWP without OS involvement |
| **TPMI** | Topology Power Management Interface — sole OOB path on NWP/DMR (PECI removed) |
| **OOBMSM** | Out-of-Band Management System Manager — BMC-facing interface for TPMI access |
| **PCS** | Platform Configuration Service — TPMI register abstraction used by BMC |
| **Index 53** | TPMI PCS index for HWP OOB registers |
| **IB_WRITE_BLOCK** | TPMI control bit to lock out in-band (OS) write access |

### NWP-Specific Deltas

- **TPMI-only OOB path** — PECI-based HWP OOB is zero-bug-bounced on NWP; TPMI is the sole mechanism.
- **Same APS algorithm** — APS/UBPS in Acode unchanged; uses OOB-supplied EPP instead of OS EPP.
- **Package-level policy** — All cores receive the same min/max/EPP from OOB request (no per-thread granularity).
- **2 CBBs** — Fewer cores but same OOB behavior; package-level policy applies uniformly.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422318 — HWP OOB Mode BIOS configuration](https://hsdes.intel.com/appstore/article-one/#/22022422318) | BIOS knob | Verify ProcessorHWPMEnable=2 activates OOB mode; CPUID hides HWP from OS |
| [22022422326 — HWP OOB Mode EPP resolution](https://hsdes.intel.com/appstore/article-one/#/22022422326) | EPP priority | Verify OOB-TPMI EPP overrides in-band OS EPP; EPP source priority correct |
| [22022422332 — HWP OOB Mode APS](https://hsdes.intel.com/appstore/article-one/#/22022422332) | APS with OOB EPP | Verify APS/UBPS operates correctly with OOB-supplied EPP and Activity Window |
| [22022422337 — HWP OOB Mode Turbo Disabled](https://hsdes.intel.com/appstore/article-one/#/22022422337) | Turbo cap | Verify HWP max capped at P1 when TURBO_DISABLE set in OOB mode |

---

## Section 2: Interfaces and Protocols

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS (CPL3) | Set ProcessorHWPMEnable=2 (OOB mode) | BIOS Setup |
| 2 | BIOS (CPL3) | Write MISC_PWR_MGMT[8]=1 to enable OOB mode | MSR 0x1AA |
| 3 | BIOS (CPL3) | Do NOT enumerate HWP in ACPI/CPUID | CPUID |
| 4 | BMC | Discover TPMI HWP capability via PCS | TPMI |
| 5 | BMC | Optionally set IB_WRITE_BLOCK to lock out in-band access | TPMI |
| 6 | BMC | Write OOB_HWP_REQUEST (min/max/EPP) via PCS Index 53, Param 0x1 | TPMI |
| 7 | PCode (PUnit) | Read TPMI HWP request registers | TPMI Shadow |
| 8 | PCode (PUnit) | Resolve global constraints: ICCP, PL1/PL2, thermal | Slowloop |
| 9 | PCode (PUnit) | Enforce Pn guardrail via GUARDRAIL_CLKI.MIN_RATIO | HW Register |
| 10 | PCode (PUnit) | Write constraint limits to WP registers (Fceil, WP4) | WP Registers |
| 11 | Acode Slowloop | Read TPMI-sourced HWP request (NOT OS MSR 0x774) | Internal |
| 12 | Acode APS/UBPS | Compute target ratio using OOB EPP and utilization | Algorithm |
| 13 | Acode | Clip target to PCode-provided WP limits | Internal |
| 14 | Acode | Issue WP command to core FIVR controller | Core Mailbox |
| 15 | Core FIVR+PLL | Execute GV transition to new frequency/voltage | Hardware |
| 16 | Core | Update IA32_PERF_STATUS with new ratio | MSR 0x198 |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|-----|---------|-----------|
| 1 | BMC | OOBMSM | Write OOB_HWP_REQUEST via TPMI PCS Index 53 | TPMI |
| 2 | OOBMSM | PCode | Latch TPMI HWP request to shadow registers | Internal |
| 3 | OS | Core MSR | WRMSR IA32_HWP_REQUEST (0x774) | MSR |
| 4 | PCode | — | **IGNORE** OS MSR 0x774 write (OOB mode active) | — |
| 5 | PCode | WP Regs | Update Fceil, WP4 with global constraint limits | WP |
| 6 | Acode Timer | APS | hcpm_timer expiry triggers UBPS evaluation | Internal |
| 7 | APS | OOB Shadow | Read OOB-sourced EPP, min, max | Internal |
| 8 | APS | Algorithm | Compute gain_term, decay_term using OOB EPP | Internal |
| 9 | APS | Algorithm | Select target_ratio | Internal |
| 10 | Acode | Core | Issue WP command | Mailbox |
| 11 | Core FIVR | PLL | Configure VID and frequency | Hardware |
| 12 | Core | MSR | Update IA32_PERF_STATUS | Register |

### Interface Table

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| MSR | MISC_PWR_MGMT (0x1AA) | RW | [8] OOB mode enable; [6] Native mode enable |
| TPMI | PCS Index 53, Param 0x0 | RO | OOB HWP_CAPABILITIES (mirrors MSR 0x771 layout) |
| TPMI | PCS Index 53, Param 0x1 | RW | OOB HWP_REQUEST (min/max/EPP) — BMC writes this |
| TPMI | PCS Index 53, Param 0x2 | RW | OOB EPB (Energy Performance Bias) |
| TPMI | PCS Index 53, Param 0x3 | RW | HWP Native PECI Override Enable |
| TPMI | IB_WRITE_BLOCK | RW | Lock out in-band (OS) write access to HWP |
| MSR | IA32_HWP_REQUEST (0x774) | — | **Ignored** by PCode in OOB mode |
| MSR | IA32_PERF_STATUS (0x198) | RO | Current operating ratio (readable by OS even in OOB mode) |

---

## Section 3: Reset / Power / Clocking

- **BIOS CPL3**: BIOS sets ProcessorHWPMEnable=2 to activate OOB mode. Writes MISC_PWR_MGMT[8]=1. Does NOT enumerate HWP in ACPI/CPUID — OS sees HWP as absent.
- **Mode selection**: Native vs OOB mode selection is **boot-time only** — changing requires a system reset.
- **BMC initialization**: BMC discovers TPMI HWP capability, optionally locks out in-band access, then writes OOB_HWP_REQUEST with desired policy.
- **APS slowloop**: Acode APS evaluates TPMI-sourced HWP request every ~1 ms; uses OOB-supplied EPP.
- **PCode constraints**: PCode resolves global constraints and writes WP limits; same as Native mode.
- **GV transition**: Same mechanism as Native mode — core FIVR + PLL transition to target frequency.

---

## Section 4: Programming Model

HWP OOB mode programming differs from Native mode in the control path and policy source.

### Stage 1: BIOS Enable (CPL3)

BIOS configures OOB mode and hides HWP from OS:

\\\
Write MISC_PWR_MGMT[8] = 1  — enable OOB mode
Write MISC_PWR_MGMT[6] = 0  — disable Native mode
Do NOT enumerate HWP in ACPI (_OSC/_PDC returns HWP unsupported)
CPUID.06H:EAX[7] = 0 (or BIOS patches CPUID to hide HWP)
\\\

### Stage 2: BMC Initialization

BMC takes control of HWP via TPMI:

\\\
Read PCS Index 53, Param 0x0 — OOB_HWP_CAPABILITIES
  Extract Highest/Guaranteed/Lowest performance levels
Optionally: Set IB_WRITE_BLOCK = 1 — lock out OS writes
Write PCS Index 53, Param 0x1 — OOB_HWP_REQUEST:
  MIN_PERF = policy_min (≥ Pn)
  MAX_PERF = policy_max (≤ P0n)
  EPP = platform_policy (0=perf, 255=efficiency)
\\\

### Stage 3: Runtime Operation (APS)

**PCode (PUnit)** resolves global constraints:

\\\
// PCode slowloop:
Fceil = min(ICCP_license_cap, thermal_limit, power_limit)
WP4_min = max(Pn, GUARDRAIL_CLKI.MIN_RATIO)
\\\

**Acode (Core)** runs APS using OOB-sourced parameters:

\\\
// Acode slowloop - every hcpm_timer (~1 ms):
Read OOB_HWP_REQUEST from TPMI shadow (NOT OS MSR 0x774)
gain_term = ubps_gain[oob_epp] × avg_util
decay_term = ratio_decay[oob_epp] × current_ratio

if (gain_term > decay_term):
    target = ramp_up(current_ratio)
else:
    target = ramp_down(current_ratio)

// Clip to OOB bounds and PCode limits:
final = clamp(target, OOB_MIN_PERF, OOB_MAX_PERF)
final = clamp(final, WP4_min, Fceil)

// Issue GV:
Apply GV transition to final
\\\

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| OOB mode enabled at boot | MISC_PWR_MGMT[8]=1; HWP hidden from OS; TPMI HWP active |
| OS writes MSR 0x774 | Write is **ignored** by PCode; no effect on frequency |
| BMC writes TPMI HWP_REQUEST | New policy takes effect within ~1 ms; APS uses OOB EPP |
| BMC sets EPP = 0 | APS favors higher frequency; faster response to load |
| BMC sets EPP = 255 | APS favors lower frequency; slower ramp-up |
| Turbo disabled | APS clamps MAX_PERF to P1 regardless of OOB request |
| IB_WRITE_BLOCK set | Additional protection — OS in-band writes blocked at TPMI layer |
| Thermal throttle active | APS respects thermal limit regardless of OOB request |

---

## Section 6: Corner Cases & Error Handling

- **Mode transition**: OOB ↔ Native mode change requires system reset; verify no mid-boot switch.
- **OS HWP enumeration**: Verify CPUID.06H:EAX[7] = 0 in OOB mode; OS should not attempt HWP access.
- **TPMI vs PECI**: On NWP, PECI HWP is removed — verify TPMI is the only working OOB path.
- **IB_WRITE_BLOCK**: Verify OS MSR writes fail gracefully when IB_WRITE_BLOCK is set.
- **OOB + Turbo Disable**: Verify HWP max capped at P1 when both OOB mode and TURBO_DISABLE are active.
- **BMC not present**: Verify default OOB HWP_REQUEST provides reasonable behavior if BMC never writes.

---

## Section 7: Security / Safety / Policy

- OOB mode provides **platform-level control** independent of OS — useful for bare-metal deployments.
- **IB_WRITE_BLOCK** prevents OS from overriding BMC policy — defense-in-depth.
- TPMI access requires BMC-level privilege — not accessible to OS or user-space.
- No OS-visible indication that HWP is being controlled by BMC (by design).

---

## Section 8: References

- [Pstate-HWP Feature KB -- pstate_hwp.md](../../../pm_features/pstate_stack/pstate_hwp.md)
- [Core P-State HAS -- HWP OOB](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html)
- [NWP PM MAS -- TPMI HWP](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [OOBMSM HAS -- PCS Index 53](https://docs.intel.com/documents/pm_doc/src/OOBMSM/OOBMSM_HAS.html)
- [Intel SDM -- MISC_PWR_MGMT MSR](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [Parent TCD HSD 22022421006](https://hsdes.intel.com/appstore/article-one/#/22022421006)

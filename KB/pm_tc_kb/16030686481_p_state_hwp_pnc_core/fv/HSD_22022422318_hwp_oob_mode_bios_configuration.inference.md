# Deep Analysis: HWP OOB Mode BIOS Configuration

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422318 |
| **Title** | HWP OOB Mode Bios configuration |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP Out-of-Band (OOB) Mode BIOS knob verification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies HWP BIOS knobs in **OOB (Out-of-Band) Mode**, where EPP is provided via PECI rather than the OS. OOB mode uses:
- `ProcessorHWPMEnable = 0x2` (OOB mode vs 0x1 for native mode)
- `ProcessorHWPMInterrupt = 0x0` (OOB mode typically disables interrupt)
- `ProcessorAPSrocketing = 0x0` (disabled in OOB)

The test procedure is similar to TC 22022422301 (Native Mode BIOS config) but verifies the OOB-specific knob combination. Uses same `Flexcon` tool with `DMRSV.ini` → `NWPSV.ini`.

**Key Justification:**
- HWP OOB mode applicable on NWP (PECI-based EPP for BMC control)
- `DMR_PO` tag: bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### OOB vs Native Mode Knobs

| BIOS Knob | Native Mode | OOB Mode |
|-----------|-------------|----------|
| `ProcessorHWPMEnable` | 0x1 | **0x2** |
| `ProcessorHWPMInterrupt` | 0x1 | **0x0** |
| `ProcessorAPSrocketing` | 0x1 | **0x0** |

### OOB Mode Characteristics
- EPP source: PECI (BMC/external management) instead of OS `IA32_HWP_REQUEST`
- OS `IA32_HWP_REQUEST` writes may be ignored in OOB mode
- BMC/management software controls frequency bias

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set OOB BIOS knobs; boot NWP | `ProcessorHWPMEnable = 0x2`, others = 0x0 |
| 2 | Run Flexcon: `python flexcon.py -i NWPSV.ini --onlyspecifiedmodules -m flexconPM` | NWP config |
| 3 | Verify no hangs with OOB knob combination | Same verification |
| 4 | Verify PECI EPP delivery mechanism active | BMC sends EPP via PECI interface |
| 5 | Boot with Native Mode knobs; run Flexcon again | Verify both modes work |

### NWP Pass Criteria
- OOB mode BIOS knobs accepted without hang
- `ProcessorHWPMEnable = 0x2` properly sets OOB mode in PCode
- PECI EPP channel active in OOB mode
- Flexcon PM module passes in OOB mode configuration

---

## Section F: Recommendation

**Recommendation: ADOPT — `DMRSV.ini` → `NWPSV.ini`; OOB mode BIOS knobs same on NWP**

Required adaptations:
1. Replace `DMRSV.ini` with `NWPSV.ini` in Flexcon command
2. Verify PECI infrastructure active on NWP platform (BMC with PECI access)
3. Verify `ProcessorHWPMEnable = 0x2` encoding is same for NWP BIOS

**Priority**: High — `DMR_PO`; HWP OOB mode is used in server management/BMC-controlled deployments

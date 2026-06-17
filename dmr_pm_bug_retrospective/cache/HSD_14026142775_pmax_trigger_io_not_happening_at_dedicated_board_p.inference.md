# HSD 14026142775: Pmax Trigger IO not happening at dedicated board pin

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026142775](https://hsdes.intel.com/appstore/article-one/#/14026142775) |
| **Status** | root_caused.awaiting_fix |
| **Priority** | 2-high |
| **Owner** | jgbeltra |
| **Component** | hw.power |
| **Defect Die** | ioe |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Reset/Boot | 75% |
| **Sub-Feature** | Boot | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

﻿
Summary:

========

For PMAX feature, we have a dedicated pin out on DMR board, this will notify clients about PMAX is asserting. The signal is called PMAX_TRIGGER_IO, and we have two of them, one for IMH0 and one for IMH1.

We ensure that PMAX TRIGGER is happening on PMAX IP, showed in the scope and also with register read in PMAX_LOG, but 

this is not happening on System

. The is a HSD already from RTL (
14025961369 - DMR iMH2 - Wrong Pmax Trigger Connection between Punit and GPIO
), but w

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
﻿
Summary:

========

For PMAX feature, we have a dedicated pin out on DMR board, this will notify clients about PMAX is asserting. The signal is called PMAX_TRIGGER_IO, and we have two of them, one for IMH0 and one for IMH1.

We ensure that PMAX TRIGGER is happening on PMAX IP, showed in the scope and also with register read in PMAX_LOG, but 

this is not happening on System

. The is a HSD already from RTL (
14025961369 - DMR iMH2 - Wrong Pmax Trigger Connection between Punit and GPIO
), but we need to follow up on post-si validation side.

Impact:

========

This is for client observability.

Details:

========

REPLACE  with failure and triage details.

==> System configuration ...

BKC DMR PO.

BIOS:OKSDCRB1_86B_2025.40.2.02_2798.D04_6000096E_0.616.0_1P0_NonIPClean_Trace_DebugSigned_40580295_202510152035.bin

If you have the possibility to connect a VP to scope will be great. PMAX_TRIGGER_IO is a must.

JT1C2 is for IMH0 VP0.

J2B1.1 - J2B1.2 (probe with socked) pin 1 and 2. 

==> Reproducibility and Time To Failure ...

Boot to BIOS window or OS.

1 - Import class that will be used.

from diamondrapids.pdi_dev_tools.applications.blocks_handler.CBlocksHandler import blocks_handler

2 - Route PMAXTRIGGER SIGNAL to Viewpins and HARD_THROTTLE.

blocks_handler.signals.vs_viewpins['PMAX_Channel0_vp_PmaxTrigXnnnH_dig0'].SignalSet({'Controller':&quot;PMAX_MT&quot;})

3 - Read PMAX_EN field to ensure feature is enabled. Should be 1.

sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_en.show()

4 - If feature is disable we just enable it.

sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_en.write(1)

5 - Reset the code to make the trigger, and reset the counters.

sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes.write(0x00)

sv.socket0.imh0.pmax.pmax0.pmax_debug_1.tst_mon_clr.write(1)

6 - Read the counter of MT0 PMAX and PMAX_log to ensure nothing happens until now. We will monitor 
mt0_cbb_trig_count
 and 
pmax_log

sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_tr

### Comments (latest)
++++14614755026 jhernan2
[CloneScript] PreSighting 14026121273 cloned to Sighting 14026142775

++++14614756627 vwang 
This one should be a PM sighting.  @Wang, Vidar - > can you take a look at what kind of tickets these are (pre-sightings?) and work on getting Sightings and root-causing and cloning/  I’m driving a meeting but can look later if you cannot.   Thanks!! Matthew From: Faber, Bob <bob.faber@intel.com> Sent: Tuesday, October 28, 2025 1:19 PM To: Haider, Nazar Syed <nazar.syed.haider@intel.com>; Muljono, Harry <harry.muljono@intel.com>; Gupta, Rajat <rajat.gupta@intel.com>; Goihman, Tal <tal.goihman@intel.com>; Kaur, Jasveen <jasveen.kaur@intel.com>; Vu, Lan D <lan.d.vu@intel.com>; Raghavan, Arvind <arvind.raghavan@intel.com>; Huerta Vazquez, Gabriel <gabriel.huerta.vazquez@intel.com>; Aguirre Diaz, Hector A <hector.a.aguirre.diaz@intel.com>; Munugoti, Prafulla Chandra <prafulla.chandra.munugoti@intel.com>; Rayess, Rachid E <rachid.e.rayess@intel.com>; Fausto, Matthew B <matthew.b.fausto@intel.com> Subject: RE: Need to close on the fixes for both of these HSD (bugs in DMR) for IMH2 and IMH1 (B-step)   @Fausto, Matthew B – Can you help getting these into SoC bugecos? https://hsdes.intel.com/resource/14026121273     

++++14614756672 vwang 
Hi Nazar,   https://hsdes.intel.com/resource/14026121273  We got the approval for fixing the bug on iMH2. We need to go to DCCB for iMH1 next week.   Thanks, Lan The is a HSD already from RTL (14025961369 - DMR iMH2 - Wrong Pmax Trigger Connection between Punit and GPIO),


++++14614756707 vwang 
.


++++14614759151 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14026142775] of [component=hw.power] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [bug] to [server.bugeco.id=14026151147] of [component=soc.top] in [release=dmrhub-a0]

++++14614759185 jhernan2
 @Beltran Becerra, Gilberto this HSD is under vt.pm , we (S2T_Perf) will not be tracking..Please follow up with the appropriate Sysdebug group

### Tags
SysDebugCloned,SysDebugDccbDone,SysDebugDccbDriver, PSF=Y

### Conclusion
hw.bug

### Component
hw.power

## Root Cause Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Fix Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Source Code References

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Root Cause

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Fix

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Feature Mapping

- **Primary Feature**: Reset/Boot
- **Sub-Feature**: Boot
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_en.show`
- `sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_en.write`
- `sv.socket0.imh0.pmax.pmax0.pmax_control.pmax_dac0_hvm_codes.write`
- `sv.socket0.imh0.pmax.pmax0.pmax_debug_1.tst_mon_clr.write`
- `sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count.show`

## Timeline

- **Submitted**: 2025-10-28 21:57:11
- **Root Caused**: 2025-10-29 22:02:27
- **Days Open**: 205

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

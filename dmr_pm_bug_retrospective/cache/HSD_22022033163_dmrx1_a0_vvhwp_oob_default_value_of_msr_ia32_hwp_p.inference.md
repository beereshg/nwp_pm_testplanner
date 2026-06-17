# HSD 22022033163: [DMR][X1 A0 VV][HWP OOB] Default value of MSR IA32_HWP_PECI_REQUEST is not zero after setting IA32_PM_ENABLE.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22022033163](https://hsdes.intel.com/appstore/article-one/#/22022033163) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | egomezgo |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Platform PM Interface | 80% |
| **Sub-Feature** | PECI | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

After boot, the default value of MSR 0x775 is not 0 and mismatches from OPC_HWP_CONTROLS in TPMI.

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww12.4]
* Double checking loading the correct patch for the increased verbosity and information - not seeing it.
* Val wondering how to get a &quot;smaller/appropriate&quot; trace that isn't 6GB in size.
    ==> Is there a particular reset phase to capture versus all of reset?
* Previous pTracker review, doesn't look like pCode writes to that register.
   ==> CBB pCode updates only when it gets an HPM from Primecode
* In Simics should be a way to trigger/monitor for the register right
   ==> We have an entire PSS team that should know all these answers --> use them  (Jeff Scanlon)
   ==> Is it a SB write we want to moinitor to find &quot;when/where/who&quot; is generating that write?
   ==> Can we monitor that RTL signal itself (without an emulation model compilation) ?
   ==> Run something in parallel that is 'looking' for the value like a debug tool/etc. so we get a timeframe?

[26ww12.3]

Emiliano provided ptracker from SIMICS, pending on pCode to debug.

Emiliano will work on collecting a higher log level to see if we can see the HPM messages, at least on the SMICS side. Along with sideband transactions to that register like IO reg trace.

[26ww11.3]

Emiliano provided ptracker from SIMICS, pending on Anatoli to debug.

[26ww10.3]

Emiliano is testing the same post-si test patch on simics, looking forward for more debug capabilities for pcode. ETA EOW. 

[26ww10.1]

Vlad

 is 
on the reserve duty.

[26ww09.3]

Anatoli said 
Barkanass, Vladislav

 is working on this.

[26ww08.3]

Anatoli will talk with VaX about this one.

[26ww07.3]

Anatoli will get VaX, Elad to support this ticket as well.

[26ww06.1]

Alex and Abhinand discussed whether there were any other sightings related to invalid default values from Pcode, and James recalled a previous issue with the Max allowed ratio, but no new related issues were identified; the team will continue to investigate the source of the non-zero default value.

### Description
After boot, the default value of MSR 0x775 is not 0 and mismatches from OPC_HWP_CONTROLS in TPMI.

### Comments (latest)
++++22611729748 mbfausto
Hector, what you have filed is a symptom.  What should be the default value and who programs it?  Is it writable?  you have .show() , what about when using RdMSR or TPMI?  When you change/program HWP does it update the value?  What are you default-related BIOS knobs and configurations that feed into this? There is still triage to be done to even point at pCode or something, please take a look at the pre-sighting contents you have here and provide the analysis of what/when it should change, is it stuck or just default value, do other settings work/apply, etc.
++++14615017751 egomezgo
The default value of MSR 0x775 should indeed be 0, and expectation is that pCode updates this value. The non-zero value observed after boot (0x8000FF00) indicates that something is programming this MSR before the OS takes control, before any out-of-band (OOB) override. After using OOB HWP requests, the MSR returns to the expected value, confirming that it is not stuck but rather being set by firmware at boot
++++22611739486 mbfausto
When you break at various points in reset / BIOS / OS Boot and look at the register via pythonSV, when does it change value to the incorrect one?  Or is the HW reset values 1 and it is reset FW that should clear this out?
++++14615072203 egomezgo
Modifying the title since the behavior is observed not after the boot, is after enabling HWP.

++++14615072219 egomezgo 
After enabling IA32_PM_ENABLE default value is not zero: Need feedback from Pcode team. Update: Notice that the wrong behavior is just at the initialization, after enabling HWP. Then when OPC_HWP_CONTROLS = 0 (releasing the request), the MSR contains correct info.


++++14615083518 egomezgo
Talked with Vlad and he will provide a debug patch.

++++14615088500 egomezgo
I test Vlad's patch, but seems that the wrong behavior is still observed:

++++14615088539 egomezgo
I got a dump of the registers from pcode.vars: https://hsdes.intel.com/resource/14027070261 
++++22611784792 mbfausto
Team - no updates in almost 2 weeks.  What is the current status of the debug/sighting?  With the patch results and pcode.vars, what were the results of the analysis form 2 weeks ago with the pCode team?
++++14615134809 vwang 
I was told  Vladislav doesn't have bandwidth on DMR right now. busy on PTL.  But Anatoli will try to ask him.


++++14615146758 egomezgo
Vlad provided another debug patch and suggest trying in Simics since the wrong behavior is still observed in Post Si.  I haven't used Simics for a while so I'm figuring out with Pooja Patel how to launch a session with the recent versions.
++++1363598288 aodler
 @Gomez Guerrero, Emiliano I cannot understand whether Vlad's patch still didn't work. Can you detail on that?
++++14615154456 egomezgo
Vlad has provided 2 patches but neither have worked in Post Si. Right now he wants me to try it on Simics in order to get a Pcode trace and clarify why is not working, as far as I know.  @Odler, Anatoli 
++++1363598666 aodler
 @Go

### Tags
FV_PM

### Conclusion
not_a_bug

### Component
fw.pcode

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: PECI
- **Component Path**: fw.pcode

## Firmware Touchpoints

### PCODE
- `pCode update`

## Key Registers

- `MSR 0x775`

## Timeline

- **Submitted**: 2026-01-28 06:37:34
- **Closed**: 2026-03-27 06:44:46
- **Days Open**: 58

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

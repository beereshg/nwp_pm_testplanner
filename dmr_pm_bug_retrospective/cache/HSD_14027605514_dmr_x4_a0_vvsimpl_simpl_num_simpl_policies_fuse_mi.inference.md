# HSD 14027605514: [DMR X4 A0 VV][SIMPL] SIMPL NUM_SIMPL_POLICIES fuse missing on IMH

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027605514](https://hsdes.intel.com/appstore/article-one/#/14027605514) |
| **Status** | root_caused.validating |
| **Priority** | 3-medium |
| **Owner** | pcanetel |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Power/RAPL | 60% |
| **Sub-Feature** | VR | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

From SIMPL HAS, it states that this IMH TPMI register, that
publishes the number of policies must do this check: 

    
Check: 0 <=
SIMPL_MIN_POLICY_OVRD <= SIMPL_MAX_POLICY_OVRD < fuse: NUM_SIMPL_POLICIES

 

But
 
fuse
NUM_SIMPL_POLICIES doesn’t exist on IMH
.

From latest 
SIMPL
HAS
:

v\:* {behavior:url(#default#VML);}
o\:* {behavior:url(#default#VML);}
w\:* {behavior:url(#default#VML);}
.shape {behavior:url(#default#VML);}

 

  
Normal

  
0

  

  

  

  

  
false

  
false

  
false

 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww15.4]

Issue: the absence of a required fuse NUM_SIMPL_POLICIES in the Primecode implementation, the current workaround of hard-coding values, and the need for Primecode and Architecture teams to align on a long-term solution and update the specification accordingly.

Primecode currently uses a hard-coded value (set to four) instead of reading from fuse, which is not aligned with the specification. Nilanjan clarified that while this is acceptable as a temporary measure for ES1/ES2, a real fuse is required for long-term correctness.

The specification explicitly requires a fuse, but it was not implemented, leading to the current bug. The group agreed that there is a missing fuse, and the workaround is to hard-code the value until a decision is made.

Arch and Primecode need to formally decide whether to implement the fuse or continue with the hard-coded value, update the spec and bug documentation, and ensure all stakeholders are aligned before closing the issue.

AR: Vidar will create a channel for Alex, Nilanjan, and Sagar to finalize the decision. Any changes, including spec updates or bug closure, will be documented once consensus is reached.

### Description
From SIMPL HAS, it states that this IMH TPMI register, that
publishes the number of policies must do this check: 

    
Check: 0 <=
SIMPL_MIN_POLICY_OVRD <= SIMPL_MAX_POLICY_OVRD < fuse: NUM_SIMPL_POLICIES

 

But
 
fuse
NUM_SIMPL_POLICIES doesn’t exist on IMH
.

From latest 
SIMPL
HAS
:

v\:* {behavior:url(#default#VML);}
o\:* {behavior:url(#default#VML);}
w\:* {behavior:url(#default#VML);}
.shape {behavior:url(#default#VML);}

 

  
Normal

  
0

  

  

  

  

  
false

  
false

  
false

  

  
EN-US

  
X-NONE

  
X-NONE

  

   

   

   

   

   

   

   

   

   

  

  
MicrosoftInternetExplorer4

  

   

   

   

   

   

   

   

   

   

   

   

  

 

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  

  


### Comments (latest)
++++22611836007 pcanetel
I do see a symbol in Primecode called 'FUSES_SIMPL_POLICY_COUNT' but as it is right now, it would report '4' even when we have the fix to have only 1 policy enabled.
++++14615312715 vwang 
While Arch, Fuse and Primcode teams are discussing the long term solution offline.  We need to correct hard-coded NUM_SIMPL_POLICIES to value 1 as a temporary measure for ES1/ES2.

++++14615312726 vwang
[CloneScript] Sighting [sighting_central.sighting.id=14027605514] of [component=fw.primecode] in [release=pkg.dmr-a0] has been cloned to a [bug] to [server.bugeco.id=14027621260] of [component=soc.PrimeCode 2.0#] in [release=dmrhub-a0]
++++22611869878 mbfausto
[SysDebug] The FW ticket (id=14027621260) cloned from this sighting has been fixed and released in ingredient version "DMR_AP1_A0_600009A0" on [SysDebug] Sighting tag appended with "FIX_PATCH_DMR_AP1_A0_600009A0" [SysDebug] [SysDebug] The Sighting owner (pcanetel) may be enabled to validate the fix is working in the released collateral.

++++22611871147 mbfausto
[SysDebug Tag Script] IFWI version "DMR_AP1_2026.17.3.02" has been released that contains the component release "FIX_PATCH_DMR_AP1_A0_600009A0" [SysDebug Tag Script] Sighting tag appended with "FIX_IFWI_DMR_AP1_2026.17.3.02"
++++14615395969 pcanetel
What is the definition of the fix? So far I can't find a place where the number of actual valid policies is exposed from IMH side.

++++14615396655 agraback
NUM_SIMPL_POLICIES fuse added to primecode. It's present in the primecode fuse xml now and the logic is aligned to the HAS. To accommodate existing parts with current fusing, if that fuse value is 0x0 it will default to max polices (0x4) 
++++22611889317 pcanetel
As the HSD is for a missing fuse, we still need Arch input to define if we will have the real fuse or not. As far as I understand now we have the 'placeholder' on Primecode to receive a value from a fuse and then determine the max simpl policies, but we still miss a FCCB HSD to map that fuse.  If we won't have the fuse, then the HAS needs to be updated.  @Palit, Nilanjan 
++++14615403896 vwang
From Archana: There is no Primecode “NUM_SIMPL_POLICIES” fuse today. Questions : Although DMR is architecturally capable of having more than 1 policy, is the DMR product ever going to have more than 1? ( Initial input was it will always be 1, and so Primecode fuse was Not needed) If answer to above is “Yes”, then PM arch needs to:   @Palit, Nilanjan  work with Primecode team to get the fuse added. new SKU attribute needs to be added (PM arch to work with Bin split team) FCCB HSD needs to be filed 
++++22611906093 mbfausto
[SysDebug Tag Script] BKC version "OKS_DMR_AP1_2026WW20" has been released that contains the component release "FIX_IFWI_DMR_AP1_2026.18.3.02" [SysDebug Tag Script] Sighting tag appended with "FIX_BKC_OKS_DMR_AP1_2026WW20"

### Tags
FV_PM,SysDebugCloned,SysDebugDccbBypass,FIX_PATCH_DMR_AP1_A0_600009A0,FIX_IFWI_DMR_AP1_2026.18.3.02,BKC#OKS_DMR_AP_X1_2026WW20,FIX_BKC_OKS_DMR_AP1_2026WW20

### Conclusion
fw.bug

### Component
fw.primecode

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

- **Primary Feature**: Power/RAPL
- **Sub-Feature**: VR
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI register`

## Timeline

- **Submitted**: 2026-04-09 00:06:06
- **Root Caused**: 2026-04-10 10:33:34
- **Days Open**: 42

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

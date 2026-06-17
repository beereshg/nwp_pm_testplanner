# HSD 15019298749: [OKS][DMR-AP][RAS] MLC bitfix filter does not get restored on C6 exit

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15019298749](https://hsdes.intel.com/appstore/article-one/#/15019298749) |
| **Status** | root_caused.pursuing_fix |
| **Priority** | 3-medium |
| **Owner** | cdflores |
| **Component** | hw.big_core |
| **Defect Die** | compute |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Core C-States | 75% |
| **Sub-Feature** | C6 | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

When the CPU enters C6 the MLC BFF contents should get stored and then restored on C6 exit.

We are seeing BFF issues when the CPU enters and exits C6. The filter will behave as if it was empty after C6 exit even if some entries were already occupied before entering C6.

BIOS 32.D14 with kernel 6.18

Test:

Disable idle states 1,2,3,4,5

Filter threshold = 3

Inject errors until we reach 2 entries used

Verify filter registers

First run (slice 0 and 1 were used):

In [113]: sv.socket0.cbb0.comp

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿

﻿[26ww18.3]

This is a 

RAS / low-power-state retention issue

 where 

MLC Bitfix Filter context is not preserved correctly across C6 exit

. 

When a core enters 

C6

, the 

BFF contents should be saved and restored

 when the core exits that low-power state. But 

the 

MLC Bitfix Filter (BFF)

 state is 

not properly restored after exiting C6/C6SP

.

### Description
When the CPU enters C6 the MLC BFF contents should get stored and then restored on C6 exit.

We are seeing BFF issues when the CPU enters and exits C6. The filter will behave as if it was empty after C6 exit even if some entries were already occupied before entering C6.

BIOS 32.D14 with kernel 6.18

Test:

Disable idle states 1,2,3,4,5

Filter threshold = 3

Inject errors until we reach 2 entries used

Verify filter registers

First run (slice 0 and 1 were used):

In [113]: sv.socket0.cbb0.compute0.module5.showsearch(&quot;tag_bit&quot;)

ml2_cr_tag_bitfix_entry_cr0 = 0x
9910c2e3

ml2_cr_tag_bitfix_entry_cr1 = 0x
d901
0000

ml2_cr_tag_bitfix_entry_cr2 = 0x0

ml2_cr_tag_bitfix_entry_cr3 = 0x0

Second run (only slice 1 was used):

In [123]: sv.socket0.cbb0.compute0.module5.showsearch(&quot;tag_bit&quot;)

ml2_cr_tag_bitfix_entry_cr0 = 0xd901
c2e0

ml2_cr_tag_bitfix_entry_cr1 = 0xd901
ad31

ml2_cr_tag_bitfix_entry_cr2 = 0xd9010000

ml2_cr_tag_bitfix_entry_cr3 = 0xd9010000

Verify flags: only green

Enable idle state 5 (C6SP)

Allow cores to enter C6

Disable idle state 5 (C6SP)

Verify filter registers. All values from the same slice seem to have the same value.

First run:

In [114]: sv.socket0.cbb0.compute0.module5.showsearch(&quot;tag_bit&quot;)

ml2_cr_tag_bitfix_entry_cr0 = 0xd9010000

ml2_cr_tag_bitfix_entry_cr1 = 0xd9010000

ml2_cr_tag_bitfix_entry_cr2 = 0xd9010000

ml2_cr_tag_bitfix_entry_cr3 = 0xd9010000

Second run:

In [124]: sv.socket0.cbb0.compute0.module5.showsearch(&quot;tag_bit&quot;)

ml2_cr_tag_bitfix_entry_cr0 = 0xd901ad31

ml2_cr_tag_bitfix_entry_cr1 = 0xd901ad31

ml2_cr_tag_bitfix_entry_cr2 = 0xd901ad31

ml2_cr_tag_bitfix_entry_cr3 = 0xd901ad31

Inject 1 error. This error uses the first entry as if the filter was empty.

First run:

In [120]: sv.socket0.cbb0.compute0.module5.showsearch(&quot;tag_bit&quot;)

ml2_cr_tag_bitfix_entry_cr0 = 0xd901
c2e0

ml2_cr_tag_bitfix_entry_cr1 = 0xd9010000

ml2_cr_tag_bitfix_entry_cr2 = 0xd9010000

ml2_cr_tag_bitf

### Comments (latest)
++++1566932980 feitingw
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 14027327121.

++++1566932977 mbfausto
Team - are these MLC registers saved/restored (and lost?) on a CC6 entry/exit?&nbsp; Is this fw.ucode.big_core or hw.big_core that is responsible for the save/restore (update component please).

++++1566932979 vwang
This sighting doesn't reach the level of sighting yet. Need to triage at the pre-sighting stage.

++++1566932978 rubenher
<p>Hi &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Wang, Vidar</span>&nbsp;</p><p><br /></p><p>This has been reproduced several times on Two different systems, &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Flores Pinedo, C Daniel</span>&nbsp;has uploaded the evidence from each system and is attached to the sighting.</p><p>What's missing from the details shared? What do you need for this to be treated as a sighting?</p>

++++1566932981 cdflores
<p>&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Fausto, Matthew B</span>&nbsp;yes, MLC BFF registers should be stored on C6 entry and restored on C6 exit. It seems like the info is lost.</p><p><br /></p><p>One possible reason for this behavior is due to this known issue:&nbsp;<a href="https://hsdes.intel.com/appstore/article-one/#/16027112702" target="_blank" style="font-family: Roboto, Arial, sans-serif; background-color: rgb(255, 255, 255); font-weight: 400;" tabindex="-1">16027112702 - PNC: Bitfix Read from core0 CR Bus getting junk values</a></p><p>When the filter data is read through Core 0 it fails. Data from the filter can only be read through Core 1.</p><p>We already had issues with this for our validation (<a href="https://hsdes.intel.com/appstore/article-one/#/article/15018370277" target="_blank" style="font-family: Roboto, Arial, sans-serif; background-color: rgb(255, 255, 255); font-weight: 400;" tabindex="-1">15018370277 - [X1 A0 PO] Tag Bitfix Filter (BFF) in MLC logs the same cache address in all entries</a>) and got a workaround that forces IPC to read through Core 1, but this only works for debug tools. Our theory is that internally when the data is sent to C6SRAM on C6 entry, this read might be done through Core 0, hence it doesn't store the correct values. So, on C6 exit it restores junk values.</p><p>With this behavior MLC bitfix filter becomes useless if the core often goes to C6 state. It will often get (kind of) reset and there might never be a yellow flag to indicate cache is failing.</p><!--StartFragment--><!--EndFragment-->

++++1566932982 vwang
&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Hernandez Cortes, Ruben S</span>&nbsp; we may need some insights from core experts.

++++1566932984 jtgilmer
<p>Hi,<br />I see the&nbsp;ML2_CR_TAG_BITFIX_ENTRY_CRX and all other MLC Bitfix CRs (like HEAD_PTR) should be saved/restored across C6.&nbsp;</p><p>(only one that is not is

### Tags
SysDebugDccbDone

### Conclusion
hw.bug

### Component
hw.big_core

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: C6
- **Component Path**: hw.big_core

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.compute0.module5.showsearch`

## Timeline

- **Submitted**: 2026-04-22 06:50:26
- **Root Caused**: 2026-05-12 18:31:27
- **Days Open**: 29

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

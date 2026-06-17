# HSD 14027120450: [DMR][PM] PLR register values are not being updated in PythonSV as expected

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027120450](https://hsdes.intel.com/appstore/article-one/#/14027120450) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | sdeshpan |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Platform PM Interface | 80% |
| **Sub-Feature** | PECI | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Some of the Perf Limiting Reasons Registers are not being updated as expected.

Specifically, we are looking at PLR_DIE_LEVEL (as expected) and 
PLR_MAILBOX_DATA 
(always shows zeros). 

The test scenario is running povray_r on all cores on 224c X4 part (SC00902270H8006). 

All core turbo ratio is 2.3GHz, below is a screenshot of htop showing that the cores are being throttled to 1.7GHz

Average power observed using turbostat is around 503W which is above TDP of 500W clearly pointing to RAPL thr

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[25ww10.3]

From Alex: Sahil should be able to do it just now on pythonsv due to current comming fixes on primecode. Next step, sysdebug to talk to Sahil, seems like we can demote this to pre-sighting or reject. Rejecting in 24hrs

### Description
Some of the Perf Limiting Reasons Registers are not being updated as expected.

Specifically, we are looking at PLR_DIE_LEVEL (as expected) and 
PLR_MAILBOX_DATA 
(always shows zeros). 

The test scenario is running povray_r on all cores on 224c X4 part (SC00902270H8006). 

All core turbo ratio is 2.3GHz, below is a screenshot of htop showing that the cores are being throttled to 1.7GHz

Average power observed using turbostat is around 503W which is above TDP of 500W clearly pointing to RAPL throttling the core frequencies which can be confirmed by reading PLR_DIE_LEVEL (register was reset before running this test). 

We need more fine grained status from the PLR_MAILBOX_DATA register, however, it always reads as zero in pythonsv as well as using pepc

### Comments (latest)
++++14615103362 agraback
TPMI line PLR_MAILBOX_DATA has been removed from IMH for DMR

++++14615103363 agraback
Do these pcudata variables for the RAPL PERF STATUS HPM command ever show a non-zero value?<br /><p style="margin:0in;font-family:Calibri;font-size:11.0pt">sv.socket0.imh0.pcudata.rapl_perf_limit_lo.show()</p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">sv.socket0.imh0.pcudata.rapl_perf_limit_hi.show()</p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">&nbsp;</p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">sv.socket0.imh1.pcudata.rapl_perf_limit_lo.show()</p>

<p style="margin:0in;font-family:Calibri;font-size:11.0pt">sv.socket0.imh1.pcudata.rapl_perf_limit_hi.show()</p><p style="margin:0in;font-family:Calibri;font-size:11.0pt"><br /></p><p style="margin: 0in;">They may be getting cleared as part of the HPM cmd flow...</p>

++++14615103365 vwang
[CloneScript] PreSighting 22022108348 cloned to Sighting 14027120450
++++22611778448 sdeshpan
The listed pcudata variables for the RAPL PERF STATUS HPM command always show zeroes (at idle, just after launching a workload, while RAPL is actively throttling).  sv.socket0.imh0.pcudata.rapl_perf_limit_lo.show() sv.socket0.imh0.pcudata.rapl_perf_limit_hi.show()   sv.socket0.imh1.pcudata.rapl_perf_limit_lo.show() sv.socket0.imh1.pcudata.rapl_perf_limit_hi.show() Is there any other way to get the fine grained status for why is the frequency being limited?

++++22611778463 agraback
CB Pcode is populating the fine grained reasons in the upper 32-bits of plr_mailbox_data tpmi registers. Looks like you have to issue a Read command using the PLR Mailbox Interface reg to get the data in the plr_mailbox_data reg https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html#performance-limit-reasons-mailbox

++++22611784858 mbfausto
What were the results of the mailbox data? And to confirm, *should* we have 'more fine-grained information' in the manner being read (this is a potential bug) or more an enhancement/nice-to-have in the manner  (and AlexG is pointing out al alternative method) ?

++++22611791891 mbfausto
 @Deshpande, Sahil  / Team ?  No updates, what are the results?  Sahil we need owners (and their domain/team) to provide status updates in the comment and prompt execution.  Thanks!

++++22611792171 sdeshpan
Hi,  Apologies for the delayed response.  I have been involved in a lot of discussions on this offline.  Issuing a read command to the PLR Mailbox Interface register is populating the PLR Mailbox Data, but it is setting the bits even when the outputs are saturated and not just when the frequency is being limited by the corresponding factors. This has been observed in the debug of another issue: https://hsdes.intel.com/appstore/article-one/#/article/16029367861  @Grabacki, Alex mentioned that this has since been fixed and he has shared the corresponding IFWI. I am testing this and will share my observations on this sighting.  Thanks

### Conclusion
not_a_bug

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

- **Primary Feature**: Platform PM Interface
- **Sub-Feature**: PECI
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI line`
- `sv.socket0.imh0.pcudata.rapl_perf_limit_lo.show`
- `sv.socket0.imh0.pcudata.rapl_perf_limit_hi.show`
- `sv.socket0.imh1.pcudata.rapl_perf_limit_lo.show`
- `sv.socket0.imh1.pcudata.rapl_perf_limit_hi.show`

## Timeline

- **Submitted**: 2026-02-20 06:59:45
- **Closed**: 2026-03-04 22:22:32
- **Days Open**: 12

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

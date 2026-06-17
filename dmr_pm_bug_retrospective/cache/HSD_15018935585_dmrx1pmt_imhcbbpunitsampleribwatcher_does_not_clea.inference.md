# HSD 15018935585: [DMR][X1][PMT] Imh/CBBPunitSamplerIBWatcher does not clear the One-shot sample mode flag when the data is collected

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15018935585](https://hsdes.intel.com/appstore/article-one/#/15018935585) |
| **Status** | complete.wont_validate |
| **Priority** | 3-medium |
| **Owner** | yizheliu |
| **Component** | hw.punit |
| **Defect Die** | ioe |
| **Conclusion** | hw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 85% |
| **Feature** | Platform PM Interface | 60% |
| **Sub-Feature** | general | — |

**Reasoning**: conclusion='hw.bug' → HW

## Root Cause Summary

According to PMT spec, Telemetry Sampler Register Definition, 

For
 One-shot
, it is armed once, and 
hardware should clears the sample mode when the data is collected.
 If the sample mode is cleared before the data is collected the data collection may or may not be aborted.

But This HW mechanism was not correctly implemented in Anot happened on 
IMH and CBB pcode
 sampler watcher.

 
e.g. 
 and 

Other watcher hosted by iMH OOBMSM/iMH MSM Aggregators works as expected as  described in spec.



## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww06.1]

Vidar will clone this to DCCB and move forward.

[26ww04.3]

Need primecode support, will contact Alex for next steps.

### Description
According to PMT spec, Telemetry Sampler Register Definition, 

For
 One-shot
, it is armed once, and 
hardware should clears the sample mode when the data is collected.
 If the sample mode is cleared before the data is collected the data collection may or may not be aborted.

But This HW mechanism was not correctly implemented in Anot happened on 
IMH and CBB pcode
 sampler watcher.

 
e.g. 
 and 

Other watcher hosted by iMH OOBMSM/iMH MSM Aggregators works as expected as  described in spec.

LOG in 
 

[INFO] 2026-01-16 12:15:51,133 [kayak.domains.manageability.pmt.lib.tools.ib_tools: execute: 129]: Executing on SUT: '/usr/sbin/iotools mmio_write64 0x1010ffaeb128 0x80000002000186a0'

[INFO] 2026-01-16 12:15:51,133 [kayak.core.api.os_comm: execute: 132]: execute with cmd=/usr/sbin/iotools mmio_write64 0x1010ffaeb128 0x80000002000186a0, end_pattern=None, timeout=60, cwd=None, raise_on_error=False

[INFO] 2026-01-16 12:15:51,133 [kayak.core.internals.instruments.ssh_protocol.paramiko_ssh: execute: 252]: running cmd: /usr/sbin/iotools mmio_write64 0x1010ffaeb128 0x80000002000186a0

[INFO] 2026-01-16 12:15:51,847 [kayak.domains.manageability.pmt.lib.tools.ib_tools: execute: 134]: response for 'mmio_write64 0x1010ffaeb128 0x80000002000186a0': 

[INFO] 2026-01-16 12:15:51,847 [kayak.domains.manageability.pmt.lib.tools.ib_tools: execute: 126]: iotool_path:/usr/sbin/iotools

[INFO] 2026-01-16 12:15:51,847 [kayak.domains.manageability.pmt.lib.tools.ib_tools: execute: 129]: Executing on SUT: '/usr/sbin/iotools mmio_dump 0x1010ffaeb128 8'

[INFO] 2026-01-16 12:15:51,848 [kayak.core.api.os_comm: execute: 132]: execute with cmd=/usr/sbin/iotools mmio_dump 0x1010ffaeb128 8, end_pattern=None, timeout=60, cwd=None, raise_on_error=False

[INFO] 2026-01-16 12:15:51,848 [kayak.core.internals.instruments.ssh_protocol.paramiko_ssh: execute: 252]: running cmd: /usr/sbin/iotools mmio_dump 0x1010ffaeb128 8

[INFO] 2026-01-16 12:15:52,564 [kayak.domains.manageability.pmt.lib.tools.ib_tool

### Comments (latest)
++++1566794271 yizheliu
Hi  @DeHaemer, Eric J , could you kindly ask one of your DMR pcode team to review this issue?
++++22611706008 mbfausto
The description is indicating that the PUNIT HW in the CBB and IMH does not work.  Not sure why primecode and pcode are involved yet at this time?  Let's follow up with PM folks here. Routing to PM SysDebug as we're working on PUNIT and possible pCode/Primecode debug, all the experts are there!

++++22611710005 vwang 
 @Pal, Poulomi  is currently looking for some spec clarification from Primecode. It appears that the language of the spec has not changed since GNR/SPR, so we're curious about what was done on those SoCs.


++++14614997856 ppal 
Current discussion Summary (imH Punit): Latest PMT spec has renamed the Watcher Type value 0x0 from TRACER to STREAMER, but PUnit HW registers are named TRACER for this Watcher Type (IPPUNIT-506).  So we need to look at the architectural requirements for STREAMER and apply it to PUnit registers named TRACER. The requirement was the same back then for SPR CTF architecture as it is now for DMR PMT architecture, and that this bug has been around since SPR but never caught until now in DMR. Here is the direction iMH Punit would like to proceed toward: Ideally a PUnit HW change to make the IO register alias writable from PrimeCode FW side would make fixing this in firmware easier, but we’d like to rejected.future_product with PrimeCode FW W/A The firmware workaround is that If configured for one-shot, PrimeCode FW should perform the one-shot collection of data, clear the MODE bit by writing to the GPSB register, then clear the request_pending_bit by writing to the IO register alias. In future gen, these fields should change to RW/V so PrimeCode can clear the mode bit in the same write that clears the request_pending bit when necessary Currently getting feedback from PMT owners for: what is the impact to DMR if this is not fixed and not worked around? Since SPR and GNR both have the bug, are we able to PRQ DMR without fixing/workaround this?


++++14615010482 vwang
 @Grabacki, Alex  Could you check if we can port Primecode WA ?
++++22611729237 agraback
As discussed on a call with Poulomi and team, the proposed Primecode WA is totally doable. The official WA process would need to be followed: ->RTL bugeco HSD->DCCB disposition->WA spec->Primecode WA HSD

++++22611729851 mbfausto
we need some clarity please. If I read this correctly: IMH PUNIT HW bug  (hw.punit / hw.bug) ... we have the arch/spec/requirement but never coded it that way? If this is the case, file/clone the HW Bug, and indicate (probably with addText='') that there is an agreed upon Primecode WA already discussed for the DCCB decision. Is there any issue with CBB PUnit ?  (if so, separate sighting please if there's a CBB Punit HW issue too).
++++14615032390 vwang
[CloneScript] Sighting [sighting_central.sighting.id=15018935585] of [component=hw.punit] in [release=package.dmrap-ucc-x1-a0] has been cloned to a [b

### Tags
SysDebugCloned,SysDebugDccbDone

### Conclusion
hw.bug

### Component
hw.punit

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
- **Sub-Feature**: general
- **Component Path**: hw.punit

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-01-20 13:46:53
- **Root Caused**: 2026-02-02 23:07:10
- **Closed**: 2026-02-13 18:04:54
- **Days Open**: 24

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

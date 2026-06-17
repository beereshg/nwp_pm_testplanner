# HSD 14027538694: [X4] RC FIVR WorkPoint change Timeout with PC6 enabled

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027538694](https://hsdes.intel.com/appstore/article-one/#/14027538694) |
| **Status** | open.clone |
| **Priority** | 2-high |
| **Owner** | hmpicosm |
| **Component** | hw.d2d |
| **Defect Die** | ioe |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 75% |
| **Sub-Feature** | C6 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Hitting hang in SVOS idle with PC6 enabled. TTF is less than 5 minutes:

In [41]: server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)

============================================================================================================================================================================================================================================================================================================================================================

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww21.3]

Hector described ongoing struggles to capture signals from both dies (CBB and IMH) simultaneously for FSMs, citing problems with triggering and time scale alignment. The team is working with ITH tools support, migrating between T1 and T2, and implementing local fixes.

Hector explained that tracing with Visa can block PkgC6, complicating debugging efforts. The team is making progress and expects to achieve a good VISA capture soon.

﻿[26ww21.1]

Setting up ITH T2 to be able to
trace CBB/IMH signals at the same time, as ITH T1 is exhibiting time scale
issues. Setup IN progress.

﻿[26ww20.1]

Hector described collecting VISA traces for two scenarios, monitoring voltage change signals, and posting observations, with plans to follow up with Joe or Sarah from the UCI team for further analysis.

﻿[26ww19.3]

Hector reported that debug patches released by Trevor and Alex are being tested on systems that typically reproduce the issue quickly, with mixed results—one system ran for 10 hours without failure, while another still exhibited the issue after six hours.

The team is working with the UCIe design team to define new signals for VISA capture during failures, and Jimmy is focusing on collecting relevant VISA data to aid in root cause analysis.

Efforts are ongoing to reproduce the issue in BIOS parts, with the problem currently only observed in power-on units; the team is setting up more systems and reaching out to Robert Southwell for insights on potential UCI file or recipe changes.

Joseph mentioned that Elena is conducting experiments to reproduce the issue on SLD systems, and the team is keeping the ticket open until reproduction is confirmed or ruled out in BIOS parts.

﻿[26ww18.3]

Still struggling to take a good trace, have problems with the trigger (manual stop works fine). Working with debug tools team on the issue, some next steps defined. Joe is working on acceleration patch, ETA ww18.3 - ww18.4

﻿[26ww18.1]

Hector reported that several VISA tra

### Description
Hitting hang in SVOS idle with PC6 enabled. TTF is less than 5 minutes:

In [41]: server_ip_debug.punit.errors.show_mca_status(source=&quot;reg&quot;)

===============================================================================================================================================================================================================================================================================================================================================================================================================================================

|skt|die_id|inst|inst_name         |mscod|mcacod|error type|overflow|error_source|description                                                            |error_specific_info                                                                                                                                                                                                    |next_steps                                                  |

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|0  |1     |0   |socket0.imh1.punit|AGG  |1026  |Fatal     |        |RC          |Waiting for response from voltage resource adapter for workpoint change|{'error_code': 'WATCHDOG', 'error_domain': 'VF sequencer', 'source_port_id': 265, 'source_ip': 265, 'timed_out_resource': 0, 'resource_type': 'fivr', 'ip_type': 'RC', 'instance': 'socket0.imh1.resctrl.rc_cfcmem_ew'}|Check the FIVR RA attached to this RC to see why it is stuck|

====================================================================================================================

### Comments (latest)
++++14615275548 hmpicosm
<div><br /></div><div>FOUND VALID MCA</div><div>socket0.imh0.rasip.root_ras.rasip_regs_block.rasip_reg_msg_mem_rasip_error_handler_domain.reg_ierrloggingreg = 0x306c8</div><div>0x00000000 : secondierrsrcfromcbb (49:49) (rw/v/p) -- Set to '1 if the SecondIerrSrcID is from CBB</div><div>0x00000000 : secondierrsrcvalid (48:48) (rw/v/p) --&nbsp; set to 1 if the SecondIerrSrcID is valid</div><div>0x00000000 : secondierrsrcid (47:32) (rw/v/p) -- Logical Port ID of the end point with the second IERR</div><div>0x00000001 : firstierrsrcfromcbb (17:17) (rw/v/p) -- Set to '1 if the FirstIerrSrcID is from CBB</div><div>0x00000001 : firstierrsrcvalid (16:16) (rw/v/p) -- Set to '1 if the FirstIerrSrcID is valid</div><div>0x000006c8 : firstierrsrcid (15:00) (rw/v/p) -- Logical Port ID of the end point with the first IERR</div><div><br /></div><div>None</div><div><br /></div><div>socket0.imh0.rasip.root_ras.rasip_regs_block.rasip_reg_msg_mem_rasip_error_handler_domain.reg_cbb0_ierrloggingreg = 0x306e8000306e8</div><div>0x00000001 : secondierrsrcfromcore (49:49) (rw/v/p) -- Set to '1 if the SecondIerrSrcID is from a C2U</div><div>0x00000001 : secondierrsrcvalid (48:48) (rw/v/p) --&nbsp; set to 1 if the SecondIerrSrcID is valid</div><div>0x000006e8 : secondierrsrcid (47:32) (rw/v/p) -- Logical Port ID of the end point with the second IERR</div><div>0x00000001 : firstierrsrcfromcore (17:17) (rw/v/p) -- Set to '1 if the FirstIerrSrcID is from a C2U</div><div>0x00000001 : firstierrsrcvalid (16:16) (rw/v/p) -- Set to '1 if the FirstIerrSrcID is valid</div><div>0x000006e8 : firstierrsrcid (15:00) (rw/v/p) -- Logical Port ID of the end point with the first IERR</div><div><br /></div><div>None</div><div><br /></div><div>socket0.imh0.rasip.root_ras.rasip_regs_block.rasip_reg_msg_mem_rasip_error_handler_domain.reg_cbb1_ierrloggingreg = 0x306c8000306c8</div><div>0x00000001 : secondierrsrcfromcore (49:49) (rw/v/p) -- Set to '1 if the SecondIerrSrcID is from a C2U</div><div>0x00000001 : secondierrsrcvalid (48:48) (rw/v/p) --&nbsp; set to 1 if the SecondIerrSrcID is valid</div><div>0x000006c8 : secondierrsrcid (47:32) (rw/v/p) -- Logical Port ID of the end point with the second IERR</div><div>0x00000001 : firstierrsrcfromcore (17:17) (rw/v/p) -- Set to '1 if the FirstIerrSrcID is from a C2U</div><div>0x00000001 : firstierrsrcvalid (16:16) (rw/v/p) -- Set to '1 if the FirstIerrSrcID is valid</div><div>0x000006c8 : firstierrsrcid (15:00) (rw/v/p) -- Logical Port ID of the end point with the first IERR</div><div><br /></div><div>None</div><div><br /></div><div>socket0.imh1.rasip.root_ras.rasip_regs_block.rasip_reg_msg_mem_rasip_error_handler_domain.reg_ierrloggingreg = 0x10012000306c8</div><div>0x00000000 : secondierrsrcfromcbb (49:49) (rw/v/p) -- Set to '1 if the SecondIerrSrcID is from CBB</div><div>0x00000001 : secondierrsrcvalid (48:48) (rw/v/p) --&nbsp; set to 1 if the SecondIerrSrcID is valid</div><div>0x00000012 : secondierrsrcid (47:32) (rw/v/p) -

### Tags
FV_PM,ps2strend,concern

### Component
hw.d2d

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
- **Component Path**: hw.d2d

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.imh0.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.wp_seq_status.show`
- `sv.socket0.imh0.resctrl.rc_cfcmem_ew.showsearch`
- `sv.socket0.imh0.resctrl.rc_cfcmem_ew.resctrl_prvt_wp_regs.wp_seq_status.wp_active_p0_busy.description`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_status.mca_error_code`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.mc_status.mca_error_code.description`

## Timeline

- **Submitted**: 2026-03-31 00:03:34
- **Days Open**: 51

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

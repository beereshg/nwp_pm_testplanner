# HSD 14025883988: [DMR][X1 A0 PO] [RAPL] PLR bits not getting set

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025883988](https://hsdes.intel.com/appstore/article-one/#/14025883988) |
| **Status** | rejected.filed_by_mistake |
| **Priority** | 2-high |
| **Owner** | kumara5 |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Platform PM Interface | 52% |
| **Sub-Feature** | Mailbox | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

In [123]:
import pm.pmutils.pstatesDebug as pd

we can't
import cli due: No module named 'cli'

 

In [124]:
pd.debug.pl

plot_fuse_xmls()
plr_decode()     plr_mailbox()

In [124]:
pd.debug.plr_

plr_decode()  plr_mailbox()

In [124]:
pd.debug.plr_mailbox()

Out[124]:
0x0

 

In [125]:
pd.debug.plr_mailbox()

Out[125]:
0x0

 

In [126]:
pd.debug.plr_mailbox()

Out[126]:
0x0

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
In [123]:
import pm.pmutils.pstatesDebug as pd

we can't
import cli due: No module named 'cli'

 

In [124]:
pd.debug.pl

plot_fuse_xmls()
plr_decode()     plr_mailbox()

In [124]:
pd.debug.plr_

plr_decode()  plr_mailbox()

In [124]:
pd.debug.plr_mailbox()

Out[124]:
0x0

 

In [125]:
pd.debug.plr_mailbox()

Out[125]:
0x0

 

In [126]:
pd.debug.plr_mailbox()

Out[126]:
0x0

### Comments (latest)
++++14614603806 egomezgo
Also seeing the wrong behavior. The run_busy bit never gets cleared by Pcode.

++++14614603807 sasmith2
&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Sirotin, Yuri</span>&nbsp;- Can you help with this one? We are seeing issues in PLR of bits not getting set and run_busy never cleared from mailbox interface.

++++14614603809 sasmith2
<div>In the plr_mailbox_interface.run_busy bit case:<br /><br />I am able to manually set/clear&nbsp;sv.sockets.cbbs.base.tpmi.plr_mailbox_interface.run_busy</div><div><br />I see these tpmi_enable_fastpath_mask_X values:</div><div><br /></div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_0 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_1 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_2 = 0x4000000000000</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_3 = 0x2</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_4 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_5 = 0x200000000</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_6 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_7 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_8 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_9 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_10 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_11 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_12 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_13 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_14 = 0x0</div><div>sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_15 = 0x0<br /><br /><br />I tried setting the masks all to Fs at runtime but still do not see run_busy cleared.&nbsp; I also tried clearing run_busy and then setting it again but stays set.</div><div><br /></div><div>Attaching PCUDATA and PCODE pythonSV logs.</div>

++++14614603805 cadoming
<p style="margin: 0in; color: rgba(0, 0, 0, 0.87); font-family: Calibri; font-size: 11pt;">PLR for IMH0 and IMH1 is not being set, returning to BMC, and driver these behaviour, is the issue tracked on these HSD or have other HSD for PLR on IMH</p><p style="margin: 0in; color: rgba(0, 0, 0, 0.87); font-family: Calibri; font-size: 11pt;">&nbsp;</p><p style="margin: 0in;"><font color="rgba(0, 0, 0, 0.87)" face="Calibri"><span style="font-size: 14.6667px;">socket0.imh0.punit.ptpcfsms.ptpcfsms.plr_header</span></font></p><p style="margin: 0in;"><!--StartFragment--><span style="color: rgba(0, 0, 0, 0.87); font-family: Calibri; font-size: 14.6667px;">0xffffffffffffffff</span><!--EndFragment--><font color="rgba(0, 0, 0, 0.87)" face="Calibri"><span style="font-size: 14.6667px;"></span></font></p><p style="box-sizing: border-box; margin: 0in; padding: 0px; color: rgb(0, 0, 0); font-family: Roboto, Arial, sans-serif; font-size: 14px; font-style: normal; font-variant-ligat

### Conclusion
no_root_cause.rejected

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
- **Sub-Feature**: Mailbox
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI MMIO`
- `TPMI registers`
- `sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_0`
- `sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_1`
- `sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_2`
- `sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_3`
- `sv.socket0.cbb0.pcudata.tpmi_enable_fastpath_mask_4`

## Timeline

- **Submitted**: 2025-09-09 11:01:08
- **Closed**: 2025-09-10 09:36:58

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

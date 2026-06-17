# HSD 22021614663: [X1 PO] Reading CBB TPMI via PYSV breaks GPSB access.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [22021614663](https://hsdes.intel.com/appstore/article-one/#/22021614663) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | chinnai |
| **Component** | sw.env |
| **Defect Die** | base |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **HW** | 40% |
| **Feature** | Platform PM Interface | 80% |
| **Sub-Feature** | TPMI | — |

**Reasoning**: keyword 'eco' in title/desc → HW

## Root Cause Summary

Hi 

We have 6c DMR AP system that shows below error if we ever read the TPMI register in CBB. The same issue not observed in another system with 32c DMR part. 

# if unlock, then refresh then chcek mailbox interface its fine. 

ipc.forcereconfig();ipc.unlock();sv.refresh()

sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface

# if I check current version and loading status.. 

pd.general.cbb_pcode_collateral_check_silicon(True)

 

# Then it fails. 

sv.sock

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Hi 

We have 6c DMR AP system that shows below error if we ever read the TPMI register in CBB. The same issue not observed in another system with 32c DMR part. 

# if unlock, then refresh then chcek mailbox interface its fine. 

ipc.forcereconfig();ipc.unlock();sv.refresh()

sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface

# if I check current version and loading status.. 

pd.general.cbb_pcode_collateral_check_silicon(True)

 

# Then it fails. 

sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface

 

 

In [49]: sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface

Out[49]: ---------------------------------------------------------------------------

iosfsbRspError                            Traceback (most recent call last)

File C:\Python311\Lib\site-packages\IPython\core\formatters.py:770, in PlainTextFormatter.__call__(self, obj)

    763 stream = StringIO()

    764 printer = pretty.RepresentationPrinter(stream, self.verbose,

    765     self.max_width, self.newline,

    766     max_seq_length=self.max_seq_length,

    767     singleton_pprinters=self.singleton_printers,

    768     type_pprinters=self.type_printers,

    769     deferred_pprinters=self.deferred_printers)

--> 770 printer.pretty(obj)

    771 printer.flush()

    772 return stream.getvalue()

File C:\Python311\Lib\site-packages\IPython\lib\pretty.py:411, in RepresentationPrinter.pretty(self, obj)

    400                         return meth(obj, self, cycle)

    401                 if (

    402                     cls is not object

    403                     # check if cls defines __repr__

   (...)    409                     and callable(_safe_getattr(cls, &quot;__repr__&quot;, None))

    410                 ):

--> 411                     return _repr_pprint(obj, self, cycle)

    413     return _default_pprint(obj, self, cycle)

    414 finally:

File C:\Python311\Lib\si

### Comments (latest)
++++22611481733 chinnai
Promoting to sighting as per SLD chat guidelines. 

++++22611481896 chinnai
@Adams, Kenneth W   Adding the openIPC logs from both passing/failing system 
++++14614660728 kwadams
In the log on the working system the tools are applying an override for the SAI prior to the tpmi access which is at this register: sv.socket0.cbb0.taps.tap2iosfsb_gp_base00.sbsaiover=0x101 (enable=0x1, value=0x1) However in a different system I took a log as well and see the SAI override getting applied but the system still failed.  So while I am not sure why there is a delta in the logs, it doesn't seem related.

++++14614660882 kwadams
Okay, so the issue IS related to the SAI override.  What we find is that on the TPMI register access info, there is an override for the sai: 'iosfsb_sai': 0x1, This leads to namednodes access setting the following override (override=0x1, enable=0x1) sv.socket0.cbb0.taps.tap2iosfsb_gp_base00.sbsaiover=0x101 The problem is that on subsequent accesses to the tap2iosfsb, this override remains in place, as long as the register does not use an SAI override. If we manually clear the sbsaiover, then those accesses work fine. Need to update the PythonSv access, to take care of cleaning up the SAI override.

++++14614660885 kwadams
HSD need to be returned to tools for resolution. https://hsdes.intel.com/appstore/article-one/#/article/22021600353
++++22611482165 chinnai
Adding to Kenn update, I could verify that the setting the SBSAIOVER=0 helps recover the SB access to CBB in PYSV. 
++++14614661587 daalonso
Confirmed tool , issue rejecting

### Tags
POsilicon,ptp-pm,ptp,PAIV_PLAT_PNP,PAIV_PNP_SYSDEBUG

### Conclusion
not_a_bug

### Component
sw.env

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
- **Sub-Feature**: TPMI
- **Component Path**: sw.env

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI via`
- `TPMI register`
- `sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.ucode_pcode_mailbox_interface`
- `sv.socket0.cbb0.taps.tap2iosfsb_gp_base00.sbsaiover`

## Timeline

- **Submitted**: 2025-09-26 07:09:54
- **Closed**: 2025-09-26 23:05:33

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*

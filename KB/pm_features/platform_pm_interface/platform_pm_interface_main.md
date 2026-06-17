# Platform PM Interface — Main Flow

> **Status**: Enriched — architecture summary and collateral links populated
> **Generated**: 2026-05-23 from nwp_pm_test_cases.json (11 TCs)

## NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: OS2P Mailbox, PECI PM, TPMI |
| MAS ref | NWP PM MAS: Platform PM interfaces supported |
| NWP delta | Carried from DMR |
| NWP supported | True |

## Architecture Summary
<!-- TODO: Add human-curated architecture summary -->
<!-- HW path, FW agents, interfaces, key registers -->

## FW Agents
- **Agents**: BIOS, PCode
- **Interfaces**: b2p_mailbox
- **HW Blocks**: b2p_mailbox_hw
- **Sub-features**: B2P / O2P Mailbox

## Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [TPMI HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | has_references.yaml → dmr.tpmi |
| HAS | [B2P Mailbox Specification](https://docs.intel.com/documents/primecode/has/DMR/BIOS%20Mailbox/B2P_mailbox_specification.html) | dmr_fw_architecture.yaml → spec_references.b2p_mailbox_spec |
| HAS | [TPMI Specification](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) | dmr_fw_architecture.yaml → spec_references.tpmi_spec |
| HAS | [DMR Punit IP Gen4 Features HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/Punit/Punit_IP_Gen4_Features.html) | Gen4 Punit feature list: SVID standalone, PECI standalone, relaxed SB ordering,  |
| HAS | [Hierarchical OOBMSM and Punit Interactions HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/OOBMSM/H_SOC_OOBMSM_Punit_Interations.html) | Master/Slave Punit↔OOBMSM architecture: 1:1 mapping, BMCInit, PkgC notification, |
| HAS | [NWP BIOS HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/BIOS/NWP.html) | BIOS PM knobs and execution flows |
| HAS | [NWP BIOS - Execution Flows](https://docs.intel.com/documents/custom-xeon/newport-docs/has/BIOS/NWP.html#bios-execution-flows) | BIOS boot flow for PM init |
| FAS | [OOBMSM Gen4 NWP FAS](https://docs.intel.com/documents/arch_datacenter/oobmsm/gen4/oobmsm_fw_gen4_nwp_fas.html) | NWP OOBMSM firmware — PECI/telemetry |
| HAS | [DMR Telemetry HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Telemetry.html) | Telemetry via TPMI/PMT interface |
| HAS | [NWP Telemetry & Manageability HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Manageability%20and%20Telemetry/Telemetry_and_Manageability_HAS.html) | NWP telemetry & manageability |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS |
| Primecode src | TODO | |
| PCode src | TODO | |
| Test scripts | TODO | |
| SharePoint | TODO | |

## Related Sightings
<!-- TODO: Add DMR retrospective sightings relevant to this feature -->

## Subflows (3)
- [OS2P Mailbox](os2p_mailbox.md) (3 TCs)
- [PECI PM](peci_pm.md) (3 TCs)
- [TPMI](tpmi.md) (5 TCs)

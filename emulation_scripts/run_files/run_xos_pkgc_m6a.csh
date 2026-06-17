#!/usr/intel/bin/tcsh

set MY_NQSLOT = /prj/sv/dmr/sysval/priority

setenv NB_WASH_ENABLED
setenv NB_WASH_GROUPS intelall,soc,soc73,hdk10nm,hdk10nmproc,hdk7nm,hdk7nmproc,hfpga_farm,i1278proc,i1278,dmrips,dmrprj,cbbb_c2dg_ex,dmrmcp

setenv WORKAREA /nfs/site/disks/ive_dmr_cit_015/users/agudinog/dmrmcp2-a0-25ww47a_M6a.0_ici
setenv EMU_MODEL $WORKAREA/output/dmrpkgucc2/emu/zebu_zebu/build_rev1/ZSE5_DMR_MCP_1S_ICI_FULLSTACK_HSLE

/p/hdk/cad/emurun/1.14.2/bin/emurun \
-ver $EMU_MODEL \
-fullstack_en \
-b2b_fullstack_xtors \
-enable_fuse_loading \
-enable_pcode_loading \
-enable_s3m_loading \
-enable_preloader \
-enable_imh2 \
-disable_pm_periodic_hlm \
-fuse.fuse_string_file_imh8 /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/25ww42.3_imh2_mcp_ici/fuse/mcp_ici_imh8_overrides.txt \
-fuse.fuse_string_file_imh9 /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/25ww42.3_imh2_mcp_ici/fuse/mcp_ici_imh9_overrides.txt \
-fuse.fuse_string_file_imh8 /nfs/site/disks/xpg_dmrmcp_0180/shahmana/pkgc_v5c/dmr_imh2_0p8b_pm_fuses_v1.txt \
-fuse.fuse_string_file_imh9 /nfs/site/disks/xpg_dmrmcp_0180/shahmana/pkgc_v5c/dmr_imh2_0p8b_pm_fuses_v1.txt \
-fuse.fuse_string_file_cbb /nfs/site/disks/xpg_dmrmcp_0180/shahmana/m6a_ic/fuse_pma_2.txt \
-minibios /nfs/site/disks/ive_dmr_cit_008/agudinog/collaterals/hybrid_ubios/DMR_AP2/hybrid_ubios.obj \
-hybrid_bios /nfs/site/disks/pse_oks_002/narayanm/DMR/imh2_m6a_xos/bios \
-hybrid_mapping /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/26ww03.4_imh2_mcp_ici/hybrid_mapping/dmr-mcp-ici_mapping.simics \
-jem_tlm_port_enable_init_state 1 \
-jem_port_registration_by_sw_side \
-jem_no_dpi_enabling \
-jem_no_disable_at_init \
#-os_image /nfs/site/disks/ive_dmr_prednv_009/jscanlo1/xos_pkgc_m6a/m6a_pm_svos_no_poll.craff \
-os_image /nfs/site/disks/ive_oks_dppci_002/dmr/os/svos/25WW49.5/sut-diamondrapids-efi.amd64.craff \
#override default input dir with additional prints for xos boot flow (added more prints) \
#-override_input_dir /nfs/site/disks/ive_dmr_prednv_009/jscanlo1/xos_pkgc_m6a/input_dir this is commented beacuse it was deleted \
-override_input_dir /nfs/site/disks/ive_dmr_cit_010/rviswana/XOS_AP2/26ww03.4_imh2_mcp_ici/input_dir \
-simics_post_setup_script /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/26ww03.4_imh2_mcp_ici/simics_post_script/svos_post.simics \
-simics_post_setup_script /nfs/site/disks/ive_dmr_cit_010/rviswana/XOS_AP2/simics_scripts/xos_svos_hello_world.simics \
#soc_val team script enabling pkgc flows \
-simics_post_setup_script /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pkgc/m6a/dmr_mcp_ic_pkgc_p1p0b_setup.simics \
-simics_post_setup_script /nfs/site/disks/xpg_dmrmcp_0180/shahmana/pkgc_v5c/polling_script.simics \
#xos team \
-test /nfs/site/disks/xpg_dmrmcp_0089/fnaveen/mcp/tap_unlock/max/jan13th2025/max_base_template.32.obj \
-cbb1_ucie_disable \
-cbb2_ucie_disable \
-cbb3_ucie_disable \
-disable_3cbbs \
-mcp_hsle \
-configdb_override /nfs/site/disks/xpg_dmrhub_0754/DMR_Preloader/25ww25_DMR_PRELOADER_2IMH/Preloader.dut_cfg \
-configdb_override /nfs/site/disks/ive_dmr_prednv_009/aprakas2/XOS/pkgc/pkgc_io_idle_29/wo_pcie/io_bifurcation_mio1.dut_cfg \
-configdb_override /nfs/site/disks/xpg_dmrhub_0792/users/DMR_PM_COE/IMH2/M5a/partial/bios_wa_psf0.dut_cfg \
-configdb_override /nfs/site/disks/xpg_dmrhub_0792/users/DMR_PM_COE/IMH2/M5a/partial/bios_wa_acc5_hap.dut_cfg \
-plugin /nfs/site/disks/xpg_dmrhub_0754/DMR_Preloader/finalplugin/mem_preloader.pm \
-stop_default 7200 \
-umm_enable \
#xos model release page \
-mail 'S E' \
-nbqslot $MY_NQSLOT \
-c 10000000000 \
-netbatch_opts '--exec-limits 10h:12h' \
-netbatch_opts '--log-file-dir /tmp/netbatch' \
-execlimit 43200 \
-enable_xos \
-espi_passthrough \
-imhpunit_fmod \
-cbbpunit_fmod \
-primecode_tracker_en \
-p_tracker_en \
-cbb_pm_tracker_en \
-iosf_sb_tracker_en \
-pm_collector_tracker_en \
#-guop_tracker_en \
#-guop_tracker_start_cycle 3520000000 \
#-idi_tracker_en \
-test_name PEGA_P6_IMH2_M6A_PCUDATA \
-pythonsv_enable \
-pythonsv.logging \
-pythonsv.base simics \
-pythonsv.start_condition '@wait_for_log(\"xos_base_launch.simics\",\"restore done\",\"emu.engine\")' \
#-pythonsv.script /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pkgc/pega_c6.py \
-pythonsv.script /nfs/site/disks/ive_dmr_prednv_009/isaxena/xos/pega_c6.py \
-pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live \
-pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR/AP2/M6A/MCP/SLE/pysv_config_ici.ini \
-tap_unlock
#-i -null -autorun

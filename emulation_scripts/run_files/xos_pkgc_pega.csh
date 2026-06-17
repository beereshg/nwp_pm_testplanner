#!/usr/intel/bin/tcsh

set MY_NQSLOT = /prj/sv/dmr/sysval/priority

setenv NB_WASH_ENABLED
setenv NB_WASH_GROUPS intelall,soc,soc73,hdk10nm,hdk10nmproc,hdk7nm,hdk7nmproc,hfpga_farm,i1278proc,i1278,dmrips,dmrprj,cbbb_c2dg_ex

setenv WORKAREA /nfs/site/disks/pse_dmrprj_01/agudinog/dmrmcp-a0-25ww14b_v14.0/

/p/hdk/cad/emurun/1.14.1/bin/emurun \
-ver /nfs/site/disks/pse_dmrprj_01/agudinog/dmrmcp-a0-25ww14b_v14.0/output/dmrpkgucc1/emu/zebu_zebu/build_perf/ZSE5_DMR_MCP_1S_ICI_FULLSTACK_HSLE \
-b2b_fullstack_xtors \
#-configdb_override /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/25ww39.2_mcp_ici/configdb/io_bifurcation_mio1.dut_cfg \
-configdb_override /nfs/site/disks/ive_dmr_prednv_009/aprakas2/XOS/pkgc/pkgc_io_idle_29/wo_pcie/io_bifurcation_mio1.dut_cfg \
-enable_pcode_loading \
-enable_s3m_loading \
-enable_fuse_loading \
-enable_ocode \
-ocode_backdoor \
-enable_pcie_xtor \
-fuse.fuse_string_file_imh8 /nfs/site/disks/ive_dmr_prednv_009/jscanlo1/xos_cc6/dmr_imh_p1p0b_pm_fuses_v1.txt \
-fuse.fuse_string_file_imh9 /nfs/site/disks/ive_dmr_prednv_009/jscanlo1/xos_cc6/dmr_imh_p1p0b_pm_fuses_v1.txt \
#-hybrid_bios /nfs/site/disks/ive_oks_dppci_002/dmr/ifwi/OAKSTRM.0.RPB.0025.D.01/hsle/25ww27_2_1/mcp \
-hybrid_bios /nfs/site/disks/ive_dmr_prednv_009/jscanlo1/xos_cc6/bios \
-minibios /nfs/site/disks/ive_sem_dmr_dev_004/sasubram/MCP/V10/017_D38_1p0g_ubios/ubios_annotated.obj \
-hybrid_mapping /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/25ww39.2_mcp_ici/hybrid_mapping/dmr-mcp-ici_mapping.simics \
-jem_tlm_port_enable_init_state 1 \
-jem_port_registration_by_sw_side \
-jem_no_dpi_enabling \
-jem_no_disable_at_init \
-os_image /nfs/site/disks/ive_oks_dppci_002/dmr/xos/svos/25ww26_5/sut-diamondrapids-efi_pysv_june6_6_14.amd64.craff \
-override_input_dir /nfs/site/disks/ive_dmr_prednv_009/jscanlo1/xos_hwp/input_dir \
-test /nfs/site/disks/xpg_dmrmcp_0089/fnaveen/mcp/tap_unlock/max/jan13th2025/max_base_template.32.obj \
-bios_fetchor_logging_dis \
-cbbpunit_fmod \
-disable_3cbbs \
-enable_preloader \
-enable_xos \
-espi_passthrough \
-fastclk_8g \
-fullstack_en \
-imhpunit_fmod \
-mcp_hsle \
-tardis_debug_disable \
-test_name PEGA_C6_IMH1_V14_XOS \
-umm_enable \
-c 10000000000 \
-primecode_tracker_en \
-p_tracker_en \
#-guop_tracker_en \
#-iosf_sb_tracker_en \
-mail 'S E' \
-nbqslot $MY_NQSLOT \
-netbatch_opts '--exec-limits 10h:12h' \
-netbatch_opts '--log-file-dir /tmp/netbatch' \
-execlimit 43200 \
-simics_post_setup_script /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/25ww39.2_mcp_ici/simics_post_script/svos_post.simics \
-simics_post_setup_script /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/users/jscanlo1/xos_hwpm/xos_svos_hello_world.simics \
-tap_unlock \
-pythonsv_enable \
-pythonsv.logging \
-pythonsv.base simics \
-pythonsv.start_condition '@wait_for_log(\"xos_base_launch.simics\",\"restore done\",\"emu.engine\")' \
#-pythonsv.script /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pkgc/pega_c6.py \
-pythonsv.script /nfs/site/disks/ive_dmr_prednv_009/aprakas2/XOS/pkgc/pkgc_io_idle_29/pega_c6.py \
-pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live \
-pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR_AP/MCP/SLE/pysv_config_3.ini


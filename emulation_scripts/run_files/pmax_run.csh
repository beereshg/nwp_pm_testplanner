#!/usr/intel/bin/tcsh
setenv PATH /p/hdk/cad/zapo_crt/latest/bin:${PATH}
setenv NB_WASH_ENABLED
setenv NB_WASH_GROUPS intelall,soc,soc73,shdk73,hdk7nm,adl_rtl,adl,gnr74,gnr76,cicg,c2dgusers,dmrips,dmrprj,cbbb_c2dg_ex,dmrmcp

#crt -rid 40584 -bf mcp_ici_hsle_svos --er -nbqslot /prj/sv/dmr/sysval/standard -c 4000000000 -netbatch_opts \'--log-file-dir /tmp/netbatch\' -mail \'S E\' -simics_post_setup_script /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/26ww11.4_imh2_mcp_ici/simics_post_script/PPR_auto_exit_svos_sc.simics -pythonsv_enable -pythonsv.base simics -pythonsv.logging -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live -pythonsv.script  /nfs/site/disks/ive_oks_dppci_002/dmr/collaterals/pythonsv_doa_test/pysvdoa_ww45/pythonSV_DOA.py -pythonsv.stub /nfs/site/disks/ive_pysv_dmr_001/pysv_configs/DMR/AP2/M7/MCP/SLE/pysv_config_ici.ini -pythonsv.start_condition "'"'@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")'"'" --

#added bios knob for HWP
#added acode,pcode,primecode and iosf-sb tracker 
#running job with priority
#added fuse overrides for pmax run
#added bios knobs for pmax run
crt -rid 40206 -bf mcp_ici_hsle_xos_svos \
 --er \
 -nbqslot /prj/sv/dmr/sysval/priority \
 -c 8000000000 \
 -netbatch_opts \'--exec-limits 7h:8h\' \
 -mail \'S E\' \
 -idi_tracker_en -iosf_sb_newt_tracker_en -iosf_sb_tracker_en -ufi_d2d_tracker_en \
 -p_tracker_en -primecode_tracker_en -acode_tracker_en -iosf_sb_tracker_en \
 -pythonsv.start_condition '@wait_for_log(\"uefi_post.simics\",\"PPR_TEST_DONE\",\"emu.devices\")' \
 -pythonsv.script_args=--die imh0 imh1 cbb0 \
 -pythonsv_enable \
 -pythonsv.logging \
 -pythonsv.base simics \
 -fuse.fuse_string_file_imh8 /nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/fuse_overrides/pmax_imh8_fuse.txt \
 -fuse.fuse_string_file_imh9 /nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/fuse_overrides/pmax_imh9_fuse.txt \
 -fuse.fuse_string_file_cbb /nfs/site/disks/ive_dmr_prednv_009/nkudliba/training/fuse_overrides/pmax_cbb_fuse.txt \
 -pythonsv.script /nfs/site/disks/ive_oks_dppci_002/dmr/collaterals/pythonsv_doa_test/pysv_oobmsm_ww32/pythonSV_DOA.py \
 -pythonsv.script /nfs/site/disks/ive_pysv_dmr_001/pythonsv_ap2_live/diamondrapids/pm/pss/pmax/pmax_dfx_inject.py \
 -pythonsv.path /nfs/site/disks/ive_pysv_dmr_001/pythonsv_a0_mcp_py310 \
 -pythonsv.stub socket_2imhs_post1p0z_a0_4cbbs_25ww13f_a0_s4_c64_1p0.tlmdb.tar.xz --













 
 
  --


crt -rid 40206 -bf mcp_ici_hsle_xos_svos --er -nbqslot <YOUR APPROVED QSLOT> -c 6000000000 -netbatch_opts \'--exec-limits 7h:8h\' -mail \'S E\' -idi_tracker_en -iosf_sb_newt_tracker_en -iosf_sb_tracker_en -ufi_d2d_tracker_en -simics_post_setup_script  /nfs/site/disks/ive_oks_dppci_002/dmr/A0/hsle/mcp_ici/releases/25ww23.2_mcp_ici/simics_post_script/xos_svos_hello_world.simics